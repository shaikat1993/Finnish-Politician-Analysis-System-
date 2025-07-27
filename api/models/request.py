"""
Request models for FPAS API
Pydantic models for API request validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# Pagination parameters
class PaginationParams(BaseModel):
    """Common pagination parameters"""
    page: int = Field(1, ge=1, description="Page number, starting from 1")
    limit: int = Field(100, ge=1, le=500, description="Items per page, max 500")

# Search parameters
class SearchParams(BaseModel):
    """Common search parameters"""
    query: str = Field(..., min_length=1, description="Search query string")
    
# Politician-related requests
class PoliticianSearch(PaginationParams, SearchParams):
    """Politician search parameters"""
    party: Optional[str] = Field(None, description="Filter by political party")
    active_only: bool = Field(False, description="Show only active politicians")

class PoliticianCreate(BaseModel):
    """Create new politician record"""
    name: str
    party: Optional[str] = None
    title: Optional[str] = None
    image_url: Optional[str] = None
    external_ids: Optional[Dict[str, str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Sanna Marin",
                "party": "SDP",
                "title": "Former Prime Minister",
                "image_url": "https://example.com/sanna_marin.jpg",
                "external_ids": {
                    "eduskunta_id": "1366",
                    "twitter": "@MarinSanna"
                }
            }
        }

class PoliticianUpdate(BaseModel):
    """Update existing politician"""
    name: Optional[str] = None
    party: Optional[str] = None
    title: Optional[str] = None
    image_url: Optional[str] = None
    external_ids: Optional[Dict[str, str]] = None

# News-related requests
class NewsSearch(PaginationParams, SearchParams):
    """News search parameters"""
    source: Optional[str] = Field(None, description="Filter by news source")
    politician_id: Optional[str] = Field(None, description="Filter by politician")
    start_date: Optional[datetime] = Field(None, description="Filter by date range start")
    end_date: Optional[datetime] = Field(None, description="Filter by date range end")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment (positive/negative/neutral)")

# Analysis requests
class RelationshipAnalysisRequest(BaseModel):
    """Request for relationship analysis"""
    politician_ids: List[str] = Field(..., min_items=1, max_items=10, 
                                     description="IDs of politicians to analyze")
    depth: int = Field(2, ge=1, le=3, description="Relationship depth")
    include_evidence: bool = Field(False, description="Include evidence for relationships")
    
    class Config:
        schema_extra = {
            "example": {
                "politician_ids": ["politician-123", "politician-456"],
                "depth": 2,
                "include_evidence": True
            }
        }

class CoalitionAnalysisRequest(BaseModel):
    """Request for coalition analysis"""
    party_ids: List[str] = Field(..., min_items=2, max_items=8, 
                              description="IDs of parties to analyze for coalition potential")
    include_historical: bool = Field(True, description="Include historical data in analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "party_ids": ["party-sdp", "party-kok", "party-kesk"],
                "include_historical": True
            }
        }

class CustomAnalysisRequest(BaseModel):
    """Request for custom AI analysis"""
    query: str = Field(..., min_length=10, max_length=500, 
                     description="Natural language query for analysis")
    context_ids: Optional[List[str]] = Field(None, description="IDs of entities to include as context")
    detailed_response: bool = Field(False, description="Request detailed analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Analyze the potential impact of recent economic policies on the next election",
                "context_ids": ["party-sdp", "party-kok"],
                "detailed_response": True
            }
        }

# Data collection requests
class CollectionRequest(BaseModel):
    """Request for data collection"""
    sources: Optional[List[str]] = Field(None, description="Specific sources to collect from")
    limit: int = Field(50, ge=1, le=500, description="Maximum items to collect")
    refresh_cache: bool = Field(False, description="Force refresh cache")
    
    class Config:
        schema_extra = {
            "example": {
                "sources": ["eduskunta", "wikipedia"],
                "limit": 50,
                "refresh_cache": True
            }
        }
