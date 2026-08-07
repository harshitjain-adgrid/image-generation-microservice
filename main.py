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
    refiner: str = "" # Options: gemini-3.1-flash-lite, gpt-4.1-nano, gpt-4o-mini, deepseek-v3, claude-haiku
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
    1. Refines the user query via the configured refiner (Gemini, GPT, etc.)
    2. Sends the refined prompt to the configured image model on Fal.ai
    3. Downloads and saves the resulting image to the local output folder
    """
    
    print(f"\n{'#'*60}")
    print(f"NEW REQUEST")
    print(f"  Text Refiner : {request.refiner or 'gemini-3.1-flash-lite (default)'}")
    print(f"  Image Model  : {request.model}")
    print(f"  Quality      : {request.quality}")
    print(f"{'#'*60}")
    
    # 1. Refine the Prompt
    try:
        refined_prompt = refine_prompt(request.query, refiner=request.refiner)
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
