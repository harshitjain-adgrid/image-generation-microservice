import os
import fal_client
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize Gemini API Client
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

from services.prompts import COUPON_SYSTEM_PROMPT

# Supported refiner models — all verified working on fal.ai (tested Aug 2026)
REFINERS = {
    # Gemini models (via google-genai SDK — uses GEMINI_API_KEY)
    "gemini-3.1-flash-lite": {"provider": "gemini", "model": "gemini-3.1-flash-lite"},
    "gemini-2.5-flash":      {"provider": "gemini", "model": "gemini-2.5-flash"},
    
    # OpenAI models (via fal.ai OpenRouter — uses FAL_KEY)
    "gpt-4.1-mini":  {"provider": "openrouter", "model": "openai/gpt-4.1-mini"},
    
    # Other models (via fal.ai OpenRouter — uses FAL_KEY)
    "deepseek-chat":     {"provider": "openrouter", "model": "deepseek/deepseek-chat"},
    "claude-haiku-4.5":  {"provider": "openrouter", "model": "anthropic/claude-haiku-4.5"},
    "claude-sonnet-5":   {"provider": "openrouter", "model": "anthropic/claude-sonnet-5"},
}

DEFAULT_REFINER = "gemini-3.1-flash-lite"


def _refine_with_gemini(query: str, model_name: str) -> str:
    """Refine prompt using Gemini via google-genai SDK."""
    response = gemini_client.models.generate_content(
        model=model_name,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=COUPON_SYSTEM_PROMPT
        )
    )
    if not response.text:
        raise ValueError("Gemini returned an empty or blocked response.")
    return response.text.strip()


def _refine_with_openrouter(query: str, model_name: str) -> str:
    """Refine prompt using any LLM via fal.ai's OpenRouter integration."""
    result = fal_client.subscribe(
        "openrouter/router/enterprise",
        arguments={
            "prompt": query,
            "system_prompt": COUPON_SYSTEM_PROMPT,
            "model": model_name,
            "temperature": 0.7,
        }
    )
    
    output = result.get("output", "")
    if not output:
        raise ValueError(f"OpenRouter ({model_name}) returned an empty response.")
    
    # Print cost info if available
    usage = result.get("usage", {})
    if usage:
        cost = usage.get("cost", 0)
        total_tokens = usage.get("total_tokens", 0)
        print(f"  Refiner usage: {total_tokens} tokens, cost: ${cost:.6f}")
    
    return output.strip()


def refine_prompt(query: str, refiner: str = "") -> str:
    """
    Refines a simple user query into a detailed prompt.
    
    Args:
        query: The merchant's JSON payload as a string.
        refiner: The refiner model to use. See REFINERS dict for options.
                 Empty string uses the default refiner.
    """
    if not query:
        raise ValueError("Query cannot be empty.")
    
    # Use default if not specified
    refiner_key = refiner if refiner else DEFAULT_REFINER
    
    # Look up the refiner config
    if refiner_key not in REFINERS:
        available = ", ".join(REFINERS.keys())
        raise ValueError(f"Unknown refiner '{refiner_key}'. Available: {available}")
    
    config = REFINERS[refiner_key]
    provider = config["provider"]
    model_name = config["model"]
    
    print(f"\n{'='*60}")
    print(f"PROMPT REFINER: {refiner_key} (provider: {provider}, model: {model_name})")
    print(f"{'='*60}")
    
    if provider == "gemini":
        return _refine_with_gemini(query, model_name)
    elif provider == "openrouter":
        return _refine_with_openrouter(query, model_name)
    else:
        raise ValueError(f"Unknown provider: {provider}")
