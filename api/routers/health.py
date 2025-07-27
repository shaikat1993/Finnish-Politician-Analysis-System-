"""
Health check router for FPAS API
Provides system health check endpoints that integrate with verify_system.py
"""

import asyncio
import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from api.models.response import HealthCheckResponse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import system verifier
from verify_system import SystemVerifier

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        503: {"description": "Service Unavailable"},
        500: {"description": "Internal Server Error"},
    },
)

logger = logging.getLogger("fpas_api.health")

@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="System health check",
    description="Check the health status of all system components",
)
async def health_check():
    """
    Check the health of all system components.
    
    Returns:
        HealthCheckResponse: Health status of all components
    """
    try:
        # Use the existing system verifier
        verifier = SystemVerifier()
        
        # Run minimal health checks in parallel
        tasks = [
            verifier.verify_neo4j_integration(),
            verifier.verify_data_collection(),
            verifier.verify_ai_pipeline()
        ]
        
        await asyncio.gather(*tasks)
        
        # Determine overall status
        await verifier.determine_overall_status()
        
        # Convert verifier results to API response
        return HealthCheckResponse(
            components=verifier.results['checks'],
            overall_status=verifier.results['overall_status']
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get(
    "/neo4j",
    summary="Neo4j database health",
    description="Check Neo4j database connection and schema status"
)
async def neo4j_health():
    """
    Check Neo4j database health specifically.
    
    Returns:
        dict: Neo4j health status
    """
    try:
        verifier = SystemVerifier()
        await verifier.verify_neo4j_integration()
        
        if verifier.results['checks'].get('neo4j', {}).get('status') == 'failed':
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j database unavailable"
            )
            
        return verifier.results['checks']['neo4j']
    except Exception as e:
        logger.error(f"Neo4j health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Neo4j health check failed: {str(e)}"
        )

@router.get(
    "/ai-pipeline", 
    summary="AI pipeline health",
    description="Check AI pipeline components status"
)
async def ai_pipeline_health():
    """
    Check AI pipeline health specifically.
    
    Returns:
        dict: AI pipeline health status
    """
    try:
        verifier = SystemVerifier()
        await verifier.verify_ai_pipeline()
        
        if verifier.results['checks'].get('ai_pipeline', {}).get('status') == 'failed':
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI pipeline unavailable"
            )
            
        return verifier.results['checks']['ai_pipeline']
    except Exception as e:
        logger.error(f"AI pipeline health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI pipeline health check failed: {str(e)}"
        )

@router.get(
    "/data-collection",
    summary="Data collection health",
    description="Check data collection components status"
)
async def data_collection_health():
    """
    Check data collection health specifically.
    
    Returns:
        dict: Data collection health status
    """
    try:
        verifier = SystemVerifier()
        await verifier.verify_data_collection()
        
        if verifier.results['checks'].get('data_collection', {}).get('status') == 'failed':
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Data collection service unavailable"
            )
            
        return verifier.results['checks']['data_collection']
    except Exception as e:
        logger.error(f"Data collection health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data collection health check failed: {str(e)}"
        )
