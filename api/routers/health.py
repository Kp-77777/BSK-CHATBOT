"""Health check endpoint."""
from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/", response_model=HealthResponse)
def health_check():
    """Health check for server and monitoring."""
    return HealthResponse()
