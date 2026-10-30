import uuid
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

def test_registration_validation():
    # Weak password (<8 chars)
    res_short = client.post("/api/v1/auth/register", json={
        "email": f"short_{uuid.uuid4().hex[:8]}@lifebook.ai",
        "password": "pass",
        "full_name": "Short Password"
    })
    assert res_short.status_code == 422

    # Weak password (no number or special character)
    res_no_num = client.post("/api/v1/auth/register", json={
        "email": f"nonum_{uuid.uuid4().hex[:8]}@lifebook.ai",
        "password": "onlylettershere",
        "full_name": "No Number Password"
    })
    assert res_no_num.status_code == 422

    # Successful registration
    unique_email = f"user_{uuid.uuid4().hex[:8]}@lifebook.ai"
    res_success = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "ValidPassword2026!",
        "full_name": "Valid User"
    })
    assert res_success.status_code == 201
    data = res_success.json()
    assert data["user"]["email"] == unique_email
    assert data["user"]["full_name"] == "Valid User"
    assert "hashed_password" not in data["user"]
    assert "access_token" in data

    # Duplicate registration rejected
    res_dup = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "ValidPassword2026!",
        "full_name": "Duplicate User"
    })
    assert res_dup.status_code == 400
    assert "already registered" in res_dup.json()["detail"].lower()

def test_login_and_token_handling():
    email = f"login_{uuid.uuid4().hex[:8]}@lifebook.ai"
    password = "CorrectPassword123!"

    # Create account
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Login Tester"
    })

    # Successful login
    res_ok = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert res_ok.status_code == 200
    token_data = res_ok.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]
    user_id = token_data["user"]["id"]

    # Verify /me endpoint with valid token
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == email

    # Incorrect password
    res_wrong_pw = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword123!"
    })
    assert res_wrong_pw.status_code == 401

    # Non-existent email
    res_no_user = client.post("/api/v1/auth/login", json={
        "email": f"nonexistent_{uuid.uuid4().hex[:8]}@lifebook.ai",
        "password": "Password123!"
    })
    assert res_no_user.status_code == 401

    # Missing token on protected endpoint
    res_no_token = client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # Malformed token
    res_malformed = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert res_malformed.status_code == 401

    # Tampered token
    tampered_token = token[:-5] + "XXXXX"
    res_tampered = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_tampered.status_code == 401

    # Expired token
    expired_token = create_access_token(user_id, expires_delta=timedelta(seconds=-60))
    res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401

def test_google_oauth_mock_and_account_linking():
    g_uid = uuid.uuid4().hex[:8]
    # 1. Sign up/in with Google Mock Token
    custom_avatar = "https://lh3.googleusercontent.com/avatar_test.jpg"
    google_mock_token = f"mock-google-token:goog_id_{g_uid}:google_{g_uid}@lifebook.ai:Google Dev:{custom_avatar}"
    res_google = client.post("/api/v1/auth/google", json={"id_token": google_mock_token})
    assert res_google.status_code == 200
    g_data = res_google.json()
    assert "access_token" in g_data
    assert g_data["user"]["email"] == f"google_{g_uid}@lifebook.ai"
    assert g_data["user"]["auth_provider"] == "google"
    assert g_data["user"]["avatar_url"] == custom_avatar

    # 2. Subsequent login with same Google account returns same user
    res_google_again = client.post("/api/v1/auth/google", json={"id_token": google_mock_token})
    assert res_google_again.status_code == 200
    assert res_google_again.json()["user"]["id"] == g_data["user"]["id"]

    # 3. Account Linking: Register with email first, then sign in with Google with same email
    link_uid = uuid.uuid4().hex[:8]
    link_email = f"link_{link_uid}@lifebook.ai"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": link_email,
        "password": "Password2026!",
        "full_name": "Link Candidate"
    })
    assert reg_res.status_code == 201

    # Now login with Google having the same email
    google_link_token = f"mock-google-token:goog_link_{link_uid}:{link_email}:Google Linked Name:https://avatar.url/linked.jpg"
    res_link = client.post("/api/v1/auth/google", json={"id_token": google_link_token})
    assert res_link.status_code == 200
    linked_user = res_link.json()["user"]
    assert linked_user["email"] == link_email
    assert linked_user["auth_provider"] == "both"
    assert linked_user["google_id"] == f"goog_link_{link_uid}"

def test_user_data_isolation():
    # Register User 1
    u1_email = f"user1_{uuid.uuid4().hex[:8]}@lifebook.ai"
    client.post("/api/v1/auth/register", json={
        "email": u1_email,
        "password": "Password123!",
        "full_name": "User One"
    })
    token_1 = client.post("/api/v1/auth/login", json={
        "email": u1_email,
        "password": "Password123!"
    }).json()["access_token"]
    h1 = {"Authorization": f"Bearer {token_1}"}

    # Register User 2
    u2_email = f"user2_{uuid.uuid4().hex[:8]}@lifebook.ai"
    client.post("/api/v1/auth/register", json={
        "email": u2_email,
        "password": "Password123!",
        "full_name": "User Two"
    })
    token_2 = client.post("/api/v1/auth/login", json={
        "email": u2_email,
        "password": "Password123!"
    }).json()["access_token"]
    h2 = {"Authorization": f"Bearer {token_2}"}

    # User 1 creates a private diary entry
    res_entry = client.post("/api/v1/diary/text", headers=h1, json={
        "raw_text": "Confidential diary entry belonging only to User One.",
        "title": "User 1 Secret Diary"
    })
    assert res_entry.status_code == 200
    entry_id = res_entry.json()["id"]

    # User 2 attempts to view User 1's diary entry -> 404 Not Found
    res_fetch = client.get(f"/api/v1/diary/{entry_id}", headers=h2)
    assert res_fetch.status_code == 404

    # User 2's diary list should NOT contain User 1's entry
    res_list = client.get("/api/v1/diary", headers=h2)
    assert res_list.status_code == 200
    entry_ids = [e["id"] for e in res_list.json()]
    assert entry_id not in entry_ids

    # User 2 cannot retry or regenerate User 1's entry -> 404 Not Found
    res_retry = client.post(f"/api/v1/diary/{entry_id}/retry", headers=h2)
    assert res_retry.status_code == 404

    # User 1 creates a commitment
    res_comm = client.post("/api/v1/commitments", headers=h1, json={
        "title": "User 1 Secret Goal",
        "description": "Must not be visible to User 2",
        "due_date": "2026-12-31"
    })
    assert res_comm.status_code == 200
    comm_id = res_comm.json()["id"]

    # User 2 cannot complete or see User 1's commitment
    res_complete = client.post(f"/api/v1/commitments/{comm_id}/complete", headers=h2)
    assert res_complete.status_code == 404

    res_comms_2 = client.get("/api/v1/commitments", headers=h2)
    assert res_comms_2.status_code == 200
    comm_ids_2 = [c["id"] for c in res_comms_2.json()]
    assert comm_id not in comm_ids_2

    # User 2 cannot dismiss User 1's commitment
    res_dismiss = client.post(f"/api/v1/commitments/{comm_id}/dismiss", headers=h2)
    assert res_dismiss.status_code == 404

def test_password_reset_flow():
    email = f"reset_{uuid.uuid4().hex[:8]}@lifebook.ai"
    old_pw = "OriginalPassword123!"
    new_pw = "BrandNewPassword2026!"

    # 1. Register
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": old_pw,
        "full_name": "Reset Tester"
    })

    # 2. Forgot Password Request
    res_forgot = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert res_forgot.status_code == 200
    reset_token = res_forgot.json().get("reset_token")
    assert reset_token is not None

    # 3. Reset Password
    res_reset = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": new_pw
    })
    assert res_reset.status_code == 200

    # 4. Old password fails
    res_old_fail = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": old_pw
    })
    assert res_old_fail.status_code == 401

    # 5. New password succeeds
    res_new_ok = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": new_pw
    })
    assert res_new_ok.status_code == 200
    assert "access_token" in res_new_ok.json()
