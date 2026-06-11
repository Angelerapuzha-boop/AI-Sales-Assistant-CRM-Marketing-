"""Basic API tests - run with: pytest tests/ -v"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Sales" in response.json()["message"]


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_info():
    response = client.get("/api/info")
    assert response.status_code == 200
    assert "features" in response.json()


def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200


def test_login_invalid():
    response = client.post("/api/auth/login", json={"email": "invalid@test.com", "password": "wrong"})
    assert response.status_code == 401
