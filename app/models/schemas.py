"""
Pydantic models for API request / response schemas.

Two separate request models for deals and discounts — each with only
the fields relevant to that category. No ambiguity in Swagger docs.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


# ── Valid Fal.ai Aspect Ratios ────────────────────────────────────────
# Some of these are native fal.ai presets, others are custom presets
# that we translate to {"width": W, "height": H} in the provider layer.
ImageSize = Literal[
    "square_hd",
    "square",
    "portrait_4_3",
    "portrait_4_5",
    "portrait_16_9",
    "portrait_3_5",
    "portrait_9_18",
    "landscape_4_3",
    "landscape_16_9",
    "landscape_18_9",
    "landscape_20_9",
]

# Aspect ratios generated during batch (on offer approval).
# Excludes landscape_16_9 since it already exists from the initial generation.
BATCH_SIZES: list[str] = [
    "portrait_3_5",     # 3:5
    "portrait_16_9",    # 9:16
    "portrait_9_18",    # 9:18
    "portrait_4_3",     # 3:4
    "landscape_18_9",   # 18:9
    "landscape_20_9",   # 20:9
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
    image_size: Annotated[ImageSize, Field(description="Aspect ratio")] = "landscape_16_9"


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
    image_size: Annotated[ImageSize, Field(description="Aspect ratio")] = "landscape_16_9"


# ── Food Request ─────────────────────────────────────────────────────

class FoodRequest(BaseModel):
    """
    Request body for POST /generate/food.

    Used for generating clean, text-free commercial food photography
    of individual menu items (like Zomato/Swiggy).
    """
    dish_name: str = Field(
        ...,
        description="The name of the food item (e.g. 'Butter Chicken', 'Margherita Pizza')"
    )
    merchant_prompt: str | None = Field(
        default=None,
        description="Optional: Custom creative direction (e.g., 'serve in a black ceramic bowl')"
    )
    image_size: Annotated[ImageSize, Field(description="Aspect ratio")] = "landscape_16_9"


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
    image_size: Annotated[ImageSize, Field(description="Aspect ratio")] = "landscape_16_9"


# ── Batch Request ────────────────────────────────────────────────────

class BatchRequest(BaseModel):
    """
    Request body for POST /generate/batch.

    Used when a merchant approves an offer — generates images for all
    required aspect ratios in parallel so they are pre-cached for later
    promotion (stories, banners, etc.). Bypasses the LLM refiner.
    """

    approved_refined_prompt: str = Field(
        ...,
        description="The refined_prompt from the approved offer",
    )
    sizes: list[str] | None = Field(
        default=None,
        description="Optional override: list of image size keys to generate. "
                    "Defaults to BATCH_SIZES if not provided.",
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


class BatchImageItem(BaseModel):
    """A single image within a batch generation response."""

    image_url: str = Field(description="URL of the generated image")
    image_size: str = Field(description="Aspect ratio used. e.g. portrait_3_5, landscape_18_9")


class BatchGenerateResponse(BaseModel):
    """Response when generate_all=true. Contains images for all required aspect ratios."""

    images: list[BatchImageItem] = Field(description="List of generated images with their ratios")
    refined_prompt: str = Field(description="The approved refined prompt that was used")
    refiner_used: str = Field(
        default="skipped",
        description="Refiner is skipped in batch mode — the approved prompt is reused as-is",
    )
    cost: CostBreakdown | None = Field(
        default=None,
        description="Always None in batch mode (no refiner cost)",
    )
