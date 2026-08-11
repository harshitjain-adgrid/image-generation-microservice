"""
Fal.ai image generation provider — thin wrapper for GPT Image 2.

Handles the safety suffix injection and model-specific API arguments.
"""

from __future__ import annotations

import logging

import fal_client

from app.safety.rules import GPT_SAFETY_SUFFIX

logger = logging.getLogger("imagegen.providers.fal_image")


def generate(
    prompt: str,
    quality: str = "low",
    image_size: str = "landscape_16_9",
) -> str:
    """
    Generate an image using GPT Image 2 on fal.ai.

    The safety suffix is automatically appended to prevent brand hallucination.

    Args:
        prompt: The refined image generation prompt.
        quality: Image quality tier (low | medium | high).
        image_size: Image dimensions preset (landscape_4_3, landscape_16_9, etc.).

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

    logger.info(
        "Calling GPT Image 2",
        extra={"quality": quality, "image_size": image_size},
    )
    logger.debug("Full prompt:\n%s", safe_prompt)

    result = fal_client.subscribe(
        "fal-ai/gpt-image-2",
        arguments={
            "prompt": safe_prompt,
            "image_size": image_size,
            "quality": quality,
        },
    )

    images = result.get("images", [])
    if not images:
        raise RuntimeError("GPT Image 2 returned no images.")

    url = images[0]["url"]
    logger.info("Image generated successfully", extra={"url": url})
    return url
