"""
Politicians router for FPAS API
Provides endpoints for politician data access and management
"""

import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from neo4j import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import dependencies and models
from api.core.dependencies import get_db_session, get_analytics_service
from api.models.response import (
    PoliticianResponse, 
    PoliticianListResponse,
    RelationshipResponse,
    ErrorResponse
)
from api.models.request import PoliticianSearch, PoliticianCreate, PoliticianUpdate

router = APIRouter(
    prefix="/politicians",
    tags=["politicians"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)

@router.get(
    "/",
    response_model=PoliticianListResponse,
    summary="List politicians",
    description="Get a paginated list of politicians with optional filtering"
)
async def list_politicians(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    party: Optional[str] = Query(None, description="Filter by political party"),
    active_only: bool = Query(False, description="Show only active politicians")
):
    """
    Get a paginated list of politicians with optional filtering.
    
    Args:
        session: Neo4j database session
        page: Page number (1-indexed)
        limit: Number of items per page
        party: Filter by political party
        active_only: Show only active politicians
        
    Returns:
        PoliticianListResponse: List of politicians with pagination info
    """
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Build Cypher query with parameters
    query = """
    MATCH (p:Politician)
    WHERE 
        ($party IS NULL OR p.party = $party)
        AND ($active_only = False OR p.active = True)
    RETURN p
    ORDER BY p.name
    SKIP $skip
    LIMIT $limit
    """
    
    # Also get total count for pagination
    count_query = """
    MATCH (p:Politician)
    WHERE 
        ($party IS NULL OR p.party = $party)
        AND ($active_only = False OR p.active = True)
    RETURN count(p) AS total
    """
    
    try:
        # Run queries
        result = await session.run(query, {
            "party": party,
            "active_only": active_only,
            "skip": skip,
            "limit": limit
        })
        
        politicians = [record["p"] for record in await result.fetch_all()]
        
        count_result = await session.run(count_query, {
            "party": party,
            "active_only": active_only
        })
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/politicians?page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/politicians?page={page-1}&limit={limit}" if page > 1 else None
        
        if party:
            next_page = f"{next_page}&party={party}" if next_page else None
            prev_page = f"{prev_page}&party={party}" if prev_page else None
            
        if active_only:
            next_page = f"{next_page}&active_only=true" if next_page else None
            prev_page = f"{prev_page}&active_only=true" if prev_page else None
        
        return PoliticianListResponse(
            page=page,
            limit=limit,
            total=total,
            next_page=next_page,
            prev_page=prev_page,
            data=politicians
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch politicians: {str(e)}"
        )

@router.get(
    "/{politician_id}",
    response_model=PoliticianResponse,
    summary="Get politician details",
    description="Get detailed information about a specific politician"
)
async def get_politician(
    politician_id: str = Path(..., description="Politician ID"),
    session: AsyncSession = Depends(get_db_session),
    include_news: bool = Query(True, description="Include latest news"),
    include_relationships: bool = Query(False, description="Include relationship data")
):
    """
    Get detailed information about a specific politician.
    
    Args:
        politician_id: Politician ID
        session: Neo4j database session
        include_news: Include latest news about the politician
        include_relationships: Include politician's relationships
        
    Returns:
        PoliticianResponse: Politician details
    """
    try:
        # Base query for politician data
        query = """
        MATCH (p:Politician {id: $id})
        RETURN p
        """
        
        result = await session.run(query, {"id": politician_id})
        record = await result.single()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Politician with ID {politician_id} not found"
            )
            
        politician = record["p"]
        
        # Get latest news if requested
        if include_news:
            news_query = """
            MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
            RETURN n
            ORDER BY n.published_date DESC
            LIMIT 5
            """
            
            news_result = await session.run(news_query, {"id": politician_id})
            news_records = await news_result.fetch_all()
            latest_news = [record["n"] for record in news_records]
            politician["latest_news"] = latest_news
            
        # Get relationships if requested
        if include_relationships:
            relations_query = """
            MATCH (p:Politician {id: $id})-[r]-(other:Politician)
            RETURN type(r) as type, other, r.strength as strength, r.evidence as evidence
            LIMIT 10
            """
            
            relations_result = await session.run(relations_query, {"id": politician_id})
            relations_records = await relations_result.fetch_all()
            
            relationships = []
            for record in relations_records:
                relationships.append({
                    "type": record["type"],
                    "politician": record["other"],
                    "strength": record["strength"],
                    "evidence": record["evidence"]
                })
                
            politician["relationships"] = relationships
            
        return politician
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch politician: {str(e)}"
        )

@router.get(
    "/search",
    response_model=PoliticianListResponse,
    summary="Search politicians",
    description="Search for politicians by name or other attributes"
)
async def search_politicians(
    query: str = Query(..., min_length=2, description="Search query"),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page")
):
    """
    Search for politicians by name or other attributes.
    
    Args:
        query: Search query string
        session: Neo4j database session
        page: Page number
        limit: Items per page
        
    Returns:
        PoliticianListResponse: List of matching politicians
    """
    try:
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Build case-insensitive search query
        search_query = """
        MATCH (p:Politician)
        WHERE toLower(p.name) CONTAINS toLower($query)
           OR toLower(p.party) CONTAINS toLower($query)
           OR toLower(p.title) CONTAINS toLower($query)
        RETURN p
        ORDER BY p.name
        SKIP $skip
        LIMIT $limit
        """
        
        # Also get total count for pagination
        count_query = """
        MATCH (p:Politician)
        WHERE toLower(p.name) CONTAINS toLower($query)
           OR toLower(p.party) CONTAINS toLower($query)
           OR toLower(p.title) CONTAINS toLower($query)
        RETURN count(p) AS total
        """
        
        # Run queries
        result = await session.run(search_query, {
            "query": query,
            "skip": skip,
            "limit": limit
        })
        
        politicians = [record["p"] for record in await result.fetch_all()]
        
        count_result = await session.run(count_query, {"query": query})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/politicians/search?query={query}&page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/politicians/search?query={query}&page={page-1}&limit={limit}" if page > 1 else None
        
        return PoliticianListResponse(
            page=page,
            limit=limit,
            total=total,
            next_page=next_page,
            prev_page=prev_page,
            data=politicians
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get(
    "/{politician_id}/relationships",
    response_model=List[RelationshipResponse],
    summary="Get politician relationships",
    description="Get relationships between a politician and others"
)
async def get_politician_relationships(
    politician_id: str = Path(..., description="Politician ID"),
    session: AsyncSession = Depends(get_db_session),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum relationships to return")
):
    """
    Get relationships between a politician and others.
    
    Args:
        politician_id: Politician ID
        session: Neo4j database session
        relationship_type: Filter by specific relationship type
        limit: Maximum number of relationships to return
        
    Returns:
        List[RelationshipResponse]: List of political relationships
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
        
        # Build relationship query based on filters
        if relationship_type:
            relationship_query = f"""
            MATCH (p1:Politician {{id: $id}})-[r:{relationship_type}]-(p2:Politician)
            RETURN p1, p2, type(r) as type, r.strength as strength, r.evidence as evidence
            LIMIT $limit
            """
        else:
            relationship_query = """
            MATCH (p1:Politician {id: $id})-[r]-(p2:Politician)
            RETURN p1, p2, type(r) as type, r.strength as strength, r.evidence as evidence
            LIMIT $limit
            """
        
        # Execute query
        result = await session.run(relationship_query, {
            "id": politician_id,
            "limit": limit
        })
        
        records = await result.fetch_all()
        
        # Transform to response model
        relationships = []
        for record in records:
            p1 = record["p1"]
            p2 = record["p2"]
            
            relationships.append(RelationshipResponse(
                source_id=p1["id"],
                source_name=p1["name"],
                target_id=p2["id"],
                target_name=p2["name"],
                relationship_type=record["type"],
                strength=record["strength"],
                evidence=record["evidence"]
            ))
            
        return relationships
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch relationships: {str(e)}"
        )
