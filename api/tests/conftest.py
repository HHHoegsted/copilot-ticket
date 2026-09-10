"""Shared test fixtures: a disposable Postgres database per test session.

Tests exercise the API exclusively through the HTTP seam (TestClient)
against a real database whose schema is created by the real Alembic
migrations at app startup.
"""

import os
import uuid

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

TEST_PG_USER = "ticketing"
TEST_PG_PASSWORD = "ticketing"
TEST_PG_HOST = os.environ.get("TEST_PG_HOST", "localhost:5433")
TEST_DB_NAME = "ticketing_test"

SEED_AGENT_USERNAME = "agent"
SEED_AGENT_PASSWORD = "agent-password-123"


def _server_url() -> str:
    return f"postgresql+psycopg2://{TEST_PG_USER}:{TEST_PG_PASSWORD}@{TEST_PG_HOST}/postgres"


def _test_url() -> str:
    return f"postgresql+psycopg2://{TEST_PG_USER}:{TEST_PG_PASSWORD}@{TEST_PG_HOST}/{TEST_DB_NAME}"


def _reset_database() -> None:
    engine = sa.create_engine(_server_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
        conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    engine.dispose()


@pytest.fixture(scope="session")
def app():
    _reset_database()
    os.environ["DATABASE_URL"] = _test_url()
    os.environ["SESSION_SECRET"] = "test-session-secret"
    os.environ["INITIAL_AGENT_USERNAME"] = SEED_AGENT_USERNAME
    os.environ["INITIAL_AGENT_PASSWORD"] = SEED_AGENT_PASSWORD
    from app.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def make_agent(client):
    """Create an agent user directly in the database (test setup only).

    Registration always creates customers, so additional agents are
    inserted directly. This is setup, never a way to verify behaviour.
    """
    from app.db import SessionLocal
    from app.models import User
    from app.security import hash_password

    def _make_agent(username: str | None = None, password: str = "agent-password-123") -> dict:
        username = username or f"agent-{uuid.uuid4().hex[:8]}"
        with SessionLocal() as session:
            user = User(username=username, password_hash=hash_password(password), role="agent")
            session.add(user)
            session.commit()
            session.refresh(user)
            return {"id": user.id, "username": username, "password": password}

    return _make_agent