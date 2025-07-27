"""
Simplified pytest fixtures for API testing
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Create test app
test_app = FastAPI(
    title="FPAS API Test",
    description="Finnish Politician Analysis System API - Test Version",
    version="1.0.0"
)

# Mock services
class MockNeo4jService:
    async def get_politicians(self, **kwargs):
        return {
            "politicians": [
                {"id": "1", "name": "Test Politician", "party": "Test Party"}
            ],
            "total": 1
        }
        
    async def get_politician_by_id(self, politician_id, **kwargs):
        return {"id": politician_id, "name": "Test Politician", "party": "Test Party"}
        
    async def get_news_articles(self, **kwargs):
        return {
            "news_articles": [
                {"id": "1", "title": "Test News", "content": "Test content"}
            ],
            "total": 1
        }


class MockAnalyticsService:
    async def analyze_politician_network(self, **kwargs):
        return {
            "nodes": [{"id": "1", "name": "Test Politician"}],
            "edges": []
        }
        
    async def analyze_coalition_potential(self, **kwargs):
        return {
            "compatibility_matrix": {},
            "key_issues": ["Issue 1", "Issue 2"]
        }


@pytest.fixture
def test_client():
    """Test client for FastAPI application"""
    return TestClient(test_app)


@pytest.fixture
def mock_neo4j_service():
    """Mock Neo4j service"""
    return MockNeo4jService()


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service"""
    return MockAnalyticsService()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    return session
