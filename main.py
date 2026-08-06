from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from services.prompt_service import refine_prompt
from services.image_service import generate_image
from services.storage_service import save_image_from_url

app = FastAPI(
    title="Image Generation Microservice",
    description="A basic pipeline to test text-to-image models on Fal.ai with Gemini prompt refinement.",
    version="1.0.0"
)

class GenerateRequest(BaseModel):
    query: str
    model: str = "fal-ai/gpt-image-2"
    quality: str = "low" # Options: low, medium, high
class GenerateResponse(BaseModel):
    original_query: str
    refined_prompt: str
    image_url: str
    local_path: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Image generation microservice is running."}

@app.post("/generate", response_model=GenerateResponse)
def generate_endpoint(request: GenerateRequest):
    """
    1. Refines the user query via Gemini
    2. Sends the refined prompt to Fal.ai
    3. Downloads and saves the resulting image to the local output folder
    """
    
    # 1. Refine the Prompt
    try:
        refined_prompt = refine_prompt(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt refinement failed: {str(e)}")
        
    # 2. Generate Image via Fal.ai
    try:
        image_url = generate_image(prompt=refined_prompt, model_name=request.model, quality=request.quality)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
        
    # 3. Save the image locally
    try:
        local_path = save_image_from_url(image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image saving failed: {str(e)}")
        
    return GenerateResponse(
        original_query=request.query,
        refined_prompt=refined_prompt,
        image_url=image_url,
        local_path=local_path
    )

if __name__ == "__main__":
    import uvicorn
    # To run locally: uvicorn main:app --reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
