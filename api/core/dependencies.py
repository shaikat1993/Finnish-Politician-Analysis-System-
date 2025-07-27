"""
Dependency injection providers for FPAS API
Handles database sessions and common dependencies
"""

import sys
import os
from fastapi import Depends, HTTPException, status
from typing import AsyncGenerator
from neo4j import AsyncDriver, AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing Neo4j connection manager from the project
from database.neo4j_connection import get_neo4j_connection

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a Neo4j database session using the existing connection manager.
    This dependency can be injected into API endpoints.
    
    Returns:
        AsyncGenerator[AsyncSession, None]: Neo4j async session
    """
    try:
        async with get_neo4j_connection() as session:
            yield session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}",
        )

# Get Neo4j analytics functions from the existing project
async def get_analytics_service():
    """
    Get Neo4j analytics service from the existing project
    
    Returns:
        Neo4jAnalytics: Analytics service instance
    """
    try:
        from database import get_neo4j_analytics
        return get_neo4j_analytics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analytics service unavailable: {str(e)}",
        )

# Get AI pipeline tools
async def get_ai_pipeline_service():
    """
    Get AI pipeline service (SupervisorAgent) from the existing project
    
    Returns:
        SupervisorAgent: AI pipeline supervisor agent
    """
    try:
        from ai_pipeline.agents.supervisor_agent import SupervisorAgent
        return SupervisorAgent()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI pipeline service unavailable: {str(e)}",
        )

# Get data collection service
async def get_collection_service():
    """
    Get data collection service from the existing project
    
    Returns:
        CollectorNeo4jBridge: Collector service
    """
    try:
        from database import CollectorNeo4jBridge
        return CollectorNeo4jBridge()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Collection service unavailable: {str(e)}",
        )
