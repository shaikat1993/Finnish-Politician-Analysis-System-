#!/usr/bin/env python3
"""
Health check API endpoints for Finnish Political Analysis System
"""

from fastapi import APIRouter, Response, status
from typing import Dict, Any
import time

# Create router
router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", summary="Get system health status")
async def get_health_status() -> Dict[str, Any]:
    """
    Get system health status
    
    Returns overall system health status
    """
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@router.get("/live", summary="Liveness probe")
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe
    
    Simple endpoint to check if the API is running
    """
    return {"status": "alive"}

@router.get("/ready", summary="Readiness probe")
async def readiness_probe() -> Dict[str, Any]:
    """
    Readiness probe
    
    Checks if the system is ready to handle requests
    """
    return {
        "status": "ready",
        "ready": True
    }
