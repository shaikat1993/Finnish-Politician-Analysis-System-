"""
News router for FPAS API
Provides endpoints for news article data and analysis
"""

import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from datetime import datetime, timedelta
from neo4j import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import dependencies and models
from api.core.dependencies import get_db_session, get_ai_pipeline_service
from api.models.response import (
    NewsArticleResponse, 
    NewsListResponse,
    ErrorResponse
)
from api.models.request import NewsSearch

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)

@router.get(
    "/",
    response_model=NewsListResponse,
    summary="List news articles",
    description="Get a paginated list of news articles with optional filtering"
)
async def list_news_articles(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by news source"),
    days: Optional[int] = Query(30, ge=1, le=365, description="Show articles from last X days")
):
    """
    Get a paginated list of news articles with optional filtering.
    
    Args:
        session: Neo4j database session
        page: Page number (1-indexed)
        limit: Number of items per page
        source: Filter by news source
        days: Show articles from last X days
        
    Returns:
        NewsListResponse: List of news articles with pagination info
    """
    # Calculate pagination and date filter
    skip = (page - 1) * limit
    start_date = datetime.now() - timedelta(days=days) if days else None
    
    # Build Cypher query with parameters
    query = """
    MATCH (n:News)
    WHERE 
        ($source IS NULL OR n.source = $source)
        AND ($start_date IS NULL OR n.published_date >= $start_date)
    RETURN n
    ORDER BY n.published_date DESC
    SKIP $skip
    LIMIT $limit
    """
    
    # Also get total count for pagination
    count_query = """
    MATCH (n:News)
    WHERE 
        ($source IS NULL OR n.source = $source)
        AND ($start_date IS NULL OR n.published_date >= $start_date)
    RETURN count(n) AS total
    """
    
    try:
        # Run queries
        result = await session.run(query, {
            "source": source,
            "start_date": start_date.isoformat() if start_date else None,
            "skip": skip,
            "limit": limit
        })
        
        news_articles = [record["n"] for record in await result.fetch_all()]
        
        count_result = await session.run(count_query, {
            "source": source,
            "start_date": start_date.isoformat() if start_date else None
        })
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/news?page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/news?page={page-1}&limit={limit}" if page > 1 else None
        
        if source:
            next_page = f"{next_page}&source={source}" if next_page else None
            prev_page = f"{prev_page}&source={source}" if prev_page else None
            
        if days:
            next_page = f"{next_page}&days={days}" if next_page else None
            prev_page = f"{prev_page}&days={days}" if prev_page else None
        
        return NewsListResponse(
            page=page,
            limit=limit,
            total=total,
            next_page=next_page,
            prev_page=prev_page,
            data=news_articles
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news articles: {str(e)}"
        )

@router.get(
    "/{news_id}",
    response_model=NewsArticleResponse,
    summary="Get news article details",
    description="Get detailed information about a specific news article"
)
async def get_news_article(
    news_id: str = Path(..., description="News article ID"),
    session: AsyncSession = Depends(get_db_session),
    include_politicians: bool = Query(True, description="Include mentioned politicians")
):
    """
    Get detailed information about a specific news article.
    
    Args:
        news_id: News article ID
        session: Neo4j database session
        include_politicians: Include politicians mentioned in the article
        
    Returns:
        NewsArticleResponse: News article details
    """
    try:
        # Base query for news article data
        query = """
        MATCH (n:News {id: $id})
        RETURN n
        """
        
        result = await session.run(query, {"id": news_id})
        record = await result.single()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"News article with ID {news_id} not found"
            )
            
        news_article = record["n"]
        
        # Get mentioned politicians if requested
        if include_politicians:
            politicians_query = """
            MATCH (n:News {id: $id})<-[:MENTIONED_IN]-(p:Politician)
            RETURN p
            """
            
            politicians_result = await session.run(politicians_query, {"id": news_id})
            politicians_records = await politicians_result.fetch_all()
            politicians = [record["p"] for record in politicians_records]
            news_article["politicians"] = politicians
            
        return news_article
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news article: {str(e)}"
        )

@router.get(
    "/search",
    response_model=NewsListResponse,
    summary="Search news articles",
    description="Search for news articles by content or other attributes"
)
async def search_news(
    query: str = Query(..., min_length=2, description="Search query"),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page")
):
    """
    Search for news articles by content or other attributes.
    
    Args:
        query: Search query string
        session: Neo4j database session
        page: Page number
        limit: Items per page
        
    Returns:
        NewsListResponse: List of matching news articles
    """
    try:
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Build case-insensitive search query
        search_query = """
        MATCH (n:News)
        WHERE toLower(n.title) CONTAINS toLower($query)
           OR toLower(n.content) CONTAINS toLower($query)
           OR toLower(n.summary) CONTAINS toLower($query)
           OR toLower(n.source) CONTAINS toLower($query)
        RETURN n
        ORDER BY n.published_date DESC
        SKIP $skip
        LIMIT $limit
        """
        
        # Also get total count for pagination
        count_query = """
        MATCH (n:News)
        WHERE toLower(n.title) CONTAINS toLower($query)
           OR toLower(n.content) CONTAINS toLower($query)
           OR toLower(n.summary) CONTAINS toLower($query)
           OR toLower(n.source) CONTAINS toLower($query)
        RETURN count(n) AS total
        """
        
        # Run queries
        result = await session.run(search_query, {
            "query": query,
            "skip": skip,
            "limit": limit
        })
        
        news_articles = [record["n"] for record in await result.fetch_all()]
        
        count_result = await session.run(count_query, {"query": query})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/news/search?query={query}&page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/news/search?query={query}&page={page-1}&limit={limit}" if page > 1 else None
        
        return NewsListResponse(
            page=page,
            limit=limit,
            total=total,
            next_page=next_page,
            prev_page=prev_page,
            data=news_articles
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get(
    "/by-politician/{politician_id}",
    response_model=NewsListResponse,
    summary="Get news by politician",
    description="Get news articles mentioning a specific politician"
)
async def get_news_by_politician(
    politician_id: str = Path(..., description="Politician ID"),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get news articles mentioning a specific politician.
    
    Args:
        politician_id: Politician ID
        session: Neo4j database session
        page: Page number
        limit: Items per page
        
    Returns:
        NewsListResponse: List of news articles mentioning the politician
    """
    try:
        # Check if politician exists
        check_query = "MATCH (p:Politician {id: $id}) RETURN p"
        check_result = await session.run(check_query, {"id": politician_id})
        check_record = await check_result.single()
        
        if not check_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Politician with ID {politician_id} not found"
            )
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get news articles
        news_query = """
        MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
        RETURN n
        ORDER BY n.published_date DESC
        SKIP $skip
        LIMIT $limit
        """
        
        # Also get total count for pagination
        count_query = """
        MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
        RETURN count(n) AS total
        """
        
        # Execute queries
        result = await session.run(news_query, {
            "id": politician_id,
            "skip": skip,
            "limit": limit
        })
        
        news_articles = [record["n"] for record in await result.fetch_all()]
        
        count_result = await session.run(count_query, {"id": politician_id})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/news/by-politician/{politician_id}?page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/news/by-politician/{politician_id}?page={page-1}&limit={limit}" if page > 1 else None
        
        return NewsListResponse(
            page=page,
            limit=limit,
            total=total,
            next_page=next_page,
            prev_page=prev_page,
            data=news_articles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news articles: {str(e)}"
        )
