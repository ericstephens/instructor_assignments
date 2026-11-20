"""
API integration tests — real PostgreSQL, no mocking.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def test_create_event(client):
    payload = {
        "title": "Python 101",
        "description": "Intro course",
        "duration": 2,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 2,
        "max_students": 20,
        "location": "Room A",
        "catalog_status": "active",
    }
    r = client.post("/events", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Python 101"
    assert data["location"] == "Room A"
    assert data["id"] is not None


def test_list_events(client):
    # Create one event first
    client.post("/events", json={
        "title": "Event List Test",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room B",
    })
    r = client.get("/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_event(client):
    create_r = client.post("/events", json={
        "title": "Get Event Test",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room C",
    })
    event_id = create_r.json()["id"]
    r = client.get(f"/events/{event_id}")
    assert r.status_code == 200
    assert r.json()["id"] == event_id


def test_get_event_not_found(client):
    r = client.get("/events/999999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Instructors
# ---------------------------------------------------------------------------

def test_create_instructor(client):
    payload = {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "lead",
    }
    r = client.post("/instructors", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "lead"


def test_create_instructor_duplicate_email(client):
    payload = {"name": "Bob", "email": "bob_dup@example.com", "role": "primary"}
    client.post("/instructors", json=payload)
    r = client.post("/instructors", json=payload)
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# EventDates
# ---------------------------------------------------------------------------

def test_create_event_date(client):
    # Create parent event
    event_r = client.post("/events", json={
        "title": "Event for Dates",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 1,
        "max_students": 15,
        "location": "Room D",
    })
    event_id = event_r.json()["id"]

    payload = {
        "event_id": event_id,
        "date": "2026-03-01T00:00:00",
        "start_time": "2026-03-01T09:00:00",
        "end_time": "2026-03-01T17:00:00",
        "registered_students": 5,
    }
    r = client.post("/event-dates", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["event_id"] == event_id


# ---------------------------------------------------------------------------
# Allocations
# ---------------------------------------------------------------------------

def _setup_allocation_fixture(client):
    """Helper: create event, two event_dates, two instructors. Returns dict."""
    event_r = client.post("/events", json={
        "title": "Alloc Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 1,
        "max_students": 20,
        "location": "Room E",
    })
    event_id = event_r.json()["id"]

    ed1_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-04-01T00:00:00",
        "start_time": "2026-04-01T09:00:00",
        "end_time": "2026-04-01T17:00:00",
    })
    ed1_id = ed1_r.json()["id"]

    # Overlapping second event date (same window)
    ed2_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-04-01T00:00:00",
        "start_time": "2026-04-01T10:00:00",
        "end_time": "2026-04-01T14:00:00",
    })
    ed2_id = ed2_r.json()["id"]

    inst1_r = client.post("/instructors", json={
        "name": "Carol Jones",
        "email": "carol_alloc@example.com",
        "role": "lead",
    })
    inst1_id = inst1_r.json()["id"]

    return {
        "event_id": event_id,
        "ed1_id": ed1_id,
        "ed2_id": ed2_id,
        "inst1_id": inst1_id,
    }


def test_create_allocation_valid(client):
    fx = _setup_allocation_fixture(client)
    payload = {
        "event_date_id": fx["ed1_id"],
        "instructor_id": fx["inst1_id"],
        "shift_duration": 8,
        "role": "primary",
    }
    r = client.post("/allocations", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["event_date_id"] == fx["ed1_id"]
    assert data["instructor_id"] == fx["inst1_id"]


def test_create_allocation_double_booking(client):
    """Instructor allocated to ed1 (09-17) cannot be allocated to overlapping ed2 (10-14)."""
    fx = _setup_allocation_fixture(client)

    # First allocation on ed1
    r1 = client.post("/allocations", json={
        "event_date_id": fx["ed1_id"],
        "instructor_id": fx["inst1_id"],
        "shift_duration": 8,
        "role": "primary",
    })
    assert r1.status_code == 201

    # Second allocation on overlapping ed2 — must be 409
    r2 = client.post("/allocations", json={
        "event_date_id": fx["ed2_id"],
        "instructor_id": fx["inst1_id"],
        "shift_duration": 4,
        "role": "secondary",
    })
    assert r2.status_code == 409


def test_create_allocation_duplicate_lead(client):
    """Only one lead per EventDate."""
    fx = _setup_allocation_fixture(client)

    # Create a second instructor
    inst2_r = client.post("/instructors", json={
        "name": "Dave Lead",
        "email": "dave_lead@example.com",
        "role": "lead",
    })
    inst2_id = inst2_r.json()["id"]

    # First lead allocation
    r1 = client.post("/allocations", json={
        "event_date_id": fx["ed1_id"],
        "instructor_id": fx["inst1_id"],
        "shift_duration": 8,
        "role": "lead",
    })
    assert r1.status_code == 201

    # Second lead on same event_date — must be 409
    r2 = client.post("/allocations", json={
        "event_date_id": fx["ed1_id"],
        "instructor_id": inst2_id,
        "shift_duration": 8,
        "role": "lead",
    })
    assert r2.status_code == 409


def test_delete_allocation(client):
    fx = _setup_allocation_fixture(client)
    create_r = client.post("/allocations", json={
        "event_date_id": fx["ed1_id"],
        "instructor_id": fx["inst1_id"],
        "shift_duration": 8,
        "role": "secondary",
    })
    assert create_r.status_code == 201
    alloc_id = create_r.json()["id"]

    del_r = client.delete(f"/allocations/{alloc_id}")
    assert del_r.status_code == 204

    # Verify gone
    list_r = client.get(f"/allocations?event_date_id={fx['ed1_id']}")
    ids = [a["id"] for a in list_r.json()]
    assert alloc_id not in ids


# ---------------------------------------------------------------------------
# Staffing status
# ---------------------------------------------------------------------------

def test_staffing_status(client):
    event_r = client.post("/events", json={
        "title": "Staffing Event",
        "duration": 1,
        "min_primary_instructors": 2,
        "min_secondary_instructors": 1,
        "max_students": 20,
        "location": "Room F",
    })
    event_id = event_r.json()["id"]

    ed_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-05-01T00:00:00",
        "start_time": "2026-05-01T09:00:00",
        "end_time": "2026-05-01T17:00:00",
    })
    ed_id = ed_r.json()["id"]

    # Add a lead instructor
    lead_r = client.post("/instructors", json={
        "name": "Eve Lead",
        "email": "eve_staffing@example.com",
        "role": "lead",
    })
    lead_id = lead_r.json()["id"]

    client.post("/allocations", json={
        "event_date_id": ed_id,
        "instructor_id": lead_id,
        "shift_duration": 8,
        "role": "lead",
    })

    r = client.get(f"/event-dates/{ed_id}/staffing-status")
    assert r.status_code == 200
    data = r.json()
    assert data["lead_assigned"] is True
    assert data["lead_instructor_id"] == lead_id
    assert data["primary_count"] == 0
    assert data["min_primary_instructors"] == 2
    assert data["primary_met"] is False
    assert data["secondary_count"] == 0
    assert data["min_secondary_instructors"] == 1
    assert data["secondary_met"] is False
