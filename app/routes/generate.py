"""
Image generation endpoints.

Clean separation of concerns:
  /deal, /discount, /food  — refine → generate → return 1 image
  /regenerate              — same prompt, new seed → return 1 image
  /batch                   — approved prompt → generate all aspect ratios in parallel
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BATCH_SIZES,
    BatchGenerateResponse,
    BatchImageItem,
    BatchRequest,
    CostBreakdown,
    DealRequest,
    DiscountRequest,
    FoodRequest,
    GenerateResponse,
    RegenerateRequest,
)
from app.services import generator, refiner

logger = logging.getLogger("imagegen.routes.generate")

router = APIRouter(prefix="/v1/generate", tags=["generate"])


def _build_response(refined: refiner.RefinedPrompt, image_url: str) -> GenerateResponse:
    """Build the response from refinement and generation results."""
    return GenerateResponse(
        image_url=image_url,
        refined_prompt=refined.prompt,
        refiner_used=refined.refiner_used,
        cost=CostBreakdown(
            refiner_model=refined.model_id,
            refiner_tokens=refined.total_tokens,
            refiner_cost_usd=refined.cost_usd,
        ),
    )


def _refine_and_generate(request, use_case: str | None = None) -> GenerateResponse:
    """
    Shared pipeline for /deal, /discount, /food:
    refine the payload → generate one image → return response.
    """
    # Step 1: Refine
    try:
        kwargs = {"request": request}
        if use_case:
            kwargs["use_case"] = use_case
        refined = refiner.refine(**kwargs)
    except Exception as e:
        logger.error("Prompt refinement failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prompt refinement failed: {e}")

    # Step 2: Generate
    try:
        gen_kwargs = {"prompt": refined.prompt}
        if request.image_size:
            gen_kwargs["image_size"] = request.image_size
        image_url = generator.generate(**gen_kwargs)
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    return _build_response(refined, image_url)


@router.post("/deal", response_model=GenerateResponse)
def generate_deal(request: DealRequest):
    """
    Generate a promotional image for a deal (BOGO, combo, bundle, etc.).

    Pipeline: refine the deal payload → generate 1 image → return URL.
    """
    logger.info(
        "New deal request",
        extra={"merchant": request.merchant_name, "title": request.title},
    )
    return _refine_and_generate(request)


@router.post("/discount", response_model=GenerateResponse)
def generate_discount(request: DiscountRequest):
    """
    Generate a promotional image for a discount (percentage off, flat amount, etc.).

    Pipeline: refine the discount payload → generate 1 image → return URL.
    """
    logger.info(
        "New discount request",
        extra={
            "merchant": request.merchant_name,
            "discount_type": request.discount_type,
            "discount_value": request.discount_value,
        },
    )
    return _refine_and_generate(request)


@router.post("/food", response_model=GenerateResponse)
def generate_food(request: FoodRequest):
    """
    Generate clean, mouth-watering commercial food photography.

    Pipeline: refine the food payload → generate 1 image → return URL.
    """
    logger.info(
        "New food request",
        extra={"dish_name": request.dish_name},
    )
    return _refine_and_generate(request, use_case="food")


@router.post("/regenerate", response_model=GenerateResponse)
def regenerate_image(request: RegenerateRequest):
    """
    Regenerate a banner using the same refined prompt.

    Bypasses the LLM refiner entirely — sends the previous prompt
    directly to GPT Image 2 with a new random seed. This produces
    a similar but visually distinct variation at zero refiner cost.
    """
    logger.info("Regenerate request")

    try:
        kwargs = {"prompt": request.previous_refined_prompt}
        if request.image_size:
            kwargs["image_size"] = request.image_size

        image_url = generator.generate(**kwargs)
    except Exception as e:
        logger.error("Image regeneration failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    return GenerateResponse(
        image_url=image_url,
        refined_prompt=request.previous_refined_prompt,
        refiner_used="skipped",
        cost=None,
    )


@router.post("/batch", response_model=BatchGenerateResponse)
def generate_batch(request: BatchRequest):
    """
    Generate images for all required aspect ratios from an approved prompt.

    Called in the background after a merchant approves an offer. Generates
    all sizes in parallel so they are pre-cached for later promotion
    (stories, banners, etc.). Bypasses the LLM refiner.
    """
    sizes = request.sizes or BATCH_SIZES

    logger.info(
        "Batch generation request",
        extra={"sizes": sizes, "count": len(sizes)},
    )

    try:
        results = generator.generate_batch(
            prompt=request.approved_refined_prompt,
            sizes=sizes,
        )
    except Exception as e:
        logger.error("Batch generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {e}")

    return BatchGenerateResponse(
        images=[BatchImageItem(**r) for r in results],
        refined_prompt=request.approved_refined_prompt,
        refiner_used="skipped",
        cost=None,
    )

