"""
Pydantic models for API request / response schemas.

Two separate request models for deals and discounts — each with only
the fields relevant to that category. No ambiguity in Swagger docs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Valid Fal.ai Aspect Ratios ────────────────────────────────────────
# "portrait_4_5" is a custom preset we handle — fal.ai doesn't have it
# natively, so we translate it to {"width": 1024, "height": 1280}.
ImageSize = Literal[
    "square_hd",
    "square",
    "portrait_4_3",
    "portrait_4_5",
    "portrait_16_9",
    "landscape_4_3",
    "landscape_16_9",
]


# ── Deal Request ──────────────────────────────────────────────────────

class DealRequest(BaseModel):
    """
    Request body for POST /generate/deal.

    Used for: BOGO, combos, bundles, and similar offers.
    """

    merchant_name: str = Field(
        ...,
        description="Business name — rendered as brand identity in the image",
    )
    title: str = Field(
        ...,
        description='Headline text for the banner. e.g. "Buy 1 Get 1 Free"',
    )
    merchant_prompt: str | None = Field(
        default=None,
        description='Merchant\'s custom creative direction. e.g. "Holi theme", "show NOICE lime soda"',
    )
    category: str | None = Field(
        default=None,
        description="Product category for visual theme. e.g. FOOD_AND_BEVERAGES, ELECTRONICS",
    )
    offer_type: str | None = Field(
        default=None,
        description="Offer type. e.g. BOGO, COMBO, BUNDLE",
    )


# ── Discount Request ─────────────────────────────────────────────────

class DiscountRequest(BaseModel):
    """
    Request body for POST /generate/discount.

    Used for: percentage off, flat amount off, etc.
    Note: min_bill_amount, max_discount, valid_days are intentionally excluded.
    They are operational details — including them risks the refiner
    rendering them as text on the banner. If the merchant explicitly wants
    them shown, they can specify it in merchant_prompt.
    """

    merchant_name: str = Field(
        ...,
        description="Business name — rendered as brand identity in the image",
    )
    discount_type: str = Field(
        ...,
        description='How the discount is applied. "PERCENTAGE" or "FLAT_AMOUNT"',
    )
    discount_value: float = Field(
        ...,
        description="The discount number (10 for 10%%, 200 for ₹200)",
    )
    merchant_prompt: str | None = Field(
        default=None,
        description='Merchant\'s custom creative direction. e.g. "show Samsung phones", "Diwali theme"',
    )
    category: str | None = Field(
        default=None,
        description="Product category for visual theme. e.g. GROCERY, ELECTRONICS, FASHION",
    )


# ── Regenerate Request ────────────────────────────────────────────────

class RegenerateRequest(BaseModel):
    """
    Request body for POST /generate/regenerate.

    Used when a merchant clicks "Regenerate banner". Bypasses the LLM
    refiner entirely — the previous refined prompt is sent directly to
    the image generator with a new random seed, producing a similar but
    visually distinct variation.
    """

    previous_refined_prompt: str = Field(
        ...,
        description="The refined_prompt returned from the original /generate/deal or /generate/discount call",
    )
    image_size: ImageSize | None = Field(
        default=None,
        description="Optional: override the aspect ratio for this regeneration",
    )


# ── Response ──────────────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    """Token usage and cost details."""

    refiner_model: str = Field(description="Model that performed the refinement")
    refiner_tokens: int | None = Field(default=None, description="Total tokens used")
    refiner_cost_usd: float | None = Field(default=None, description="Refinement cost in USD")


class GenerateResponse(BaseModel):
    """Response from POST /generate/deal or /generate/discount."""

    image_url: str = Field(description="URL of the generated image")
    refined_prompt: str = Field(description="The AI-refined image generation prompt")
    refiner_used: str = Field(description="Which refiner model generated the prompt")
    cost: CostBreakdown | None = Field(
        default=None,
        description="Cost and usage breakdown",
    )
