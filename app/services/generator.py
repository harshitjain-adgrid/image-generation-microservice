"""
Image generation service.

Delegates to the fal_image provider. No fallback — if GPT Image 2 fails,
the error propagates to the caller.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import get_settings
from app.providers import fal_image

logger = logging.getLogger("imagegen.services.generator")


def generate(prompt: str, quality: str | None = None, image_size: str | None = None) -> str:
    """
    Generate a single image from a refined prompt.

    Args:
        prompt: The refined image generation prompt.
        quality: Image quality (low | medium | high). Uses config default if None.
        image_size: The aspect ratio.

    Returns:
        URL of the generated image.
    """
    settings = get_settings()
    resolved_quality = quality or settings.default_quality

    logger.info(
        "Generating image",
        extra={"generator": "fal-ai/gpt-image-2", "quality": resolved_quality},
    )

    kwargs = {"prompt": prompt, "quality": resolved_quality}
    if image_size:
        kwargs["image_size"] = image_size

    return fal_image.generate(**kwargs)


def generate_batch(prompt: str, sizes: list[str], quality: str | None = None) -> list[dict]:
    """
    Generate images for multiple aspect ratios using the same prompt.

    Uses ThreadPoolExecutor for concurrent generation — all sizes are
    fired simultaneously since fal.ai calls are I/O-bound (network).
    Typical speedup: ~5× (from ~25-40s sequential to ~5-8s parallel).

    Used when a merchant approves an offer — generates all required
    sizes in one go so the backend can store them.

    Args:
        prompt: The approved refined prompt.
        sizes: List of image size keys (e.g. ["portrait_3_5", "portrait_16_9"]).
        quality: Image quality tier. Uses config default if None.

    Returns:
        List of dicts with {"image_url": str, "image_size": str}.

    Raises:
        Exception: If any single image generation fails, the entire batch fails.
    """
    settings = get_settings()
    resolved_quality = quality or settings.default_quality

    logger.info(
        "Starting parallel batch generation",
        extra={"sizes": sizes, "count": len(sizes), "quality": resolved_quality},
    )

    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=len(sizes)) as pool:
        future_to_size = {
            pool.submit(
                fal_image.generate,
                prompt=prompt,
                quality=resolved_quality,
                image_size=size,
            ): size
            for size in sizes
        }

        for future in as_completed(future_to_size):
            size = future_to_size[future]
            url = future.result()  # raises if that call failed
            logger.info("Batch: generated %s", size)
            results.append({"image_url": url, "image_size": size})

    logger.info("Batch generation complete: %d images", len(results))
    return results
