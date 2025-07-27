"""
Analysis router for FPAS API
Provides endpoints for AI-powered political analysis
"""

import sys
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Body
from typing import List, Dict, Any, Optional
import asyncio
import time
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import dependencies and models
from api.core.dependencies import get_db_session, get_ai_pipeline_service, get_analytics_service
from api.models.response import (
    AnalysisResponse,
    ErrorResponse
)
from api.models.request import (
    RelationshipAnalysisRequest,
    CoalitionAnalysisRequest,
    CustomAnalysisRequest
)
from neo4j import AsyncSession

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)

# In-memory store for analysis results
# In production, use a persistent storage solution like Redis
analysis_results = {}

@router.post(
    "/relationship-network",
    response_model=AnalysisResponse,
    summary="Analyze politician relationships",
    description="Analyze relationships between selected politicians"
)
async def analyze_relationship_network(
    request: RelationshipAnalysisRequest,
    session: AsyncSession = Depends(get_db_session),
    analytics_service = Depends(get_analytics_service)
):
    """
    Analyze relationships between selected politicians.
    
    Args:
        request: Relationship analysis request parameters
        session: Neo4j database session
        analytics_service: Neo4j analytics service
        
    Returns:
        AnalysisResponse: Relationship analysis results
    """
    start_time = time.time()
    
    try:
        # Verify all politician IDs exist
        for politician_id in request.politician_ids:
            check_query = "MATCH (p:Politician {id: $id}) RETURN p"
            check_result = await session.run(check_query, {"id": politician_id})
            check_record = await check_result.single()
            
            if not check_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Politician with ID {politician_id} not found"
                )
        
        # Use the analytics service to perform the relationship analysis
        relationship_network = await analytics_service.analyze_politician_network(
            politician_ids=request.politician_ids,
            depth=request.depth,
            include_evidence=request.include_evidence
        )
        
        processing_time = time.time() - start_time
        
        return AnalysisResponse(
            query=f"Relationship network analysis for {len(request.politician_ids)} politicians with depth {request.depth}",
            result=relationship_network,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post(
    "/coalition-potential",
    response_model=AnalysisResponse,
    summary="Analyze coalition potential",
    description="Analyze potential coalition formation between political parties"
)
async def analyze_coalition_potential(
    request: CoalitionAnalysisRequest,
    session: AsyncSession = Depends(get_db_session),
    analytics_service = Depends(get_analytics_service)
):
    """
    Analyze potential coalition formation between political parties.
    
    Args:
        request: Coalition analysis request parameters
        session: Neo4j database session
        analytics_service: Neo4j analytics service
        
    Returns:
        AnalysisResponse: Coalition potential analysis results
    """
    start_time = time.time()
    
    try:
        # Verify all party IDs exist
        for party_id in request.party_ids:
            check_query = "MATCH (p:Party {id: $id}) RETURN p"
            check_result = await session.run(check_query, {"id": party_id})
            check_record = await check_result.single()
            
            if not check_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Party with ID {party_id} not found"
                )
        
        # Use the analytics service to perform the coalition analysis
        coalition_analysis = await analytics_service.analyze_coalition_potential(
            party_ids=request.party_ids,
            include_historical=request.include_historical
        )
        
        processing_time = time.time() - start_time
        
        return AnalysisResponse(
            query=f"Coalition potential analysis for {len(request.party_ids)} parties",
            result=coalition_analysis,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

async def run_custom_analysis(
    analysis_id: str,
    query: str,
    context_ids: Optional[List[str]],
    detailed: bool,
    ai_service
):
    """
    Background task to run custom AI analysis.
    
    Args:
        analysis_id: Unique ID for the analysis task
        query: Natural language query
        context_ids: IDs of entities to include as context
        detailed: Whether to generate detailed response
        ai_service: AI pipeline service
    """
    try:
        # Update status to in-progress
        analysis_results[analysis_id] = {
            "status": "processing",
            "query": query,
            "start_time": time.time()
        }
        
        # Run the analysis using the AI pipeline
        supervisor_agent = ai_service
        
        # Create a request for the AI pipeline
        request = {
            "query": query,
            "context_ids": context_ids or [],
            "detailed": detailed
        }
        
        # Run the analysis using the supervisor agent
        result = await supervisor_agent.analyze_query(request)
        
        # Update status to completed
        processing_time = time.time() - analysis_results[analysis_id]["start_time"]
        analysis_results[analysis_id] = {
            "status": "completed",
            "query": query,
            "result": result,
            "processing_time": processing_time
        }
        
    except Exception as e:
        # Update status to failed
        analysis_results[analysis_id] = {
            "status": "failed",
            "query": query,
            "error": str(e)
        }

@router.post(
    "/custom",
    summary="Submit custom analysis request",
    description="Submit a natural language query for custom AI analysis"
)
async def submit_custom_analysis(
    request: CustomAnalysisRequest,
    background_tasks: BackgroundTasks,
    ai_service = Depends(get_ai_pipeline_service)
):
    """
    Submit a custom analysis request to be processed asynchronously.
    
    Args:
        request: Custom analysis request parameters
        background_tasks: FastAPI background tasks
        ai_service: AI pipeline service
        
    Returns:
        dict: Analysis task information and status URL
    """
    try:
        # Generate a unique ID for the analysis task
        analysis_id = str(uuid.uuid4())
        
        # Schedule the analysis to run in the background
        background_tasks.add_task(
            run_custom_analysis,
            analysis_id=analysis_id,
            query=request.query,
            context_ids=request.context_ids,
            detailed=request.detailed_response,
            ai_service=ai_service
        )
        
        # Return task information
        return {
            "status": "accepted",
            "analysis_id": analysis_id,
            "query": request.query,
            "status_url": f"/analysis/status/{analysis_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit analysis request: {str(e)}"
        )

@router.get(
    "/status/{analysis_id}",
    summary="Get analysis status",
    description="Check the status of a custom analysis request"
)
async def get_analysis_status(
    analysis_id: str
):
    """
    Check the status of a previously submitted analysis request.
    
    Args:
        analysis_id: Analysis task ID
        
    Returns:
        dict: Analysis status and results if completed
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis task with ID {analysis_id} not found"
        )
        
    return analysis_results[analysis_id]

@router.get(
    "/sentiment/politicians",
    summary="Get politician sentiment analysis",
    description="Get sentiment analysis for politicians based on news coverage"
)
async def get_politician_sentiment(
    session: AsyncSession = Depends(get_db_session),
    analytics_service = Depends(get_analytics_service),
    limit: int = 10
):
    """
    Get sentiment analysis for politicians based on news coverage.
    
    Args:
        session: Neo4j database session
        analytics_service: Neo4j analytics service
        limit: Maximum number of politicians to include
        
    Returns:
        dict: Politician sentiment analysis results
    """
    try:
        # Use the analytics service to calculate politician sentiment
        sentiment_analysis = await analytics_service.calculate_politician_sentiment(limit=limit)
        
        return {
            "status": "success",
            "data": sentiment_analysis,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )

@router.get(
    "/topics/trending",
    summary="Get trending political topics",
    description="Get currently trending political topics from news analysis"
)
async def get_trending_topics(
    session: AsyncSession = Depends(get_db_session),
    analytics_service = Depends(get_analytics_service),
    days: int = 30,
    limit: int = 10
):
    """
    Get trending political topics from recent news.
    
    Args:
        session: Neo4j database session
        analytics_service: Neo4j analytics service
        days: Number of past days to analyze
        limit: Maximum number of topics to return
        
    Returns:
        dict: Trending topics analysis results
    """
    try:
        # Use the analytics service to identify trending topics
        trending_topics = await analytics_service.identify_trending_topics(
            days=days,
            limit=limit
        )
        
        return {
            "status": "success",
            "data": trending_topics,
            "timespan": f"Past {days} days",
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic analysis failed: {str(e)}"
        )
