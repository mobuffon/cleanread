"""
Health check endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    return HealthResponse(
        status="healthy",
        service="cleanread-api",
        version="0.1.0"
    )
