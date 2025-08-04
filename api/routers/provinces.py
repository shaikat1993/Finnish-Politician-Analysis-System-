"""
Provinces router for FPAS API
Provides endpoints for Finnish province data access
"""

import sys
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Dict, Optional
from neo4j import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import dependencies and models
from api.core.dependencies import get_db_session
from api.models.response import ApiResponse, ErrorResponse
from database.neo4j_integration import Neo4jConnectionManager
from data_collection.administrative.statistics_finland_collector import StatisticsFinlandCollector
from pydantic import BaseModel, Field

# Create logger instance
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/provinces",
    tags=["provinces"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# Province data models
from pydantic import BaseModel, Field

class ProvinceResponse(BaseModel):
    """Province information"""
    id: str
    name: str
    name_fi: str
    name_sv: Optional[str] = None
    population: int
    area_km2: float
    politician_count: int
    capital: str
    coordinates: dict = Field(..., description="Center coordinates {lat, lon}")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "uusimaa",
                "name": "Uusimaa",
                "name_fi": "Uusimaa",
                "name_sv": "Nyland",
                "population": 1700000,
                "area_km2": 9440.0,
                "politician_count": 45,
                "capital": "Helsinki",
                "coordinates": {"lat": 60.1699, "lon": 24.9384}
            }
        }

class ProvinceListResponse(BaseModel):
    """List of provinces"""
    data: List[ProvinceResponse]

class PoliticianResponse(BaseModel):
    """Politician information"""
    id: str
    name: str
    party: Optional[str] = None
    constituency: Optional[str] = None
    province: Optional[str] = None
    years_served: Optional[str] = None
    position: Optional[str] = None
    image_url: Optional[str] = Field(
        None, 
        description="URL to the politician's profile image"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "matti-vanhanen",
                "name": "Matti Vanhanen",
                "party": "Centre Party",
                "constituency": "Pirkanmaan vaalipiiri",
                "province": "pirkanmaa",
                "years_served": "2003-present",
                "position": "Member of Parliament"
            }
        }

class PoliticianListResponse(BaseModel):
    """List of politicians in a province"""
    province_id: str
    province_name: str
    total_politicians: int
    politicians: List[PoliticianResponse]

# Finnish provinces data service - NOW DYNAMIC!
class ProvinceDataService:
    """Service for managing province data with real politician counts from Neo4j and official Statistics Finland data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j_manager = Neo4jConnectionManager()
        self.stats_finland_collector = StatisticsFinlandCollector()
        
        # Constituency to Province mapping (Finnish electoral districts to regions)
        self.constituency_to_province = {
            # Helsinki area
            "Helsingin vaalipiiri": "uusimaa",
            "Uudenmaan vaalipiiri": "uusimaa",
            
            # Southwest Finland
            "Varsinais-Suomen vaalipiiri": "varsinais-suomi",
            "Satakunnan vaalipiiri": "satakunta",
            
            # Tampere area
            "Pirkanmaan vaalipiiri": "pirkanmaa",
            "Hämeen vaalipiiri": "kanta-hame",
            "Päijät-Hämeen vaalipiiri": "paijat-hame",
            
            # Central Finland
            "Keski-Suomen vaalipiiri": "keski-suomi",
            "Etelä-Savon vaalipiiri": "etela-savo",
            "Pohjois-Savon vaalipiiri": "pohjois-savo",
            "Pohjois-Karjalan vaalipiiri": "pohjois-karjala",
            
            # Northern Finland
            "Pohjois-Pohjanmaan vaalipiiri": "pohjois-pohjanmaa",
            "Kainuun vaalipiiri": "kainuu",
            "Lapin vaalipiiri": "lappi",
            
            # Eastern Finland
            "Etelä-Karjalan vaalipiiri": "etela-karjala",
            "Kymenlaakson vaalipiiri": "kymenlaakso",
            
            # Western Finland
            "Pohjanmaan vaalipiiri": "pohjanmaa",
            "Keski-Pohjanmaan vaalipiiri": "keski-pohjanmaa",
            "Etelä-Pohjanmaan vaalipiiri": "etela-pohjanmaa",
            
            # Åland
            "Ahvenanmaan vaalipiiri": "ahvenanmaa"
        }

    async def get_provinces_from_database(self) -> List[Dict]:
        """
        Get provinces from Neo4j database ONLY. No fallback to sample or Statistics Finland data for counts.
        """
        try:
            # Ensure Neo4j connection is initialized
            await self.neo4j_manager.initialize()
            
            # Try to get data from Neo4j database
            query = """
            MATCH (p:Province)
            RETURN p.province_id as id, p.name_fi as name, p.name_sv as name_sv, p.name_en as name_en,
                   p.population as population, p.area_km2 as area_km2, p.population_density as population_density,
                   p.capital as capital, p.coordinates as coordinates, p.is_active as is_active, p.last_updated as last_updated
            """
            results = await self.neo4j_manager.execute_query(query)
            if results:
                self.logger.info(f"✅ Retrieved {len(results)} provinces from Neo4j database")
                return [self._normalize_province_record(p) for p in results]
            else:
                self.logger.warning("No provinces found in database.")
                return []
        except Exception as e:
            self.logger.error(f"Database unavailable for province data: {str(e)}")
            return []

    def _normalize_province_record(self, province: dict) -> dict:
        # Ensure all required fields and fix coordinates
        coords = province.get('coordinates', {})
        if isinstance(coords, list) and len(coords) == 2:
            coords = {'lon': coords[0], 'lat': coords[1]}
        elif not isinstance(coords, dict):
            coords = {'lat': 0, 'lon': 0}
        return {
            'id': province.get('region_id', province.get('id', '')),
            'name': province.get('name_fi', province.get('name', '')),
            'name_fi': province.get('name_fi', province.get('name', '')),
            'name_sv': province.get('name_sv', ''),
            'population': province.get('population', 0),
            'area_km2': province.get('area_km2', 0),
            'politician_count': province.get('politician_count', 0),
            'capital': province.get('capital', ''),
            'coordinates': coords
        }

    async def get_politician_counts_by_province(self) -> Dict[str, int]:
        """
        Get politician counts by province from Neo4j with fallback to sample data
        """
        try:
            # Ensure Neo4j connection is initialized
            await self.neo4j_manager.initialize()
            
            # Use property-based schema to match our actual data storage
            query = """
            MATCH (p:Politician)
            WHERE p.constituency IS NOT NULL
            WITH p.constituency as constituency, count(p) as politician_count
            RETURN constituency, politician_count
            ORDER BY politician_count DESC
            """
            
            results = await self.neo4j_manager.execute_query(query)
            
            if results:
                politician_counts = {}
                for result in results:
                    constituency = result['constituency']
                    count = result['politician_count']
                    province_id = self._map_constituency_to_province_id(constituency)
                    if province_id:
                        politician_counts[province_id] = politician_counts.get(province_id, 0) + count
                        self.logger.debug(f"Mapped constituency '{constituency}' -> province '{province_id}': {count} politicians")
                    else:
                        self.logger.warning(f"Unmapped constituency '{constituency}' with {count} politicians! These politicians will not be counted.")
                
                self.logger.info(f"✅ Retrieved politician counts for {len(politician_counts)} provinces from database")
                return politician_counts
            else:
                self.logger.error("No politician data found in database. Cannot provide data.")
                raise HTTPException(status_code=503, detail="No politician data available in database.")
        except Exception as e:
            self.logger.error(f"Database unavailable for politician counts ({str(e)}). Cannot provide data.")
            raise HTTPException(status_code=503, detail=f"Database unavailable for politician counts: {str(e)}")

    def _map_constituency_to_province_id(self, constituency: str) -> str:
        """
        Map a constituency name to a province ID using simplified direct mapping
        """
        if not constituency:
            return None
            
        constituency_lower = constituency.lower()
        
        # Direct mapping for common cases
        if 'uusimaa' in constituency_lower or 'helsinki' in constituency_lower:
            return 'uusimaa'
        elif 'varsinais-suomi' in constituency_lower or 'turku' in constituency_lower:
            return 'varsinais-suomi'
        elif 'pirkanmaa' in constituency_lower or 'tampere' in constituency_lower:
            return 'pirkanmaa'
        elif 'satakunta' in constituency_lower:
            return 'satakunta'
        elif 'kanta-häme' in constituency_lower or 'kanta-hame' in constituency_lower:
            return 'kanta-hame'
        elif 'päijät-häme' in constituency_lower or 'paijat-hame' in constituency_lower:
            return 'paijat-hame'
        elif 'kymenlaakso' in constituency_lower:
            return 'kymenlaakso'
        elif 'etelä-karjala' in constituency_lower or 'etela-karjala' in constituency_lower:
            return 'etela-karjala'
        elif 'etelä-savo' in constituency_lower or 'etela-savo' in constituency_lower:
            return 'etela-savo'
        elif 'pohjois-savo' in constituency_lower:
            return 'pohjois-savo'
        elif 'pohjois-karjala' in constituency_lower:
            return 'pohjois-karjala'
        elif 'keski-suomi' in constituency_lower:
            return 'keski-suomi'
        elif 'etelä-pohjanmaa' in constituency_lower or 'etela-pohjanmaa' in constituency_lower:
            return 'etela-pohjanmaa'
        elif 'pohjanmaa' in constituency_lower and 'keski' not in constituency_lower and 'pohjois' not in constituency_lower:
            return 'pohjanmaa'
        elif 'keski-pohjanmaa' in constituency_lower:
            return 'keski-pohjanmaa'
        elif 'pohjois-pohjanmaa' in constituency_lower:
            return 'pohjois-pohjanmaa'
        elif 'kainuu' in constituency_lower:
            return 'kainuu'
        elif 'lappi' in constituency_lower or 'lapland' in constituency_lower:
            return 'lappi'
        elif 'ahvenanmaa' in constituency_lower or 'åland' in constituency_lower:
            return 'ahvenanmaa'
        else:
            # Fallback: try to normalize the constituency name as province ID
            normalized = constituency_lower.replace(' ', '-').replace('ä', 'a').replace('ö', 'o').replace('å', 'a')
            self.logger.debug(f"No direct mapping found for constituency '{constituency}', using normalized: '{normalized}'")
            return normalized

    async def get_provinces_with_live_data(self) -> List[Dict]:
        """Get all provinces with live politician counts - DYNAMIC DATA ONLY"""
        try:
            # Always get provinces from Neo4j
            provinces = await self.get_provinces_from_database()
            if not provinces:
                self.logger.warning("No province data in DB - cannot proceed")
                raise HTTPException(status_code=503, detail="No province data in database")

            # Always get live counts from Neo4j
            counts = await self.get_politician_counts_by_province()
            for province in provinces:
                province_id = province["id"]
                province["politician_count"] = counts.get(province_id, 0)
            return provinces
        except Exception as e:
            self.logger.error(f"Error getting provinces with live data: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Failed to get provinces with live data: {str(e)}")

    async def sync_provinces_to_database(self, provinces: List[Dict]):
        """Sync province data to Neo4j database"""
        try:
            for province in provinces:
                query = """
                MERGE (p:Province {province_id: $province_id})
                SET p.name_fi = $name_fi,
                    p.name_sv = $name_sv,
                    p.name_en = $name_en,
                    p.population = $population,
                    p.area_km2 = $area_km2,
                    p.capital = $capital,
                    p.coordinates = $coordinates,
                    p.source = 'statistics_finland',
                    p.is_active = true,
                    p.updated_at = datetime()
                ON CREATE SET p.created_at = datetime()
                """
                
                await self.neo4j_manager.execute_query(query, {
                    "province_id": province["id"],
                    "name_fi": province["name_fi"],
                    "name_sv": province["name_sv"],
                    "name_en": province.get("name_en", province["name_fi"]),
                    "population": province["population"],
                    "area_km2": province["area_km2"],
                    "capital": province["capital"],
                    "coordinates": province["coordinates"],
                    "last_updated": province["last_updated"]
                })
            
            self.logger.info(f"Successfully synced {len(provinces)} provinces to database")
            
        except Exception as e:
            self.logger.error(f"Error syncing provinces to database: {str(e)}")

# Initialize province data service
province_service = ProvinceDataService()

# Helper functions
async def _query_politicians_by_province(session: AsyncSession, province_id: str, limit: int) -> List[PoliticianResponse]:
    """
    Query Neo4j database for politicians in a specific province
    
    Args:
        session: Neo4j database session
        province_id: Province ID to query
        limit: Maximum number of politicians to return
        
    Returns:
        List of PoliticianResponse objects
    """
    try:
        # Simplified direct constituency matching - map province_id to likely constituency names
        constituency_patterns = []
        
        # Direct mapping for common cases
        if province_id.lower() == 'uusimaa':
            constituency_patterns = ['Uusimaa', 'uusimaa', 'Helsinki', 'Espoo', 'Vantaa']
        elif province_id.lower() == 'varsinais-suomi':
            constituency_patterns = ['Varsinais-Suomi', 'varsinais-suomi', 'Turku']
        else:
            # Fallback: try the province_id itself in various cases
            constituency_patterns = [province_id, province_id.lower(), province_id.capitalize()]
        
        # Query Neo4j for politicians in matching constituencies
        query = """
        MATCH (p:Politician)
        WHERE p.constituency IN $constituencies OR 
              toLower(p.constituency) = toLower($province_id)
        // Use direct image_url property from our working schema
        RETURN DISTINCT p.politician_id as id, 
               p.name as name, 
               p.current_party as party, 
               COALESCE(p.constituency, '') as constituency, 
               COALESCE(p.current_position, 'Member of Parliament') as position,
               COALESCE(p.is_active, true) as is_active,
               COALESCE(p.constituency, '') as province,
               p.image_url as image_url
        ORDER BY p.name
        LIMIT $limit
        """
        
        result = await session.run(query, constituencies=constituency_patterns, province_id=province_id, limit=limit)
        records = await result.data()
        
        politicians = []
        for record in records:
            politician = PoliticianResponse(
                id=record.get('id', ''),
                name=record.get('name', ''),
                party=record.get('party'),
                constituency=record.get('constituency'),
                province=province_id,
                years_served=record.get('years_served'),
                position=record.get('position', 'Member of Parliament'),
                image_url=record.get('image_url')
            )
            politicians.append(politician)
        
        logging.info(f"Found {len(politicians)} politicians for province {province_id}")
        return politicians
        
    except Exception as e:
        logging.error(f"Error querying politicians for province {province_id}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to query politicians for province {province_id}: {str(e)}")

def _get_sample_politicians_for_province(province_id: str, limit: int) -> List[PoliticianResponse]:
    """
    Provide sample politician data when database is unavailable
    
    Args:
        province_id: Province ID
        limit: Maximum politicians to return
        
    Returns:
        List of sample PoliticianResponse objects
    """
    # Sample politician data for demonstration
    sample_politicians = {
        "uusimaa": [
            {"id": "alexander-stubb", "name": "Alexander Stubb", "party": "National Coalition Party", "constituency": "Uudenmaan vaalipiiri"},
            {"id": "sanna-marin", "name": "Sanna Marin", "party": "Social Democratic Party", "constituency": "Uudenmaan vaalipiiri"},
            {"id": "petteri-orpo", "name": "Petteri Orpo", "party": "National Coalition Party", "constituency": "Uudenmaan vaalipiiri"},
        ],
        "pirkanmaa": [
            {"id": "matti-vanhanen", "name": "Matti Vanhanen", "party": "Centre Party", "constituency": "Pirkanmaan vaalipiiri"},
            {"id": "elina-lepomaki", "name": "Elina Lepomäki", "party": "National Coalition Party", "constituency": "Pirkanmaan vaalipiiri"},
            {"id": "ville-skinnari", "name": "Ville Skinnari", "party": "Social Democratic Party", "constituency": "Pirkanmaan vaalipiiri"},
        ],
        "varsinais-suomi": [
            {"id": "paavo-arhinmaki", "name": "Paavo Arhinmäki", "party": "Left Alliance", "constituency": "Varsinais-Suomen vaalipiiri"},
            {"id": "sofia-vikman", "name": "Sofia Vikman", "party": "National Coalition Party", "constituency": "Varsinais-Suomen vaalipiiri"},
        ],
        "lappi": [
            {"id": "markus-lohi", "name": "Markus Lohi", "party": "Centre Party", "constituency": "Lapin vaalipiiri"},
            {"id": "anne-kalmari", "name": "Anne Kalmari", "party": "Centre Party", "constituency": "Lapin vaalipiiri"},
        ]
    }
    
    province_politicians = sample_politicians.get(province_id, [])
    limited_politicians = province_politicians[:limit]
    
    return [
        PoliticianResponse(
            id=pol["id"],
            name=pol["name"],
            party=pol["party"],
            constituency=pol["constituency"],
            province=province_id,
            years_served="2019-present",
            position="Member of Parliament"
        )
        for pol in limited_politicians
    ]

@router.get(
    "/",
    response_model=ProvinceListResponse,
    summary="List Finnish provinces",
    description="Get a list of all Finnish provinces with politician counts and geographic data"
)
async def list_provinces():
    """
    Get a list of all Finnish provinces with politician counts and geographic data.
    
    Returns:
        ProvinceListResponse: List of provinces with metadata
    """
    try:
        logger.info("🔍 DEBUG: Starting provinces API endpoint")
        
        # Get provinces with live data
        logger.info("🔍 DEBUG: Calling get_provinces_with_live_data()")
        provinces = await province_service.get_provinces_with_live_data()
        
        if not provinces:
            logger.error("🔍 DEBUG: No provinces returned from get_provinces_with_live_data()")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not retrieve province data"
            )
            
        logger.info(f"🔍 DEBUG: Got {len(provinces)} provinces from get_provinces_with_live_data()")
        
        # Log all provinces and their politician counts for debugging
        for i, p in enumerate(provinces):
            logger.info(f"🔍 DEBUG: Province {i+1}: ID='{p['id']}', Name='{p['name']}', Politicians={p.get('politician_count', 'N/A')}")
        
        # Create response object
        logger.info("🔍 DEBUG: Creating ProvinceListResponse")
        response_data = []
        for province in provinces:
            try:
                response_data.append(ProvinceResponse(**province))
            except Exception as e:
                logger.error(f"🔍 ERROR: Failed to create ProvinceResponse for {province.get('id', 'unknown')}: {str(e)}")
                logger.error(f"🔍 Province data: {province}")
                raise
                
        response = ProvinceListResponse(data=response_data)
        logger.info("🔍 DEBUG: Successfully created API response")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 ERROR: Exception in list_provinces: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch provinces: {str(e)}"
        )

@router.get(
    "/{province_id}",
    response_model=ProvinceResponse,
    summary="Get province details",
    description="Get detailed information about a specific province"
)
async def get_province(
    province_id: str = Path(..., description="Province ID")
):
    """
    Get detailed information about a specific province.
    
    Args:
        province_id: Province ID
        
    Returns:
        ProvinceResponse: Province details
    """
    try:
        provinces = await province_service.get_provinces_with_live_data()
        province_data = next((p for p in provinces if p["id"] == province_id), None)
        if not province_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Province '{province_id}' not found"
            )
        
        return ProvinceResponse(**province_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch province: {str(e)}"
        )

@router.get(
    "/{province_id}/politicians",
    response_model=PoliticianListResponse,
    summary="Get politicians by province",
    description="Get politicians from a specific province with detailed information"
)
async def get_province_politicians(
    province_id: str = Path(..., description="Province ID"),
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200, description="Maximum politicians to return")
):
    """
    Get politicians from a specific province.
    
    Args:
        province_id: Province ID
        session: Neo4j database session
        limit: Maximum politicians to return
        
    Returns:
        PoliticianListResponse: List of politicians from the province
    """
    try:
        # Check if province exists
        provinces = await province_service.get_provinces_with_live_data()
        province_data = next((p for p in provinces if p["id"] == province_id), None)
        if not province_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Province '{province_id}' not found"
            )
        
        # Query Neo4j for politicians in this province
        politicians = await _query_politicians_by_province(session, province_id, limit)
        
        return PoliticianListResponse(
            province_id=province_id,
            province_name=province_data["name"],
            total_politicians=len(politicians),
            politicians=politicians
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching politicians for province {province_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch province politicians: {str(e)}"
        )

@router.post(
    "/sync",
    summary="Sync province data",
    description="Manually sync province data from Statistics Finland to database"
)
async def sync_province_data():
    """
    Manually trigger sync of province data from Statistics Finland to Neo4j database.
    
    Returns:
        Sync status and results
    """
    try:
        # Fetch fresh data from Statistics Finland
        provinces = await province_service.get_provinces_from_statistics_finland()
        
        if not provinces:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch data from Statistics Finland"
            )
        
        # Sync to database
        await province_service.sync_provinces_to_database(provinces)
        
        return {
            "status": "success",
            "message": f"Successfully synced {len(provinces)} provinces from Statistics Finland",
            "provinces_synced": len(provinces),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync province data: {str(e)}"
        )
