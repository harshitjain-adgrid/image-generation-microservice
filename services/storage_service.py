import os
import requests
import uuid
from urllib.parse import urlparse

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

def save_image_from_url(url: str) -> str:
    """
    Downloads an image from a URL and saves it to the output directory.
    
    Args:
        url (str): The URL of the image to download.
        
    Returns:
        str: The absolute path to the saved image file.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Try to extract the extension from the URL, otherwise default to .jpg
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1]
    if not ext:
        ext = ".jpg"

    filename = f"image_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        print(f"Downloading image from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print(f"Image successfully saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error downloading or saving image: {e}")
        raise
