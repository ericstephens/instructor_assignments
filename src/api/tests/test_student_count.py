"""
Tests for PATCH /event-dates/{id}/students endpoint.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone


def _make_event(client, max_students=20, title="Student Test Event"):
    r = client.post("/events", json={
        "title": title,
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": max_students,
        "location": "Room S",
    })
    assert r.status_code == 201, r.text
    return r.json()


def _make_event_date(client, event_id):
    now = datetime.now(timezone.utc)
    start = now.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=17, minute=0, second=0, microsecond=0).isoformat()
    r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": now.date().isoformat(),
        "start_time": start,
        "end_time": end,
    })
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_patch_students_sets_count(client):
    event = _make_event(client, max_students=30)
    ed = _make_event_date(client, event["id"])

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": 15})
    assert r.status_code == 200
    assert r.json()["registered_students"] == 15


def test_patch_students_zero(client):
    event = _make_event(client, max_students=10)
    ed = _make_event_date(client, event["id"])

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": 0})
    assert r.status_code == 200
    assert r.json()["registered_students"] == 0


def test_patch_students_at_max_capacity(client):
    event = _make_event(client, max_students=25)
    ed = _make_event_date(client, event["id"])

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": 25})
    assert r.status_code == 200
    assert r.json()["registered_students"] == 25


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_patch_students_exceeds_max_409(client):
    event = _make_event(client, max_students=10)
    ed = _make_event_date(client, event["id"])

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": 11})
    assert r.status_code == 409
    assert "max_students" in r.json()["detail"]


def test_patch_students_negative_422(client):
    event = _make_event(client, max_students=10)
    ed = _make_event_date(client, event["id"])

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": -1})
    assert r.status_code == 422


def test_patch_students_not_found_404(client):
    r = client.patch("/event-dates/99999/students", json={"registered_students": 5})
    assert r.status_code == 404


def test_patch_students_on_cancelled_event_date_409(client):
    event = _make_event(client, max_students=20)
    ed = _make_event_date(client, event["id"])

    client.post(f"/event-dates/{ed['id']}/cancel")

    r = client.patch(f"/event-dates/{ed['id']}/students", json={"registered_students": 5})
    assert r.status_code == 409
    assert "cancelled" in r.json()["detail"].lower()
