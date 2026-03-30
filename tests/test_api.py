import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app, Settings, pwd_context, fake_users_db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.mark.anyio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == app.title
    assert data["version"] == app.version


@pytest.mark.anyio
async def test_predict_endpoint(async_client: AsyncClient):
    payload = {"input_text": "hello world"}
    response = await async_client.post("/api/predict", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prediction"] == "dlrow olleh"
    assert data["model_version"] == app.version


@pytest.mark.anyio
async def test_successful_login_and_protected_route(async_client: AsyncClient):
    # Login with valid credentials
    login_data = {"username": "alice", "password": "secret1"}
    response = await async_client.post(
        "/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    # Access protected route
    protected_response = await async_client.get(
        "/protected", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert protected_response.status_code == status.HTTP_200_OK
    protected_data = protected_response.json()
    assert protected_data["message"] == "Hello, alice! This is a protected endpoint."


@pytest.mark.anyio
async def test_login_failure(async_client: AsyncClient):
    # Wrong password
    login_data = {"username": "alice", "password": "wrongpassword"}
    response = await async_client.post(
        "/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_detail = response.json()["detail"]
    assert error_detail == "Incorrect username or password"


@pytest.mark.anyio
async def test_inactive_user_cannot_access_protected(async_client: AsyncClient):
    # Temporarily disable user bob
    fake_users_db["bob"].disabled = True

    # Login as bob (should succeed, token still issued)
    login_data = {"username": "bob", "password": "secret2"}
    response = await async_client.post(
        "/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]

    # Attempt to access protected route, expect 400
    protected_response = await async_client.get(
        "/protected", headers={"Authorization": f"Bearer {token}"}
    )
    assert protected_response.status_code == status.HTTP_400_BAD_REQUEST
    assert protected_response.json()["detail"] == "Inactive user"

    # Clean up
    fake_users_db["bob"].disabled = False