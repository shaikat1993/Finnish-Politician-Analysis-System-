"""
Document Processors for AI Pipeline
Transform raw data into LangChain-compatible documents.
"""

from .politician_processor import PoliticianProcessor
from .news_processor import NewsProcessor
from .relationship_extractor import RelationshipExtractor

__all__ = [
    'PoliticianProcessor',
    'NewsProcessor', 
    'RelationshipExtractor'
]
