"""
rest.py — REST API endpoints for CogniTree backend server.
"""

from fastapi import APIRouter
from python_backend.server.dependencies import get_token_telemetry

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for status monitoring."""
    return {"status": "ok", "service": "CogniTree Backend", "version": "1.0.0"}


@router.get("/api/telemetry")
async def token_telemetry():
    """Returns rolling 5h and 24h token consumption statistics."""
    return get_token_telemetry()
