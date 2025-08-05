import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# Replace with a real politician ID present in your test database
TEST_POLITICIAN_ID = "petteri-orpo"


def test_politician_details_success():
    response = client.get(f"/api/v1/politicians/{TEST_POLITICIAN_ID}/details")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data and data["id"] == TEST_POLITICIAN_ID
    assert "name" in data and data["name"]
    assert "news" in data
    assert "wikipedia" in data
    assert "links" in data


def test_politician_details_no_news():
    # Use a politician with no news if possible
    response = client.get(f"/api/v1/politicians/{TEST_POLITICIAN_ID}/details")
    assert response.status_code == 200
    data = response.json()
    assert "news" in data


def test_politician_details_not_found():
    response = client.get("/api/v1/politicians/nonexistent-id/details")
    assert response.status_code == 404
