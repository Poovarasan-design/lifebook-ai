import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "jothiram@lifebook.ai",
        "password": "LifeBook2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]

def test_create_text_entry_and_status():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/diary/text", headers=headers, json={
        "raw_text": "Today I went to college with Ravi and we worked on our SIH project.",
        "title": "College SIH Sprint"
    })
    assert res.status_code == 200
    entry = res.json()
    assert entry["status"] in ["RECEIVED", "SAVED"]
    assert entry["input_type"] == "text"
    
    # Check status endpoint
    status_res = client.get(f"/api/v1/diary/{entry['id']}/status", headers=headers)
    assert status_res.status_code == 200
    assert "status" in status_res.json()

def test_confirm_entry():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create entry
    res = client.post("/api/v1/diary/text", headers=headers, json={
        "raw_text": "Customer meeting in Madurai with Ravi.",
        "title": "Madurai Visit"
    })
    entry = res.json()

    # Confirm
    conf_res = client.post(f"/api/v1/diary/{entry['id']}/confirm", headers=headers, json={
        "confirmed_title": "Confirmed Madurai Visit",
        "confirmed_content": "Today I went to Madurai for a customer meeting with Ravi."
    })
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "COMPLETED"

def test_calendar_activities_and_specials():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/memories/calendar?year=2026&month=9", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["year"] == 2026
    assert data["month"] == 9
    assert data["month_name"] == "September"
    assert len(data["days"]) == 30
    assert "monthly_specials" in data
    assert len(data["monthly_specials"]) >= 1
    assert "yearly_specials" in data
    assert len(data["yearly_specials"]) >= 1
    assert "annual_story" in data
    assert len(data["annual_story"]) > 20
