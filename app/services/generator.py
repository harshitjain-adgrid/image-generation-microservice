"""
Image generation service.

Delegates to the fal_image provider. No fallback — if GPT Image 2 fails,
the error propagates to the caller.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.providers import fal_image

logger = logging.getLogger("imagegen.services.generator")


def generate(prompt: str, quality: str | None = None) -> str:
    """
    Generate an image from a refined prompt.

    Args:
        prompt: The refined image generation prompt.
        quality: Image quality (low | medium | high). Uses config default if None.

    Returns:
        URL of the generated image.
    """
    settings = get_settings()
    resolved_quality = quality or settings.default_quality

    logger.info(
        "Generating image",
        extra={"generator": "fal-ai/gpt-image-2", "quality": resolved_quality},
    )

    return fal_image.generate(prompt=prompt, quality=resolved_quality)
