"""
Image Generation Microservice.

Load environment variables at import time so that all providers
(fal_client, etc.) can pick up FAL_KEY automatically.
"""

from dotenv import load_dotenv

load_dotenv()
