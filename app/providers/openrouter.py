"""
OpenRouter provider — thin wrapper around fal.ai's OpenRouter integration.

All LLM-based refiners (Haiku, Gemini, GPT, DeepSeek, etc.) are called
through this single provider using the FAL_KEY.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import fal_client

logger = logging.getLogger("imagegen.providers.openrouter")


@dataclass
class RefinerResult:
    """Result from a prompt refinement call."""

    text: str
    model: str
    total_tokens: int | None = None
    cost_usd: float | None = None


def complete(
    query: str,
    system_prompt: str,
    model: str,
    temperature: float = 0.7,
) -> RefinerResult:
    """
    Call an LLM via fal.ai's OpenRouter enterprise endpoint.

    Args:
        query: The user's input to refine.
        system_prompt: System instructions for the LLM.
        model: OpenRouter model ID (e.g. "anthropic/claude-haiku-4.5").
        temperature: Sampling temperature.

    Returns:
        RefinerResult with the generated text and usage metadata.

    Raises:
        ValueError: If the model returns an empty response.
        Exception: Any fal_client errors (network, auth, model not found).
    """
    logger.info("Calling OpenRouter", extra={"model": model})

    result = fal_client.subscribe(
        "openrouter/router/enterprise",
        arguments={
            "prompt": query,
            "system_prompt": system_prompt,
            "model": model,
            "temperature": temperature,
        },
    )

    output = result.get("output", "")
    if not output:
        raise ValueError(f"OpenRouter ({model}) returned an empty response.")

    # Extract usage metadata
    usage = result.get("usage", {})
    total_tokens = usage.get("total_tokens")
    cost_usd = usage.get("cost")

    logger.info(
        "Refinement complete",
        extra={"model": model, "tokens": total_tokens, "cost_usd": cost_usd},
    )

    return RefinerResult(
        text=output.strip(),
        model=model,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
    )
