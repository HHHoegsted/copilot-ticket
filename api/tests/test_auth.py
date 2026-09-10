from fastapi.testclient import TestClient

from tests.conftest import SEED_AGENT_PASSWORD, SEED_AGENT_USERNAME


def test_registration_creates_customer_account(client):
    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "secret-123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == "customer"


def test_registration_rejects_duplicate_username(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "other-456"}
    )
    assert response.status_code == 409
    assert "error" in str(response.json()).lower() or "detail" in response.json()


def test_login_with_valid_credentials_establishes_session(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    response = client.post(
        "/api/auth/login", json={"username": "alice", "password": "secret-123"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert "session" in response.cookies
    assert "httponly" in response.headers["set-cookie"].lower()


def test_login_with_invalid_credentials_is_rejected(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    response = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert response.status_code == 401


def test_logout_invalidates_session(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    client.post("/api/auth/login", json={"username": "alice", "password": "secret-123"})
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_current_user_returns_identity_and_role(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    client.post("/api/auth/login", json={"username": "alice", "password": "secret-123"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == "customer"


def test_passwords_are_stored_hashed(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "secret-123"})
    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as session:
        user = session.query(User).filter_by(username="alice").one()
        assert user.password_hash != "secret-123"
        assert user.password_hash.startswith("$2")


def test_seeded_agent_can_log_in_and_is_recognized_as_agent(client):
    response = client.post(
        "/api/auth/login",
        json={"username": SEED_AGENT_USERNAME, "password": SEED_AGENT_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "agent"


def test_seeded_agent_is_not_recreated_on_later_starts(app, client):
    first = client.post(
        "/api/auth/login",
        json={"username": SEED_AGENT_USERNAME, "password": SEED_AGENT_PASSWORD},
    )
    assert first.status_code == 200
    first_id = first.json()["id"]
    # Simulate a later start of the API: startup runs the seed again.
    with TestClient(app) as second_client:
        second = second_client.post(
            "/api/auth/login",
            json={"username": SEED_AGENT_USERNAME, "password": SEED_AGENT_PASSWORD},
        )
    assert second.status_code == 200
    assert second.json()["id"] == first_id