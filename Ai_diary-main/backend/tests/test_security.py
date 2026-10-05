from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_isolation():
    # Register User A
    client.post("/api/v1/auth/register", json={
        "email": "usera_sec@lifebook.ai",
        "password": "Password123!",
        "full_name": "User A"
    })
    token_a = client.post("/api/v1/auth/login", json={
        "email": "usera_sec@lifebook.ai",
        "password": "Password123!"
    }).json()["access_token"]

    # Register User B
    client.post("/api/v1/auth/register", json={
        "email": "userb_sec@lifebook.ai",
        "password": "Password123!",
        "full_name": "User B"
    })
    token_b = client.post("/api/v1/auth/login", json={
        "email": "userb_sec@lifebook.ai",
        "password": "Password123!"
    }).json()["access_token"]

    # User A creates entry
    res_a = client.post("/api/v1/diary/text", headers={"Authorization": f"Bearer {token_a}"}, json={
        "raw_text": "User A Private Secret Diary",
        "title": "Private Entry A"
    })
    entry_id_a = res_a.json()["id"]

    # User B tries to fetch User A's entry -> must return 404
    fetch_b = client.get(f"/api/v1/diary/{entry_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert fetch_b.status_code == 404

def test_unauthenticated_access_rejected():
    res = client.get("/api/v1/diary")
    assert res.status_code == 401
