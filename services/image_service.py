import os
import fal_client
from dotenv import load_dotenv

load_dotenv()

# Safety rules appended to GPT Image 2 prompts (it's a reasoning model, so it follows constraints)
GPT_SAFETY_SUFFIX = (
    '\n\nSTRICT RULES: Do not render any real-world brand names, logos, or trademarks '
    'anywhere in the image unless they are explicitly named in this prompt. '
    'All products must appear completely unbranded with blank/plain labels. '
    'Any brand names that ARE explicitly mentioned in this prompt MUST be rendered accurately.'
)

# System prompt for Nano Banana models (uses the dedicated system_prompt field)
NANO_BANANA_SYSTEM_PROMPT = (
    'You are generating a commercial promotional banner. '
    'STRICT RULES: Do not include any real-world brand names, logos, or trademarks '
    'unless they are explicitly named in the user prompt. '
    'All products must appear completely unbranded unless specified otherwise. '
    'Render all text exactly as described with zero spelling errors.'
)


def generate_image(prompt: str, model_name: str = "fal-ai/gpt-image-2", quality: str = "low") -> str:
    """
    Generates an image using Fal.ai and returns the image URL.
    
    Args:
        prompt (str): The refined prompt for image generation.
        model_name (str): The Fal.ai model endpoint. 
        quality (str): The quality setting, primarily used for gpt-image-2.
    
    Returns:
        str: The URL of the generated image.
    """
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    # Build the arguments based on model type
    args = {
        "prompt": prompt,
    }
    
    # GPT Image 2: uses "image_size" presets + safety suffix + quality
    if "gpt-image-2" in model_name:
        args["image_size"] = "landscape_4_3"
        args["prompt"] = prompt + GPT_SAFETY_SUFFIX
        args["quality"] = quality
    
    # Nano Banana models: uses "aspect_ratio" ratios + system_prompt
    elif "nano-banana" in model_name:
        args["aspect_ratio"] = "4:3"
        args["system_prompt"] = NANO_BANANA_SYSTEM_PROMPT
    
    # Diffusion models (Flux, Ideogram, Kling): use image_size, no safety rules
    else:
        args["image_size"] = "landscape_4_3"

    print(f"Calling fal.ai model: {model_name} (Quality: {quality}) with prompt:\n{args['prompt']}\n")

    try:
        result = fal_client.subscribe(
            model_name,
            arguments=args,
        )
        
        if "images" in result and len(result["images"]) > 0:
            return result["images"][0]["url"]
        else:
            raise Exception("No images found in the response from fal.ai")

    except Exception as e:
        print(f"Error generating image with fal.ai: {e}")
        raise

