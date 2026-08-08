"""
Application configuration — single source of truth for all settings.

All values are loaded from environment variables with sensible defaults.
Override any value by setting the corresponding env var or adding it to .env.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ── API Keys ──────────────────────────────────────────────────────
    fal_key: str = Field(
        ...,
        description="Fal.ai API key — used for both image generation and OpenRouter refiners",
    )

    # ── Refiner Defaults ──────────────────────────────────────────────
    primary_refiner: str = Field(
        default="claude-haiku-4.5",
        description="Primary LLM for prompt refinement",
    )
    fallback_refiner: str = Field(
        default="gemini-2.5-flash",
        description="Fallback LLM if the primary refiner fails",
    )

    # ── Generator Defaults ────────────────────────────────────────────
    default_quality: str = Field(
        default="low",
        description="Default image quality (low | medium | high)",
    )

    # ── Logging ───────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG | INFO | WARNING | ERROR)",
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


# ── Refiner Registry ─────────────────────────────────────────────────
# Maps friendly refiner names → OpenRouter model IDs.
# Primary: Claude Haiku 4.5 | Fallback: Gemini 2.5 Flash

REFINER_REGISTRY: dict[str, str] = {
    "claude-haiku-4.5": "anthropic/claude-haiku-4.5",
    "gemini-2.5-flash":  "google/gemini-2.5-flash",
}


# ── Use-Case Registry ────────────────────────────────────────────────
# Maps use-case names → prompt module + attribute.
# Adding a new use-case = add one .py file in app/prompts/ + one entry here.

USE_CASE_REGISTRY: dict[str, dict[str, str]] = {
    "coupon": {
        "prompt_module": "app.prompts.coupon",
        "prompt_attr": "COUPON_SYSTEM_PROMPT",
    },
}

DEFAULT_USE_CASE = "coupon"


def get_system_prompt(use_case: str) -> str:
    """Dynamically load the system prompt for a given use-case."""
    if use_case not in USE_CASE_REGISTRY:
        available = ", ".join(USE_CASE_REGISTRY.keys())
        raise ValueError(f"Unknown use_case '{use_case}'. Available: {available}")

    entry = USE_CASE_REGISTRY[use_case]
    module = import_module(entry["prompt_module"])
    return getattr(module, entry["prompt_attr"])


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()
