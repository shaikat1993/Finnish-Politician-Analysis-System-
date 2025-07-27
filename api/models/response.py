"""
Response models for FPAS API
Pydantic models for API responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# Base response models
class ApiResponse(BaseModel):
    """Base API response"""
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(ApiResponse):
    """Error response"""
    status: str = "error"
    error_code: str
    detail: str
    
class PaginatedResponse(ApiResponse):
    """Base paginated response"""
    page: int
    limit: int
    total: int
    next_page: Optional[str] = None
    prev_page: Optional[str] = None

# Entity models
class PoliticianBase(BaseModel):
    """Base politician information"""
    id: str
    name: str
    party: Optional[str] = None
    title: Optional[str] = None

class PoliticianResponse(PoliticianBase):
    """Full politician response model"""
    image_url: Optional[str] = None
    election_history: Optional[List[Dict[str, Any]]] = None
    latest_news: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "politician-123",
                "name": "Sanna Marin",
                "party": "SDP",
                "title": "Former Prime Minister",
                "image_url": "https://example.com/sanna_marin.jpg",
                "election_history": [
                    {"year": 2019, "votes": 19088, "district": "Pirkanmaa"}
                ],
                "latest_news": [
                    {"title": "Policy statement", "date": "2023-05-20", "source": "YLE"}
                ]
            }
        }

class PoliticianListResponse(PaginatedResponse):
    """List of politicians with pagination"""
    data: List[PoliticianBase]

class PartyResponse(BaseModel):
    """Political party information"""
    id: str
    name: str
    abbreviation: Optional[str] = None
    logo_url: Optional[str] = None
    leader: Optional[PoliticianBase] = None
    member_count: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "party-sdp",
                "name": "Social Democratic Party of Finland",
                "abbreviation": "SDP",
                "logo_url": "https://example.com/sdp_logo.png",
                "leader": {
                    "id": "politician-456",
                    "name": "Antti Lindtman",
                    "title": "Party Chair"
                },
                "member_count": 40000
            }
        }

class NewsArticleResponse(BaseModel):
    """News article information"""
    id: str
    title: str
    source: str
    published_date: datetime
    url: str
    summary: Optional[str] = None
    sentiment: Optional[float] = None
    politicians: Optional[List[PoliticianBase]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "news-789",
                "title": "Government announces budget proposal",
                "source": "Helsingin Sanomat",
                "published_date": "2023-09-05T12:30:00",
                "url": "https://hs.fi/article-123",
                "summary": "The Finnish government revealed their budget proposal for 2024...",
                "sentiment": 0.2,
                "politicians": [
                    {"id": "politician-789", "name": "Petteri Orpo", "title": "Prime Minister"}
                ]
            }
        }

class NewsListResponse(PaginatedResponse):
    """List of news articles with pagination"""
    data: List[NewsArticleResponse]

class RelationshipResponse(BaseModel):
    """Political relationship information"""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    relationship_type: str
    strength: Optional[float] = None
    evidence: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "source_id": "politician-123",
                "source_name": "Sanna Marin",
                "target_id": "politician-456",
                "target_name": "Antti Lindtman",
                "relationship_type": "COLLEAGUE",
                "strength": 0.85,
                "evidence": ["Worked together in SDP leadership", "Joint policy statements"]
            }
        }

class AnalysisResponse(ApiResponse):
    """AI analysis response"""
    query: str
    result: Dict[str, Any]
    processing_time: float
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-09-05T12:30:00",
                "query": "Analyze coalition possibilities between SDP and Kokoomus",
                "result": {
                    "compatibility": "moderate",
                    "common_issues": ["Economic reform", "EU policy"],
                    "disagreements": ["Healthcare privatization", "Tax policy"]
                },
                "processing_time": 1.23
            }
        }

class HealthCheckResponse(ApiResponse):
    """System health check response"""
    components: Dict[str, Dict[str, Any]]
    overall_status: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "timestamp": "2023-09-05T12:30:00",
                "components": {
                    "database": {
                        "status": "healthy",
                        "latency_ms": 5,
                        "connections": 3
                    },
                    "ai_pipeline": {
                        "status": "healthy",
                        "models_loaded": True
                    },
                    "data_collection": {
                        "status": "degraded",
                        "message": "Some API sources unavailable"
                    }
                },
                "overall_status": "degraded"
            }
        }
