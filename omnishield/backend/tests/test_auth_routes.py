# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from fastapi import status
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_user_registration_and_login(client: TestClient):
    # 1. Register a test user
    reg_payload = {
        "email": "tester@example.com",
        "password": "securepassword123"
    }
    reg_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_response.status_code == status.HTTP_201_CREATED
    data = reg_response.json()
    assert data["email"] == "tester@example.com"
    assert "id" in data
    assert data["role"] == "client"

    # 2. Try to register same email again (duplicate error check)
    dup_response = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in dup_response.json()["detail"]

    # 3. Login with correct credentials
    login_payload = {
        "username": "tester@example.com",
        "password": "securepassword123"
    }
    login_response = client.post("/api/v1/auth/login", data=login_payload)
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert "access_token" in token_data

    # 4. Login with incorrect password
    bad_login_payload = {
        "username": "tester@example.com",
        "password": "wrongpassword"
    }
    bad_login_response = client.post("/api/v1/auth/login", data=bad_login_payload)
    assert bad_login_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Incorrect email or password" in bad_login_response.json()["detail"]
