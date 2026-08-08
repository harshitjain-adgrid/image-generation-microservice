"""
Prompt refinement service.

Orchestrates:
  1. Serialising the request into a clean JSON payload for the LLM
  2. Resolving the system prompt from the use-case
  3. Calling the primary refiner (Claude Haiku 4.5)
  4. Falling back to the fallback refiner (Gemini 2.5 Flash) on failure
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Union

from app.config import REFINER_REGISTRY, get_settings, get_system_prompt
from app.models.schemas import DealRequest, DiscountRequest
from app.providers import openrouter

logger = logging.getLogger("imagegen.services.refiner")


@dataclass
class RefinedPrompt:
    """Output of the refinement step."""

    prompt: str
    refiner_used: str       # friendly name, e.g. "claude-haiku-4.5"
    model_id: str           # OpenRouter model ID
    total_tokens: int | None = None
    cost_usd: float | None = None


def _build_deal_payload(request: DealRequest) -> dict:
    """Build a clean dict from a deal request."""
    payload: dict = {
        "type": "deal",
        "merchant_name": request.merchant_name,
        "title": request.title,
    }
    if request.merchant_prompt:
        payload["merchant_prompt"] = request.merchant_prompt
    if request.category:
        payload["category"] = request.category
    if request.offer_type:
        payload["offer_type"] = request.offer_type
    return payload


def _build_discount_payload(request: DiscountRequest) -> dict:
    """Build a clean dict from a discount request."""
    payload: dict = {
        "type": "discount",
        "merchant_name": request.merchant_name,
        "discount_type": request.discount_type,
        "discount_value": request.discount_value,
    }
    if request.merchant_prompt:
        payload["merchant_prompt"] = request.merchant_prompt
    if request.category:
        payload["category"] = request.category
    return payload


def _resolve_refiner(refiner_name: str) -> str:
    """Map a friendly refiner name to its OpenRouter model ID."""
    if refiner_name not in REFINER_REGISTRY:
        available = ", ".join(REFINER_REGISTRY.keys())
        raise ValueError(f"Unknown refiner '{refiner_name}'. Available: {available}")
    return REFINER_REGISTRY[refiner_name]


def refine(
    request: Union[DealRequest, DiscountRequest],
    use_case: str = "coupon",
) -> RefinedPrompt:
    """
    Refine the user's request into a detailed image generation prompt.

    Strategy:
      1. Try the primary refiner (Claude Haiku 4.5).
      2. If it fails, fall back to the fallback refiner (Gemini 2.5 Flash).
      3. If both fail, raise the error.
    """
    settings = get_settings()

    # Build the input payload based on request type
    if isinstance(request, DealRequest):
        payload = _build_deal_payload(request)
    else:
        payload = _build_discount_payload(request)

    refiner_input = json.dumps(payload, ensure_ascii=False, indent=2)

    # Resolve the system prompt for this use-case
    system_prompt = get_system_prompt(use_case)

    # Determine refiners
    primary_name = settings.primary_refiner
    fallback_name = settings.fallback_refiner

    logger.info(
        "Starting refinement",
        extra={"primary": primary_name, "fallback": fallback_name},
    )

    # ── Attempt 1: Primary refiner ────────────────────────────────────
    primary_error = None
    try:
        primary_model_id = _resolve_refiner(primary_name)
        logger.info("Trying primary refiner: %s (%s)", primary_name, primary_model_id)

        result = openrouter.complete(
            query=refiner_input,
            system_prompt=system_prompt,
            model=primary_model_id,
        )

        return RefinedPrompt(
            prompt=result.text,
            refiner_used=primary_name,
            model_id=result.model,
            total_tokens=result.total_tokens,
            cost_usd=result.cost_usd,
        )

    except Exception as err:
        primary_error = err
        logger.warning(
            "Primary refiner failed: %s. Falling back to %s",
            err,
            fallback_name,
        )

    # ── Attempt 2: Fallback refiner ───────────────────────────────────
    try:
        fallback_model_id = _resolve_refiner(fallback_name)
        logger.info("Trying fallback refiner: %s (%s)", fallback_name, fallback_model_id)

        result = openrouter.complete(
            query=refiner_input,
            system_prompt=system_prompt,
            model=fallback_model_id,
        )

        return RefinedPrompt(
            prompt=result.text,
            refiner_used=fallback_name,
            model_id=result.model,
            total_tokens=result.total_tokens,
            cost_usd=result.cost_usd,
        )

    except Exception as fallback_err:
        logger.error("Fallback refiner also failed: %s", fallback_err)
        raise RuntimeError(
            f"All refiners failed. Primary ({primary_name}): {primary_error} | "
            f"Fallback ({fallback_name}): {fallback_err}"
        ) from fallback_err
