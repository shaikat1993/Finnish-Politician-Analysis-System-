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
import json
from pathlib import Path

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

# File-based backup for Docker environment
DOCKER_CACHE_DIR = Path("/app/cache")
if os.environ.get("ENVIRONMENT") == "docker":
    # Docker environment
    CACHE_DIR = DOCKER_CACHE_DIR
else:
    # Local environment
    CACHE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "cache"

if not CACHE_DIR.exists():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created cache directory: {CACHE_DIR}")
    except Exception as e:
        print(f"Could not create cache directory: {e}")
        # Fallback to a directory that should be writable
        CACHE_DIR = Path.home() / ".fpas_cache"
        CACHE_DIR.mkdir(exist_ok=True)
        print(f"Using fallback cache directory: {CACHE_DIR}")

# In-memory store for analysis results
# In production, use a persistent storage solution like Redis
analysis_results = {}

# Query cache for faster responses to similar questions
query_cache = {}

def save_result(analysis_id, data):
    """Save result to both memory and file (for Docker)"""
    # Save to memory
    analysis_results[analysis_id] = data
    
    # If this is a completed result, also cache by query for faster future responses
    if data.get("status") == "completed" and "query" in data and "result" in data:
        # Normalize the query (lowercase, remove extra spaces)
        query_key = " ".join(data["query"].lower().split())
        
        # Store in query cache with timestamp
        query_cache[query_key] = {
            "result": data["result"],
            "timestamp": time.time(),
            "original_id": analysis_id
        }
    
    # Also save to file for Docker persistence
    try:
        # Create a serializable copy of the data
        serializable_data = {}
        for key, value in data.items():
            # Handle special cases that aren't JSON serializable
            if key == "result" and isinstance(value, dict):
                # Create a clean copy of the result
                result_copy = {}
                for k, v in value.items():
                    # Convert non-serializable objects to strings
                    if isinstance(v, (str, int, float, bool, type(None))):
                        result_copy[k] = v
                    elif isinstance(v, list):
                        # Handle lists with potential non-serializable items
                        result_copy[k] = [str(item) if not isinstance(item, (str, int, float, bool, dict, type(None))) else item for item in v]
                    else:
                        # Convert other types to string representation
                        result_copy[k] = str(v)
                serializable_data[key] = result_copy
            elif isinstance(value, (str, int, float, bool, type(None))):
                # Basic types are directly serializable
                serializable_data[key] = value
            else:
                # Convert other types to string
                serializable_data[key] = str(value)
        
        # Add timestamp if not present
        if "timestamp" not in serializable_data:
            serializable_data["timestamp"] = time.time()
            
        cache_file = CACHE_DIR / f"{analysis_id}.json"
        with open(cache_file, 'w') as f:
            json.dump(serializable_data, f)
            
        # Verify the file was written correctly
        try:
            with open(cache_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Created corrupted JSON file for {analysis_id}. Removing it.")
            cache_file.unlink()
            
    except Exception as e:
        print(f"Warning: Could not save to file cache: {e}")
    
    return data

def get_result(analysis_id):
    """Get result from memory or file (for Docker)"""
    # Try memory first (fastest)
    if analysis_id in analysis_results:
        return analysis_results[analysis_id]
    
    # Try file as fallback (for Docker)
    try:
        cache_file = CACHE_DIR / f"{analysis_id}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Update memory cache
                analysis_results[analysis_id] = data
                return data
    except Exception as e:
        print(f"Warning: Could not read from file cache: {e}")
    
    return None

def find_similar_query(query, max_age_hours=24):
    """Find a similar query in the cache"""
    if not query:
        return None
        
    # Normalize the query
    query_key = " ".join(query.lower().split())
    
    # Check for exact match first
    if query_key in query_cache:
        cached = query_cache[query_key]
        
        # Check if it's not too old
        if (time.time() - cached.get("timestamp", 0)) < (max_age_hours * 3600):
            return cached
    
    # TODO: Add fuzzy matching for similar queries
    # This would require a more sophisticated algorithm
    
    return None

def clean_cache_directory():
    """Clean up corrupted cache files"""
    try:
        print(f"Cleaning up cache directory: {CACHE_DIR}")
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                # Try to read the file to see if it's valid JSON
                with open(cache_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                # If it's not valid JSON, delete the file
                print(f"Removing corrupted cache file: {cache_file}")
                cache_file.unlink()
    except Exception as e:
        print(f"Error cleaning cache directory: {e}")

@router.on_event("startup")
async def startup_event():
    """Initialize the API on startup"""
    # Clean up corrupted cache files first
    clean_cache_directory()
    
    # Ensure cache directory exists
    try:
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Created cache directory: {CACHE_DIR}")
        
        # Load existing results from file cache
        file_count = 0
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    analysis_id = cache_file.stem
                    data = json.load(f)
                    analysis_results[analysis_id] = data
                    file_count += 1
                    
                    # Also populate the query cache
                    if data.get("status") == "completed" and "query" in data and "result" in data:
                        query_key = " ".join(data["query"].lower().split())
                        query_cache[query_key] = {
                            "result": data["result"],
                            "timestamp": data.get("timestamp", time.time()),
                            "original_id": analysis_id
                        }
            except Exception as e:
                print(f"Error loading cache file {cache_file}: {e}")
        
        if file_count > 0:
            print(f"Loaded {file_count} analysis results from file cache")
            print(f"Populated query cache with {len(query_cache)} entries")
    except Exception as e:
        print(f"Warning: Cache initialization failed: {e}")

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
            check_query = """
            MATCH (p:Politician)
            WHERE p.politician_id = $id OR p.id = $id
            RETURN p
            """
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
        save_result(analysis_id, {
            "status": "processing",
            "query": query,
            "start_time": time.time()
        })
        
        # Run the analysis using the AI pipeline
        supervisor_agent = ai_service
        
        # Create a request for the AI pipeline
        request = {
            "query": query,
            "context_ids": context_ids or [],
            "detailed": detailed
        }
        
        # Run the analysis using the orchestrator (chat/QA)
        result = await supervisor_agent.process_user_query(
            query=request["query"],
            context={"selected_politician": request["context_ids"][0] if request["context_ids"] else None,
                    "detailed": request.get("detailed", False)}
        )
        
        # Update status to completed
        cached_data = get_result(analysis_id)
        start_time = cached_data.get("start_time", time.time() - 5) if cached_data else time.time() - 5
        processing_time = time.time() - start_time
        
        save_result(analysis_id, {
            "status": "completed",
            "query": query,
            "result": result,
            "processing_time": processing_time
        })
        
    except Exception as e:
        # Update status to failed
        save_result(analysis_id, {
            "status": "failed",
            "query": query,
            "error": str(e)
        })

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
        # Check if a similar query exists in the cache
        cached = find_similar_query(request.query)
        if cached:
            # Generate a new ID for this request
            analysis_id = str(uuid.uuid4())
            
            # Create an instant response using the cached result
            instant_result = {
                "status": "completed",
                "query": request.query,
                "result": cached["result"],
                "processing_time": 0,
                "cached": True,
                "timestamp": time.time()
            }
            
            # Save this result with the new ID
            save_result(analysis_id, instant_result)
            
            # Return success with the new ID
            return {
                "status": "accepted",
                "analysis_id": analysis_id,
                "query": request.query,
                "status_url": f"/analysis/status/{analysis_id}",
                "cached": True
            }
        
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
    result = get_result(analysis_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis task with ID {analysis_id} not found"
        )
        
    return result

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
