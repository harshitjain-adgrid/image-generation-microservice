from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "image-generation-microservice"}
