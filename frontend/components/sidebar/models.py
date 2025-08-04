"""
Models for the sidebar component
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


"""
Models for the sidebar component (search-only, no province models)
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class FilterType(str, Enum):
    """Available filter types"""
    PARTY = "party"
    SECTOR = "sector"
    TIME_PERIOD = "time_period"

class Filter(BaseModel):
    """Base filter model"""
    type: FilterType = Field(..., description="Filter type")
    value: Any = Field(..., description="Filter value")
    label: str = Field(..., description="Human-readable label")

class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search term")
    filters: List[Filter] = Field(default_factory=list, description="Applied filters")

class SidebarState(BaseModel):
    """State of the sidebar component"""
    search_query: SearchQuery = Field(default_factory=SearchQuery)
    loading: bool = Field(default=False)
    error: Optional[str] = Field(None)

    class Config:
        arbitrary_types_allowed = True
