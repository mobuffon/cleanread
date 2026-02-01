"""
API v1 Router
Combines all API endpoint routers
"""
from fastapi import APIRouter

from app.api.v1.endpoints import upload, convert, health, auth

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(convert.router, prefix="/convert", tags=["convert"])
