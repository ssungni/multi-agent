import fakeredis
import pytest
from fastapi.testclient import TestClient

from src.auth.service import _verify_code_key
from src.core.database import get_db
from src.core.redis import get_redis
from src.main import app

VALID_SIGNUP = {
    "name": "홍길동",
    "email": "router@example.com",
    "password": "Passw0rd!",
    "phone": "010-1234-5678",
}


@pytest.fixture
def client(db_session):
    redis_client = fakeredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: redis_client
    with TestClient(app) as test_client:
        test_client._fake_redis = redis_client
        yield test_client

    app.dependency_overrides.clear()


def test_signup_returns_201(client):
    res = client.post("/api/auth/signup", json=VALID_SIGNUP)
    assert res.status_code == 201
    assert res.json()["email"] == VALID_SIGNUP["email"]


def test_signup_duplicate_email_returns_409(client):
    client.post("/api/auth/signup", json=VALID_SIGNUP)
    code = client._fake_redis.get(_verify_code_key(VALID_SIGNUP["email"]))
    client.post(
        "/api/auth/signup/verify", json={"email": VALID_SIGNUP["email"], "code": code}
    )

    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, "phone": "010-0000-0000"})
    assert res.status_code == 409
    assert res.json()["error_code"] == "EMAIL_DUPLICATE"


def test_signup_weak_password_returns_422(client):
    res = client.post("/api/auth/signup", json={**VALID_SIGNUP, "password": "weak"})
    assert res.status_code == 422


def test_full_signup_login_refresh_logout_flow(client):
    client.post("/api/auth/signup", json=VALID_SIGNUP)
    code = client._fake_redis.get(_verify_code_key(VALID_SIGNUP["email"]))

    verify_res = client.post(
        "/api/auth/signup/verify", json={"email": VALID_SIGNUP["email"], "code": code}
    )
    assert verify_res.status_code == 200
    assert "refresh_token" in verify_res.cookies
    access_token = verify_res.json()["access_token"]

    me_res = client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == VALID_SIGNUP["email"]

    me_unauth_res = client.get("/api/users/me")
    assert me_unauth_res.status_code == 401
    assert me_unauth_res.json()["error_code"] == "INVALID_ACCESS_TOKEN"

    login_res = client.post(
        "/api/auth/login",
        json={"email": VALID_SIGNUP["email"], "password": VALID_SIGNUP["password"]},
    )
    assert login_res.status_code == 200

    refresh_res = client.post("/api/auth/refresh")
    assert refresh_res.status_code == 200
    assert refresh_res.json()["access_token"]

    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    refresh_after_logout_res = client.post("/api/auth/refresh")
    assert refresh_after_logout_res.status_code == 401
    assert refresh_after_logout_res.json()["error_code"] == "INVALID_REFRESH_TOKEN"


def test_login_wrong_password_returns_401(client):
    res = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "whatever1!"}
    )
    assert res.status_code == 401
    assert res.json()["error_code"] == "INVALID_CREDENTIALS"


def test_check_email_availability(client):
    res = client.get("/api/auth/check-email", params={"email": "new@example.com"})
    assert res.status_code == 200
    assert res.json()["available"] is True
