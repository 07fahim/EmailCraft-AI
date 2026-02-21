"""
API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200


# Add more API tests as needed
