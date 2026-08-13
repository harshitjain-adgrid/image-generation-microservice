"""
Fal.ai image generation provider — thin wrapper for GPT Image 2.

Handles the safety suffix injection, custom aspect ratio translation,
and model-specific API arguments.
"""

from __future__ import annotations

import logging

import fal_client

from app.safety.rules import GPT_SAFETY_SUFFIX

logger = logging.getLogger("imagegen.providers.fal_image")

# ── Custom size mapping ──────────────────────────────────────────────
# Fal.ai natively supports: square_hd, square, portrait_4_3, portrait_16_9,
# landscape_4_3, landscape_16_9, auto.
# Everything else needs explicit {width, height} (both multiples of 16).
CUSTOM_SIZE_MAP: dict[str, dict[str, int]] = {
    "portrait_4_5":   {"width": 1024, "height": 1280},   # 4:5
    "portrait_3_5":   {"width": 768,  "height": 1280},   # 3:5
    "portrait_9_18":  {"width": 640,  "height": 1280},   # 9:18 (1:2)
    "landscape_18_9": {"width": 2048, "height": 1024},   # 18:9 (2:1)
    "landscape_20_9": {"width": 2240, "height": 1008},   # 20:9
}

# ── Safe-zone suffixes ───────────────────────────────────────────────
# Appended to the prompt for tall portrait images so the top and bottom
# ~1/7th of the image remain clear of important content (UI overlays).
_SAFE_ZONE_TEMPLATE = (
    " IMPORTANT LAYOUT CONSTRAINT: This image will be displayed in a tall "
    "portrait ({ratio}) format on a mobile app. Leave the top ~14% and bottom "
    "~14% of the image as clean, uncluttered negative space (soft gradient, "
    "solid color continuation, or very subtle background) with NO text, "
    "products, faces, or important visual elements in those zones, as UI "
    "elements will overlay these areas."
)

# Sizes that need safe-zone constraints → their display ratio label
SAFE_ZONE_SIZES: dict[str, str] = {
    "portrait_16_9": "9:16",
    "portrait_9_18": "9:18",
}


def generate(
    prompt: str,
    quality: str = "low",
    image_size: str = "landscape_16_9",
) -> str:
    """
    Generate an image using GPT Image 2 on fal.ai.

    The safety suffix is automatically appended to prevent brand hallucination.
    For portrait_16_9 (9:16), a safe-zone instruction is also appended.

    Args:
        prompt: The refined image generation prompt.
        quality: Image quality tier (low | medium | high).
        image_size: Image dimensions preset or custom key.

    Returns:
        Public URL of the generated image.

    Raises:
        ValueError: If prompt is empty.
        Exception: Any fal_client errors (network, auth, quota).
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    # Append safety suffix to prevent brand hallucination
    safe_prompt = prompt + GPT_SAFETY_SUFFIX

    # For tall portrait images, append safe-zone layout constraint
    if image_size in SAFE_ZONE_SIZES:
        safe_prompt += _SAFE_ZONE_TEMPLATE.format(ratio=SAFE_ZONE_SIZES[image_size])

    logger.info(
        "Calling GPT Image 2",
        extra={"quality": quality, "image_size": image_size},
    )
    logger.debug("Full prompt:\n%s", safe_prompt)

    # Resolve custom presets to explicit {width, height}
    resolved_image_size: str | dict = CUSTOM_SIZE_MAP.get(image_size, image_size)

    result = fal_client.subscribe(
        "fal-ai/gpt-image-2",
        arguments={
            "prompt": safe_prompt,
            "image_size": resolved_image_size,
            "quality": quality,
        },
    )

    images = result.get("images", [])
    if not images:
        raise RuntimeError("GPT Image 2 returned no images.")

    url = images[0]["url"]
    logger.info("Image generated successfully", extra={"url": url})
    return url
