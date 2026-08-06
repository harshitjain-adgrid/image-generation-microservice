import os
import fal_client
from dotenv import load_dotenv

load_dotenv()

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

    print(f"Calling fal.ai model: {model_name} (Quality: {quality}) with prompt:\n{prompt}\n")

    try:
        # fal_client will automatically use the FAL_KEY environment variable
        
        args = {
            "prompt": prompt,
            "image_size": "landscape_4_3" # Defaulting to landscape
        }
        
        # Pass quality if the model supports it (like gpt-image-2)
        if "gpt-image-2" in model_name:
            args["quality"] = quality
            
        result = fal_client.subscribe(
            model_name,
            arguments=args,
        )
        
        # Typically the result contains an 'images' array with dictionaries
        if "images" in result and len(result["images"]) > 0:
            return result["images"][0]["url"]
        else:
            raise Exception("No images found in the response from fal.ai")

    except Exception as e:
        print(f"Error generating image with fal.ai: {e}")
        raise
