import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "doctor-appointment-api"

def test_readiness_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "appointments_created_total" in text
    assert "concurrency_conflicts_prevented_total" in text
