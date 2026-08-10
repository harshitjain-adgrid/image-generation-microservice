"""
Image generation endpoints.

Two separate endpoints for deals and discounts — each with a clean,
dedicated request schema. Pipeline: refine → generate → return URL.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    CostBreakdown,
    DealRequest,
    DiscountRequest,
    GenerateResponse,
    RegenerateRequest,
)
from app.services import generator, refiner

logger = logging.getLogger("imagegen.routes.generate")

router = APIRouter(prefix="/generate", tags=["generate"])


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


@router.post("/deal", response_model=GenerateResponse)
def generate_deal(request: DealRequest):
    """
    Generate a promotional image for a deal (BOGO, combo, bundle, etc.).

    Pipeline:
      1. Refine the deal payload into a detailed image prompt
      2. Generate the image via GPT Image 2
      3. Return the image URL with cost breakdown
    """
    logger.info(
        "New deal request",
        extra={"merchant": request.merchant_name, "title": request.title},
    )

    # Step 1: Refine
    try:
        refined = refiner.refine(request)
    except Exception as e:
        logger.error("Prompt refinement failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prompt refinement failed: {e}")

    # Step 2: Generate
    try:
        image_url = generator.generate(prompt=refined.prompt)
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    return _build_response(refined, image_url)


@router.post("/discount", response_model=GenerateResponse)
def generate_discount(request: DiscountRequest):
    """
    Generate a promotional image for a discount (percentage off, flat amount, etc.).

    Pipeline:
      1. Refine the discount payload into a detailed image prompt
      2. Generate the image via GPT Image 2
      3. Return the image URL with cost breakdown
    """
    logger.info(
        "New discount request",
        extra={
            "merchant": request.merchant_name,
            "discount_type": request.discount_type,
            "discount_value": request.discount_value,
        },
    )

    # Step 1: Refine
    try:
        refined = refiner.refine(request)
    except Exception as e:
        logger.error("Prompt refinement failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Prompt refinement failed: {e}")

    # Step 2: Generate
    try:
        image_url = generator.generate(prompt=refined.prompt)
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    return _build_response(refined, image_url)


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
        image_url = generator.generate(prompt=request.previous_refined_prompt)
    except Exception as e:
        logger.error("Image regeneration failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

    return GenerateResponse(
        image_url=image_url,
        refined_prompt=request.previous_refined_prompt,
        refiner_used="skipped",
        cost=None,
    )
