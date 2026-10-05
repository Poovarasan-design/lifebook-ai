import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_and_login():
    email = "testuser_auth@lifebook.ai"
    password = "SecretPassword123!"
    
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User"
    })
    assert reg_res.status_code in [201, 200, 400] # 201 Created, or 400 if already exists

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

def test_invalid_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@lifebook.ai",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
