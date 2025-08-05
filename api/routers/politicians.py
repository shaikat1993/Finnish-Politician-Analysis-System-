"""
Politicians router for FPAS API
Provides endpoints for politician data access and management
"""

import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional
from fastapi.responses import JSONResponse
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

# Place these endpoints BEFORE any dynamic path endpoints like /{politician_id}
@router.get(
    "/parties",
    response_model=List[str],
    summary="Get all unique political parties",
    description="Returns a list of all unique political party names in the database, sorted alphabetically."
)
async def get_all_parties(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Returns all unique political party names from Neo4j.
    """
    try:
        query = """
        MATCH (p:Politician)
        WHERE p.current_party IS NOT NULL AND p.current_party <> ''
        RETURN DISTINCT p.current_party AS party
        ORDER BY party ASC
        """
        result = await session.run(query)
        parties = []
        async for record in result:
            if record["party"]:
                parties.append(record["party"])
        return parties
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch parties: {str(e)}"
        )


@router.get(
    "/",
    response_model=PoliticianListResponse,
    summary="Get all politicians (paginated)",
    description="Returns a paginated list of all politicians"
)
async def list_politicians(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(48, ge=1, le=500, description="Items per page"),
    party: Optional[str] = Query(None, description="Filter by political party"),
    active_only: bool = Query(False, description="Show only active politicians")
):
    skip = (page - 1) * limit
    query = """
    MATCH (p:Politician)
    WHERE ($party IS NULL OR p.current_party = $party)
      AND ($active_only = False OR p.is_active = True)
    RETURN p.politician_id as id,
           p.name as name,
           p.current_party as party,
           p.constituency as constituency,
           p.current_position as position,
           p.is_active as is_active,
           p.image_url as image_url
    ORDER BY p.name
    SKIP $skip
    LIMIT $limit
    """
    count_query = """
    MATCH (p:Politician)
    WHERE ($party IS NULL OR p.current_party = $party)
      AND ($active_only = False OR p.is_active = True)
    RETURN count(p) AS total
    """
    try:
        result = await session.run(query, {
            "party": party,
            "active_only": active_only,
            "skip": skip,
            "limit": limit
        })
        records = []
        async for record in result:
            records.append(record)
        politicians = []
        for record in records:
            politicians.append({
                "id": record.get("id"),
                "name": record.get("name"),
                "party": record.get("party"),
                "constituency": record.get("constituency"),
                "position": record.get("position"),
                "is_active": record.get("is_active"),
                "image_url": record.get("image_url")
            })
        count_result = await session.run(count_query, {
            "party": party,
            "active_only": active_only
        })
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        next_page = f"/politicians/?page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/politicians/?page={page-1}&limit={limit}" if page > 1 else None
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
    "/count",
    response_model=int,
    summary="Get total number of politicians",
    description="Returns the total number of politicians in the database"
)
async def get_total_politician_count(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Returns the total count of politicians in the database.
    """
    try:
        count_query = """
        MATCH (p:Politician)
        RETURN count(p) AS total
        """
        result = await session.run(count_query)
        record = await result.single()
        total = record["total"] if record else 0
        return total
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch total politician count: {str(e)}")

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
    
    # Build Cypher query with parameters - fix field names to match database schema
    query = """
    MATCH (p:Politician)
    WHERE 
        (p.current_party IS NOT NULL)
    RETURN p.politician_id as id,
           p.name as name,
           p.current_party as party,
           p.constituency as constituency,
           p.current_position as position,
           p.is_active as is_active,
           p.image_url as image_url
    ORDER BY p.name
    SKIP $skip
    LIMIT $limit
    """
    
    # Also get total count for pagination
    count_query = """
    MATCH (p:Politician)
    WHERE 
        (p.current_party IS NOT NULL)
    RETURN count(p) AS total
    """
    
    try:
        # Run queries
        result = await session.run(query, {
            "skip": skip,
            "limit": limit
        })
        
        # Use correct Neo4j async API
        records = []
        async for record in result:
            records.append(record)
        
        # Process politician records into proper format
        politicians = []
        for record in records:
            politician = {
                "id": record.get("id"),
                "name": record.get("name"),
                "party": record.get("party"),
                "constituency": record.get("constituency"),
                "position": record.get("position"),
                "years_served": record.get("years_served"),
                "image_url": record.get("image_url")
            }
            politicians.append(politician)
        
        count_result = await session.run(count_query)
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
    "/province/{province_id}",
    response_model=PoliticianListResponse,
    summary="Get politicians by province",
    description="Get politicians from a specific Finnish province/region"
)
async def get_politicians_by_province(
    province_id: str = Path(..., description="Province ID (e.g., 'uusimaa', 'varsinais-suomi')"),
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    active_only: bool = Query(False, description="Show only active politicians")
):
    """
    Get politicians from a specific Finnish province/region.
    
    Args:
        province_id: Province identifier (e.g., 'uusimaa', 'varsinais-suomi')
        session: Neo4j database session
        page: Page number (1-indexed)
        limit: Number of items per page
        active_only: Show only active politicians
        
    Returns:
        PoliticianListResponse: List of politicians from the province
    """
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Build Cypher query with province filter
    query = """
    MATCH (p:Politician)
    WHERE 
        p.province = $province_id
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
        p.province = $province_id
        AND ($active_only = False OR p.active = True)
    RETURN count(p) AS total
    """
    
    try:
        # Run queries
        result = await session.run(query, {
            "province_id": province_id,
            "active_only": active_only,
            "skip": skip,
            "limit": limit
        })
        
        # Use correct Neo4j async API
        records = []
        async for record in result:
            records.append(record)
        politicians = [record["p"] for record in records]
        
        count_result = await session.run(count_query, {
            "province_id": province_id,
            "active_only": active_only
        })
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        # Build response with pagination
        next_page = f"/politicians/province/{province_id}?page={page+1}&limit={limit}" if skip + limit < total else None
        prev_page = f"/politicians/province/{province_id}?page={page-1}&limit={limit}" if page > 1 else None
            
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
            detail=f"Failed to fetch politicians for province {province_id}: {str(e)}"
        )

@router.get(
    "/search",
    response_model=PoliticianListResponse,
    summary="Search politicians",
    description="Search for politicians by name or other attributes"
)
async def search_politicians(
    query: str = Query('', min_length=0, description="Search query (optional)"),
    party: str = Query(None, description="Party name to filter by (optional)"),
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
        
        # Build dynamic Cypher WHERE clause
        where_clauses = []
        params = {"skip": skip, "limit": limit}
        # Always provide both parameters to avoid Neo4j ParameterMissing error
        params["query"] = query.strip() if query else ""
        params["party"] = party if party else ""
        if query and len(query.strip()) >= 2:
            where_clauses.append("(toLower(p.name) CONTAINS toLower($query) OR toLower(p.current_party) CONTAINS toLower($query) OR toLower(p.current_position) CONTAINS toLower($query))")
        if party:
            where_clauses.append("toLower(p.current_party) = toLower($party)")
        cypher_where = ' AND '.join(where_clauses) if where_clauses else '1=1'
        search_query = f"""
            MATCH (p:Politician)
            WHERE {cypher_where}
            RETURN p
            ORDER BY p.name
            SKIP $skip
            LIMIT $limit
        """
        count_query = f"""
            MATCH (p:Politician)
            WHERE {cypher_where}
            RETURN count(p) AS total
        """
        # Run queries
        result = await session.run(search_query, params)
        
        records = []
        async for record in result:
            records.append(record)
        politicians = []
        for record in records:
            p = record["p"]
            politicians.append({
                "id": p.get("id") or p.get("politician_id") or "",
                "name": p.get("name", ""),
                "party": p.get("party") or p.get("current_party") or "",
                "title": p.get("title") or p.get("current_position") or "",
                "province": p.get("province", ""),
                "constituency": p.get("constituency", ""),
                "position": p.get("position") or p.get("current_position") or "",
                "years_served": p.get("years_served", ""),
                "image_url": p.get("image_url", ""),
                "bio": p.get("bio", "")
            })
        
        count_result = await session.run(count_query, {"query": params["query"], "party": params["party"]})
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
        # Fetch politician by ID
        query = """
        MATCH (p:Politician)
        WHERE p.id = $id OR p.politician_id = $id
        RETURN p
        """
        result = await session.run(query, {"id": politician_id})
        record = await result.single()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Politician with ID {politician_id} not found"
            )
        p = record["p"]
        politician = {
            "id": p.get("id") or p.get("politician_id") or "",
            "name": p.get("name", ""),
            "party": p.get("party") or p.get("current_party") or "",
            "title": p.get("title") or p.get("current_position") or "",
            "province": p.get("province", ""),
            "constituency": p.get("constituency", ""),
            "position": p.get("position") or p.get("current_position") or "",
            "years_served": p.get("years_served", ""),
            "image_url": p.get("image_url", ""),
            "bio": p.get("bio", "")
        }
        # Optionally fetch news and relationships if requested (add logic here if needed)
        return politician
        
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
        result = await session.run(relationship_query, {
            "id": politician_id,
            "limit": limit
        })
        records = []
        async for record in result:
            records.append(record)
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

# --- Unified Politician Details Endpoint ---
from data_collection.secondary.wikipedia_collector import WikipediaCollector
from api.routers.news import get_news_by_politician
import logging

@router.get(
    "/{politician_id}/details",
    summary="Get unified details for a politician",
    description="Aggregates core info, news, Wikipedia, and links for a politician. Always returns as much as possible.",
)
async def get_politician_details(
    politician_id: str = Path(..., description="Politician ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Unified endpoint for politician details: core info, news, Wikipedia, and links.
    """
    result = {}
    errors = []
    # 1. Core info from Neo4j
    try:
        core_query = "MATCH (p:Politician {id: $id}) RETURN p"
        core_result = await session.run(core_query, {"id": politician_id})
        record = await core_result.single()
        if not record:
            raise HTTPException(status_code=404, detail=f"Politician with ID {politician_id} not found")
        p = record["p"]
        result.update({
            "id": p.get("id") or p.get("politician_id") or "",
            "name": p.get("name", ""),
            "party": p.get("party") or p.get("current_party") or "",
            "title": p.get("title") or p.get("current_position") or "",
            "province": p.get("province", ""),
            "constituency": p.get("constituency", ""),
            "position": p.get("position") or p.get("current_position") or "",
            "years_served": p.get("years_served", ""),
            "image_url": p.get("image_url", ""),
            "bio": p.get("bio", "")
        })
    except Exception as e:
        logging.error(f"Failed to fetch core info: {str(e)}")
        errors.append(f"core_info: {str(e)}")
    # 2. News articles
    try:
        from api.routers.news import get_news_by_politician
        news_response = await get_news_by_politician(politician_id, session, 1, 5)
        news_data = getattr(news_response, "data", []) if hasattr(news_response, "data") else news_response.get("data", [])
        # If news is missing, trigger unified enrichment
        if not news_data:
            from data_collection.news.unified_news_enricher import UnifiedNewsEnricher
            from database.neo4j_integration import get_neo4j_writer
            # Get core info for name
            politician_name = result.get("name", "")
            neo4j_writer = await get_neo4j_writer()
            enricher = UnifiedNewsEnricher(neo4j_writer=neo4j_writer)
            enriched_news = await enricher.enrich_and_store_politician_news(politician_id, politician_name)
            result["news"] = enriched_news
        else:
            result["news"] = news_data
    except Exception as e:
        logging.error(f"Failed to fetch news: {str(e)}")
        result["news"] = []
        errors.append(f"news: {str(e)}")
    # 3. Wikipedia summary
    try:
        # Try to get Wikipedia fields from Neo4j first
        wiki_fields = {k: result.get(k) for k in ["wikipedia_url", "wikipedia_summary", "wikipedia_image_url"]}
        if not all(wiki_fields.values()):
            # If any field missing, enrich and persist
            from data_collection.secondary.wikipedia_enrichment_util import enrich_and_store_wikipedia
            wiki_info = await enrich_and_store_wikipedia(result.get("id"), result.get("name", ""))
            if wiki_info:
                result["wikipedia"] = wiki_info
                # Also update result for serving links, etc.
                result["wikipedia_url"] = wiki_info["url"]
                result["wikipedia_summary"] = wiki_info["summary"]
                result["wikipedia_image_url"] = wiki_info["image_url"]
            else:
                result["wikipedia"] = {}
        else:
            result["wikipedia"] = {
                "url": wiki_fields["wikipedia_url"],
                "summary": wiki_fields["wikipedia_summary"],
                "image_url": wiki_fields["wikipedia_image_url"]
            }
    except Exception as e:
        logging.error(f"Failed to fetch Wikipedia: {str(e)}")
        result["wikipedia"] = {}
        errors.append(f"wikipedia: {str(e)}")
    # 4. Related links (optional, can be extended)
    links = []
    if result.get("wikipedia", {}).get("url"):
        links.append({"label": "Wikipedia", "url": result["wikipedia"]["url"]})
    if result.get("bio"):
        links.append({"label": "Biography", "url": result.get("bio")})
    result["links"] = links
    if errors:
        result["errors"] = errors
    return result
