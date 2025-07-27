"""
Async API endpoint tests for FPAS
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx

# Test app with async endpoints
app = FastAPI()

# Async politicians endpoint
@app.get("/async/politicians")
async def get_politicians_async():
    """Get politicians endpoint (async)"""
    return {
        "politicians": [
            {
                "id": "1",
                "name": "Test Politician",
                "party": "Test Party",
                "title": "MP",
                "position": "Chair"
            }
        ],
        "total": 1
    }

# Async politician detail endpoint
@app.get("/async/politicians/{politician_id}")
async def get_politician_async(politician_id: str):
    """Get politician by ID (async)"""
    return {
        "id": politician_id,
        "name": "Test Politician",
        "party": "Test Party",
        "title": "MP",
        "position": "Chair",
        "biography": "Test bio"
    }

# Async news by politician endpoint
@app.get("/async/politicians/{politician_id}/news")
async def get_politician_news_async(politician_id: str):
    """Get news by politician ID (async)"""
    return {
        "politician_id": politician_id,
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

# Async politician analysis endpoint
@app.get("/async/analysis/politician/{politician_id}")
async def analyze_politician_async(politician_id: str):
    """Analyze politician by ID (async)"""
    return {
        "politician_id": politician_id,
        "sentiment_score": 0.7,
        "key_topics": ["Economy", "Healthcare"],
        "recent_activity_score": 8.5
    }

# Async relationship network endpoint
@app.get("/async/analysis/network")
async def analyze_network_async(politician_ids: str):
    """Analyze politician network (async)"""
    # Parse comma-separated IDs
    ids = politician_ids.split(",")
    
    nodes = []
    edges = []
    
    # Create nodes for each politician
    for pid in ids:
        nodes.append({
            "id": pid,
            "name": f"Politician {pid}",
            "party": "Test Party"
        })
    
    # Create edges between politicians if more than one
    if len(ids) > 1:
        for i in range(len(ids)-1):
            edges.append({
                "source": ids[i],
                "target": ids[i+1],
                "type": "COLLEAGUES",
                "weight": 0.8
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "density": 0.5,
        "clusters": 1
    }


# Tests using pytest-asyncio
def test_get_politicians_async():
    """Test async politicians endpoint"""
    # Use FastAPI's TestClient
    client = TestClient(app)
    response = client.get("/async/politicians")
    assert response.status_code == 200
    data = response.json()
    assert "politicians" in data
    assert "total" in data
    assert len(data["politicians"]) > 0
    assert data["politicians"][0]["name"] == "Test Politician"


def test_get_politician_by_id_async():
    """Test async politician detail endpoint"""
    politician_id = "42"
    client = TestClient(app)
    response = client.get(f"/async/politicians/{politician_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == politician_id
    assert data["name"] == "Test Politician"
    assert "biography" in data


def test_get_politician_news_async():
    """Test async politician news endpoint"""
    politician_id = "42"
    client = TestClient(app)
    response = client.get(f"/async/politicians/{politician_id}/news")
    assert response.status_code == 200
    data = response.json()
    assert data["politician_id"] == politician_id
    assert "news_articles" in data
    assert "total" in data
    assert len(data["news_articles"]) > 0


def test_analyze_politician_async():
    """Test async politician analysis endpoint"""
    politician_id = "42"
    client = TestClient(app)
    response = client.get(f"/async/analysis/politician/{politician_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["politician_id"] == politician_id
    assert "sentiment_score" in data
    assert "key_topics" in data
    assert isinstance(data["key_topics"], list)


def test_analyze_network_async():
    """Test async network analysis endpoint"""
    politician_ids = "1,2,3"
    client = TestClient(app)
    response = client.get(f"/async/analysis/network?politician_ids={politician_ids}")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3  # Should match the number of IDs we provided
    assert len(data["edges"]) == 2  # Should be n-1 edges for a simple connected graph
