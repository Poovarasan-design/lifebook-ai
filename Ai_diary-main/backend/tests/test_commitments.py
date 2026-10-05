from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "jothiram@lifebook.ai",
        "password": "LifeBook2026!"
    })
    return res.json()["access_token"]

def test_commitments_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ensure at least one commitment exists
    client.post("/api/v1/commitments", headers=headers, json={
        "description": "Finish SIH API",
        "project": "SIH Project",
        "due_date": "Next Wednesday",
        "priority": "high"
    })

    # 2. List commitments
    list_res = client.get("/api/v1/commitments", headers=headers)
    assert list_res.status_code == 200
    commitments = list_res.json()
    assert len(commitments) > 0

    # 3. Mark first commitment as completed
    c_id = commitments[0]["id"]
    comp_res = client.post(f"/api/v1/commitments/{c_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # 4. Test "What am I forgetting?"
    forget_res = client.post("/api/v1/search/forgetting", headers=headers)
    assert forget_res.status_code == 200
    assert "items" in forget_res.json()
