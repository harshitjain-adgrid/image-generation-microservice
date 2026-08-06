import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize Gemini API Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Use gemini-2.5-flash as default (latest recommended model per official docs)
MODEL_NAME = "gemini-3.1-flash-lite"

from services.prompts import COUPON_SYSTEM_PROMPT


def refine_prompt(query: str) -> str:
    """
    Refines a simple user query into a detailed prompt using Gemini.
    """
    if not query:
        raise ValueError("Query cannot be empty.")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=COUPON_SYSTEM_PROMPT
        )
    )
    if not response.text:
        raise ValueError("Gemini returned an empty or blocked response.")
        
    return response.text.strip()
