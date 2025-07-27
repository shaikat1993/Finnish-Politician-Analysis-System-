"""
PyTest Configuration for FPAS
Senior-level test configuration with fixtures and setup
"""

import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def neo4j_manager():
    """Provide Neo4j connection manager for tests"""
    try:
        from database import get_neo4j_manager
        manager = await get_neo4j_manager()
        yield manager
        await manager.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")

@pytest.fixture(scope="function")
async def clean_test_data(neo4j_manager):
    """Clean test data before and after each test"""
    # Clean before test
    try:
        await neo4j_manager.execute_query(
            "MATCH (n:TestPolitician) DETACH DELETE n"
        )
        await neo4j_manager.execute_query(
            "MATCH (n:TestParty) DETACH DELETE n"
        )
    except:
        pass  # Ignore cleanup errors
    
    yield
    
    # Clean after test
    try:
        await neo4j_manager.execute_query(
            "MATCH (n:TestPolitician) DETACH DELETE n"
        )
        await neo4j_manager.execute_query(
            "MATCH (n:TestParty) DETACH DELETE n"
        )
    except:
        pass  # Ignore cleanup errors

@pytest.fixture
def sample_politician_data():
    """Provide sample politician data for testing"""
    return {
        "politician_id": "test_001",
        "name": "Test Politician",
        "party": "Test Party",
        "constituency": "Test Constituency",
        "term_start": "2023-01-01",
        "role": "MP",
        "email": "test@example.com"
    }

@pytest.fixture
def sample_news_data():
    """Provide sample news data for testing"""
    return {
        "article_id": "test_news_001",
        "title": "Test Political News",
        "content": "This is test political news content",
        "source": "Test Source",
        "published_date": "2023-01-01",
        "politicians_mentioned": ["test_001"]
    }

@pytest.fixture
def mock_api_responses():
    """Provide mock API responses for testing"""
    return {
        "eduskunta_politicians": [
            {
                "id": "test_001",
                "name": "Test MP",
                "party": "Test Party",
                "constituency": "Helsinki"
            }
        ],
        "yle_news": [
            {
                "id": "news_001",
                "title": "Test News",
                "content": "Test content",
                "published": "2023-01-01"
            }
        ]
    }
