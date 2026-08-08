"""
FastAPI application factory.

Entry point for the image generation microservice.
Run with: uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI

from app.config import get_settings
from app.routes import generate, health


def _configure_logging() -> None:
    """Set up structured logging to stdout."""
    settings = get_settings()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("imagegen")
    root_logger.setLevel(settings.log_level.upper())
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fal_client").setLevel(logging.WARNING)


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    _configure_logging()

    application = FastAPI(
        title="Image Generation Microservice",
        description=(
            "A configurable, production-grade microservice for generating "
            "promotional images (coupons, deals, banners) using AI-powered "
            "prompt refinement and text-to-image generation."
        ),
        version="2.0.0",
    )

    # Mount routers
    application.include_router(health.router)
    application.include_router(generate.router)

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
