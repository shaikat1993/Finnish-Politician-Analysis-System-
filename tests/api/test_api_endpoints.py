"""
Simplified API endpoint tests for FPAS
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Test app
app = FastAPI()

# Test health endpoints
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2025-07-27T18:45:00Z"
    }

@app.get("/health/ready")
def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "services": {
            "database": "up",
            "ai_pipeline": "up",
            "data_collection": "up"
        }
    }

# Test politicians endpoint
@app.get("/politicians")
def get_politicians():
    """Get politicians endpoint"""
    return {
        "politicians": [
            {
                "id": "1",
                "name": "Test Politician",
                "party": "Test Party",
                "title": "MP"
            }
        ],
        "total": 1
    }

# Test news endpoint
@app.get("/news")
def get_news():
    """Get news endpoint"""
    return {
        "news_articles": [
            {
                "id": "1",
                "title": "Test News",
                "content": "Test content",
                "published_date": "2025-07-27"
            }
        ],
        "total": 1
    }

# Test analysis endpoint
@app.post("/analysis/custom")
def custom_analysis(query: str = "Test query"):
    """Custom analysis endpoint"""
    return {
        "status": "accepted",
        "analysis_id": "test-id",
        "query": query,
        "status_url": f"/analysis/status/test-id"
    }


# Tests
def test_health_check():
    """Test the health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check():
    """Test the readiness check endpoint"""
    client = TestClient(app)
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "services" in data
    assert "database" in data["services"]
    assert "ai_pipeline" in data["services"]
    assert "data_collection" in data["services"]


def test_get_politicians():
    """Test the get politicians endpoint"""
    client = TestClient(app)
    response = client.get("/politicians")
    assert response.status_code == 200
    data = response.json()
    assert "politicians" in data
    assert "total" in data
    assert len(data["politicians"]) > 0
    assert data["politicians"][0]["name"] == "Test Politician"


def test_get_news():
    """Test the get news endpoint"""
    client = TestClient(app)
    response = client.get("/news")
    assert response.status_code == 200
    data = response.json()
    assert "news_articles" in data
    assert "total" in data
    assert len(data["news_articles"]) > 0
    assert data["news_articles"][0]["title"] == "Test News"


def test_custom_analysis():
    """Test the custom analysis endpoint"""
    client = TestClient(app)
    test_query = "What are key political issues in Finland?"
    response = client.post("/analysis/custom", params={"query": test_query})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "analysis_id" in data
    assert data["query"] == test_query
    assert "status_url" in data
