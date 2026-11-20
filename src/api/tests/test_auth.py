"""
Auth endpoint tests — register, login, /me, RBAC enforcement.
Uses real PostgreSQL (instructor_test_db) with no auth dependency overrides
so we can test the actual JWT flow.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.config import Base, get_db
from src.api.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/instructor_test_db",
)


@pytest.fixture(scope="module")
def auth_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def auth_session(auth_engine):
    connection = auth_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def raw_client(auth_session):
    """TestClient with real auth (no dependency overrides)."""
    def override_get_db():
        try:
            yield auth_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(client, email, password="password123", role="instructor"):
    return client.post("/auth/register", json={"email": email, "password": password, "role": role})


def _token(client, email, password="password123"):
    return client.post("/auth/token", data={"username": email, "password": password})


def _auth_headers(client, email, password="password123"):
    r = _token(client, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_creates_instructor(raw_client):
    r = _register(raw_client, "inst1@example.com")
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "inst1@example.com"
    assert data["role"] == "instructor"
    assert data["is_active"] is True


def test_register_creates_admin(raw_client):
    r = _register(raw_client, "admin1@example.com", role="admin")
    assert r.status_code == 201
    assert r.json()["role"] == "admin"


def test_register_duplicate_email_409(raw_client):
    _register(raw_client, "dup@example.com")
    r = _register(raw_client, "dup@example.com")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Login / token
# ---------------------------------------------------------------------------

def test_login_returns_token(raw_client):
    _register(raw_client, "login1@example.com")
    r = _token(raw_client, "login1@example.com")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_401(raw_client):
    _register(raw_client, "login2@example.com")
    r = _token(raw_client, "login2@example.com", password="wrong")
    assert r.status_code == 401


def test_login_unknown_user_401(raw_client):
    r = _token(raw_client, "nobody@example.com")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

def test_me_returns_current_user(raw_client):
    _register(raw_client, "me1@example.com")
    headers = _auth_headers(raw_client, "me1@example.com")
    r = raw_client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "me1@example.com"


def test_me_no_token_401(raw_client):
    r = raw_client.get("/auth/me")
    assert r.status_code == 401


def test_me_bad_token_401(raw_client):
    r = raw_client.get("/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# RBAC enforcement on protected endpoints
# ---------------------------------------------------------------------------

def test_create_event_requires_auth(raw_client):
    payload = {
        "title": "No Auth Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room X",
    }
    r = raw_client.post("/events", json=payload)
    assert r.status_code == 401


def test_create_event_instructor_forbidden(raw_client):
    _register(raw_client, "inst2@example.com", role="instructor")
    headers = _auth_headers(raw_client, "inst2@example.com")
    payload = {
        "title": "Instructor Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room Y",
    }
    r = raw_client.post("/events", json=payload, headers=headers)
    assert r.status_code == 403


def test_create_event_admin_succeeds(raw_client):
    _register(raw_client, "admin2@example.com", role="admin")
    headers = _auth_headers(raw_client, "admin2@example.com")
    payload = {
        "title": "Admin Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room Z",
    }
    r = raw_client.post("/events", json=payload, headers=headers)
    assert r.status_code == 201


def test_allocate_requires_auth(raw_client):
    r = raw_client.post("/allocations", json={
        "event_date_id": 1, "instructor_id": 1, "role": "primary", "shift_duration": 4
    })
    assert r.status_code == 401
