import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def unique_user():
    import uuid
    return f"user_{uuid.uuid4().hex[:6]}"

def test_register_and_login(client: TestClient, unique_user):
    # Регистрация
    resp = client.post(
        "/register",
        json={"username": unique_user, "password": "TestPass!1"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == unique_user
    assert "password" not in data

    # Логин (form data, не JSON)
    resp2 = client.post(
        "/login",
        data={"username": unique_user, "password": "TestPass!1"}
    )
    assert resp2.status_code == 200
    token_data = resp2.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
