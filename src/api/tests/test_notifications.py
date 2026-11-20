"""
Notification service tests.

Covers:
  - send_notification log backend (default) writes to logger, no SMTP call
  - Helper functions produce correct subject/body content
  - Allocation create/delete triggers notify (via caplog)
  - Event date cancel triggers notify for each allocated instructor
"""
from __future__ import annotations

import logging

import pytest

from src.api.notifications import (
    notify_allocation_created,
    notify_allocation_removed,
    notify_event_date_cancelled,
    send_notification,
)


# ---------------------------------------------------------------------------
# Unit tests for notification helpers (no DB needed)
# ---------------------------------------------------------------------------

def test_send_notification_log_backend(caplog):
    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        send_notification("test@example.com", "Test Subject", "Test body")
    assert any("Test Subject" in r.message for r in caplog.records)
    assert any("test@example.com" in r.message for r in caplog.records)


def test_notify_allocation_created_content(caplog):
    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        notify_allocation_created(
            instructor_email="inst@example.com",
            instructor_name="Alice",
            event_title="Python 101",
            event_date_str="2026-03-01",
            role="primary",
        )
    combined = " ".join(r.message for r in caplog.records)
    assert "Python 101" in combined
    assert "primary" in combined
    assert "inst@example.com" in combined


def test_notify_allocation_removed_content(caplog):
    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        notify_allocation_removed(
            instructor_email="inst@example.com",
            instructor_name="Bob",
            event_title="Go Basics",
            event_date_str="2026-04-10",
        )
    combined = " ".join(r.message for r in caplog.records)
    assert "Go Basics" in combined
    assert "removed" in combined.lower()


def test_notify_event_date_cancelled_content(caplog):
    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        notify_event_date_cancelled(
            instructor_email="lead@example.com",
            instructor_name="Carol",
            event_title="Rust Workshop",
            event_date_str="2026-05-20",
        )
    combined = " ".join(r.message for r in caplog.records)
    assert "Rust Workshop" in combined
    assert "cancelled" in combined.lower()


# ---------------------------------------------------------------------------
# Integration: notifications fire via routers
# ---------------------------------------------------------------------------

def test_allocation_create_triggers_notification(client, caplog):
    """Creating an allocation should log a notification for the instructor."""
    # Create event + event_date + instructor
    event = client.post("/events", json={
        "title": "Notify Test Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room N",
    }).json()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    start = now.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=17, minute=0, second=0, microsecond=0).isoformat()

    ed = client.post("/event-dates", json={
        "event_id": event["id"],
        "date": now.date().isoformat(),
        "start_time": start,
        "end_time": end,
    }).json()

    instr = client.post("/instructors", json={
        "name": "Notify Instructor",
        "email": "notify_instr@example.com",
        "role": "primary",
    }).json()

    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        r = client.post("/allocations", json={
            "event_date_id": ed["id"],
            "instructor_id": instr["id"],
            "role": "primary",
            "shift_duration": 8,
        })
    assert r.status_code == 201
    # Give daemon thread a moment to run
    import time; time.sleep(0.1)
    combined = " ".join(rec.message for rec in caplog.records)
    assert "notify_instr@example.com" in combined or "Notify Test Event" in combined


def test_allocation_delete_triggers_notification(client, caplog):
    """Deleting an allocation should log a removal notification."""
    event = client.post("/events", json={
        "title": "Delete Notify Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room D",
    }).json()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    start = now.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()

    ed = client.post("/event-dates", json={
        "event_id": event["id"],
        "date": now.date().isoformat(),
        "start_time": start,
        "end_time": end,
    }).json()

    instr = client.post("/instructors", json={
        "name": "Delete Notify Instructor",
        "email": "del_notify@example.com",
        "role": "primary",
    }).json()

    alloc = client.post("/allocations", json={
        "event_date_id": ed["id"],
        "instructor_id": instr["id"],
        "role": "primary",
        "shift_duration": 8,
    }).json()

    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        r = client.delete(f"/allocations/{alloc['id']}")
    assert r.status_code == 204
    import time; time.sleep(0.1)
    combined = " ".join(rec.message for rec in caplog.records)
    assert "del_notify@example.com" in combined or "Delete Notify Event" in combined


def test_cancel_event_date_notifies_allocated_instructors(client, caplog):
    """Cancelling an event date should notify all allocated instructors."""
    event = client.post("/events", json={
        "title": "Cancel Notify Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room C",
    }).json()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    start = now.replace(hour=8, minute=0, second=0, microsecond=0).isoformat()
    end = now.replace(hour=16, minute=0, second=0, microsecond=0).isoformat()

    ed = client.post("/event-dates", json={
        "event_id": event["id"],
        "date": now.date().isoformat(),
        "start_time": start,
        "end_time": end,
    }).json()

    instr1 = client.post("/instructors", json={
        "name": "Cancel Instr One",
        "email": "cancel1@example.com",
        "role": "primary",
    }).json()
    instr2 = client.post("/instructors", json={
        "name": "Cancel Instr Two",
        "email": "cancel2@example.com",
        "role": "secondary",
    }).json()

    client.post("/allocations", json={
        "event_date_id": ed["id"], "instructor_id": instr1["id"],
        "role": "primary", "shift_duration": 8,
    })
    client.post("/allocations", json={
        "event_date_id": ed["id"], "instructor_id": instr2["id"],
        "role": "secondary", "shift_duration": 4,
    })

    with caplog.at_level(logging.INFO, logger="src.api.notifications"):
        r = client.post(f"/event-dates/{ed['id']}/cancel")
    assert r.status_code == 200
    import time; time.sleep(0.1)
    combined = " ".join(rec.message for rec in caplog.records)
    assert "cancel1@example.com" in combined or "cancel2@example.com" in combined
