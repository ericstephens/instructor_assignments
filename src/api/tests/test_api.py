"""
API integration tests — real PostgreSQL, no mocking.
"""
from __future__ import annotations

import io

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


# ---------------------------------------------------------------------------
# Events — additional tests
# ---------------------------------------------------------------------------

def test_update_event(client):
    create_r = client.post("/events", json={
        "title": "Original Title",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room A",
    })
    assert create_r.status_code == 201
    event_id = create_r.json()["id"]

    r = client.put(f"/events/{event_id}", json={
        "title": "Updated Title",
        "location": "Room Z",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Updated Title"
    assert data["location"] == "Room Z"


def test_update_event_not_found(client):
    r = client.put("/events/999999", json={"title": "Ghost"})
    assert r.status_code == 404


def test_list_events_filter_by_status(client):
    client.post("/events", json={
        "title": "Active Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room A",
        "catalog_status": "active",
    })
    client.post("/events", json={
        "title": "Archived Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room A",
        "catalog_status": "archived",
    })

    r = client.get("/events?catalog_status=archived")
    assert r.status_code == 200
    results = r.json()
    assert all(e["catalog_status"] == "archived" for e in results)
    titles = [e["title"] for e in results]
    assert "Archived Event" in titles
    assert "Active Event" not in titles


def test_list_events_filter_by_location(client):
    client.post("/events", json={
        "title": "Event at Room-X",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room-X",
    })
    client.post("/events", json={
        "title": "Event at Room-Y",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room-Y",
    })

    r = client.get("/events?location=Room-X")
    assert r.status_code == 200
    results = r.json()
    assert all(e["location"] == "Room-X" for e in results)
    titles = [e["title"] for e in results]
    assert "Event at Room-X" in titles
    assert "Event at Room-Y" not in titles


def test_import_events_append(client):
    csv_content = (
        "title,description,duration,min_primary_instructors,"
        "min_secondary_instructors,max_students,location,catalog_status\n"
        "Import A,,1,1,0,20,Room A,active\n"
        "Import B,,2,1,1,30,Room B,active\n"
    )
    r = client.post(
        "/events/import",
        data={"mode": "append"},
        files={"file": ("events.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 201
    data = r.json()
    assert len(data) == 2
    titles = {e["title"] for e in data}
    assert titles == {"Import A", "Import B"}


def test_import_events_replace(client):
    # Pre-create an event that should be wiped out
    client.post("/events", json={
        "title": "Should Be Deleted",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Old Room",
    })

    csv_content = (
        "title,description,duration,min_primary_instructors,"
        "min_secondary_instructors,max_students,location,catalog_status\n"
        "Only This One,,1,1,0,15,New Room,active\n"
    )
    r = client.post(
        "/events/import",
        data={"mode": "replace"},
        files={"file": ("events.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 201

    list_r = client.get("/events")
    assert list_r.status_code == 200
    all_events = list_r.json()
    assert len(all_events) == 1
    assert all_events[0]["title"] == "Only This One"


# ---------------------------------------------------------------------------
# Event Dates — additional tests
# ---------------------------------------------------------------------------

def test_get_event_date_with_allocations(client):
    event_r = client.post("/events", json={
        "title": "Event for ED Alloc",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 20,
        "location": "Room A",
    })
    event_id = event_r.json()["id"]

    ed_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-06-01T00:00:00",
        "start_time": "2026-06-01T09:00:00",
        "end_time": "2026-06-01T17:00:00",
    })
    ed_id = ed_r.json()["id"]

    inst_r = client.post("/instructors", json={
        "name": "Frank Alloc",
        "email": "frank_alloc@example.com",
        "role": "primary",
    })
    inst_id = inst_r.json()["id"]

    alloc_r = client.post("/allocations", json={
        "event_date_id": ed_id,
        "instructor_id": inst_id,
        "shift_duration": 8,
        "role": "primary",
    })
    assert alloc_r.status_code == 201

    r = client.get(f"/event-dates/{ed_id}")
    assert r.status_code == 200
    data = r.json()
    assert "allocations" in data
    assert len(data["allocations"]) == 1
    assert data["allocations"][0]["instructor_id"] == inst_id


def test_update_event_date(client):
    event_r = client.post("/events", json={
        "title": "Event for ED Update",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 20,
        "location": "Room B",
    })
    event_id = event_r.json()["id"]

    ed_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-07-01T00:00:00",
        "start_time": "2026-07-01T09:00:00",
        "end_time": "2026-07-01T17:00:00",
        "registered_students": 5,
    })
    ed_id = ed_r.json()["id"]

    r = client.put(f"/event-dates/{ed_id}", json={"registered_students": 10})
    assert r.status_code == 200
    assert r.json()["registered_students"] == 10


def test_list_event_dates_filter_by_event(client):
    event1_r = client.post("/events", json={
        "title": "Event One",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room A",
    })
    event1_id = event1_r.json()["id"]

    event2_r = client.post("/events", json={
        "title": "Event Two",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 10,
        "location": "Room B",
    })
    event2_id = event2_r.json()["id"]

    client.post("/event-dates", json={
        "event_id": event1_id,
        "date": "2026-08-01T00:00:00",
        "start_time": "2026-08-01T09:00:00",
        "end_time": "2026-08-01T17:00:00",
    })
    client.post("/event-dates", json={
        "event_id": event2_id,
        "date": "2026-08-02T00:00:00",
        "start_time": "2026-08-02T09:00:00",
        "end_time": "2026-08-02T17:00:00",
    })

    r = client.get(f"/event-dates?event_id={event1_id}")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["event_id"] == event1_id


# ---------------------------------------------------------------------------
# Instructors — additional tests
# ---------------------------------------------------------------------------

def test_get_instructor(client):
    inst_r = client.post("/instructors", json={
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "role": "lead",
    })
    assert inst_r.status_code == 201
    inst_id = inst_r.json()["id"]

    r = client.get(f"/instructors/{inst_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == inst_id
    assert data["name"] == "Grace Hopper"
    assert "allocations" in data


def test_get_instructor_not_found(client):
    r = client.get("/instructors/999999")
    assert r.status_code == 404


def test_update_instructor(client):
    inst_r = client.post("/instructors", json={
        "name": "Old Name",
        "email": "update_inst@example.com",
        "role": "primary",
    })
    assert inst_r.status_code == 201
    inst_id = inst_r.json()["id"]

    r = client.put(f"/instructors/{inst_id}", json={"name": "New Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_add_availability(client):
    inst_r = client.post("/instructors", json={
        "name": "Henry Avail",
        "email": "henry_avail@example.com",
        "role": "secondary",
    })
    assert inst_r.status_code == 201
    inst_id = inst_r.json()["id"]

    r = client.post(f"/instructors/{inst_id}/availability", json={
        "start_time": "2026-09-01T08:00:00",
        "end_time": "2026-09-01T16:00:00",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["instructor_id"] == inst_id
    assert data["start_time"] == "2026-09-01T08:00:00"
    assert data["end_time"] == "2026-09-01T16:00:00"


def test_get_availability(client):
    inst_r = client.post("/instructors", json={
        "name": "Irene Available",
        "email": "irene_avail@example.com",
        "role": "primary",
    })
    assert inst_r.status_code == 201
    inst_id = inst_r.json()["id"]

    client.post(f"/instructors/{inst_id}/availability", json={
        "start_time": "2026-10-01T08:00:00",
        "end_time": "2026-10-01T12:00:00",
    })
    client.post(f"/instructors/{inst_id}/availability", json={
        "start_time": "2026-10-02T08:00:00",
        "end_time": "2026-10-02T12:00:00",
    })

    r = client.get(f"/instructors/{inst_id}/availability")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert all(a["instructor_id"] == inst_id for a in results)


# ---------------------------------------------------------------------------
# Allocations — additional tests
# ---------------------------------------------------------------------------

def test_list_allocations_filter(client):
    event_r = client.post("/events", json={
        "title": "Alloc Filter Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 20,
        "location": "Room A",
    })
    event_id = event_r.json()["id"]

    ed1_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-11-01T00:00:00",
        "start_time": "2026-11-01T09:00:00",
        "end_time": "2026-11-01T17:00:00",
    })
    ed1_id = ed1_r.json()["id"]

    ed2_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-11-02T00:00:00",
        "start_time": "2026-11-02T09:00:00",
        "end_time": "2026-11-02T17:00:00",
    })
    ed2_id = ed2_r.json()["id"]

    inst1_r = client.post("/instructors", json={
        "name": "Jack Filter",
        "email": "jack_filter@example.com",
        "role": "primary",
    })
    inst1_id = inst1_r.json()["id"]

    inst2_r = client.post("/instructors", json={
        "name": "Karen Filter",
        "email": "karen_filter@example.com",
        "role": "secondary",
    })
    inst2_id = inst2_r.json()["id"]

    alloc1_r = client.post("/allocations", json={
        "event_date_id": ed1_id,
        "instructor_id": inst1_id,
        "shift_duration": 8,
        "role": "primary",
    })
    assert alloc1_r.status_code == 201

    alloc2_r = client.post("/allocations", json={
        "event_date_id": ed2_id,
        "instructor_id": inst2_id,
        "shift_duration": 8,
        "role": "secondary",
    })
    assert alloc2_r.status_code == 201

    r = client.get(f"/allocations?event_date_id={ed1_id}")
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["event_date_id"] == ed1_id
    assert results[0]["instructor_id"] == inst1_id


def test_delete_allocation_not_found(client):
    r = client.delete("/allocations/999999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Reports — additional tests
# ---------------------------------------------------------------------------

def test_report_instructor_history(client):
    event_r = client.post("/events", json={
        "title": "History Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 20,
        "location": "Room A",
    })
    event_id = event_r.json()["id"]

    ed_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-12-01T00:00:00",
        "start_time": "2026-12-01T09:00:00",
        "end_time": "2026-12-01T17:00:00",
    })
    ed_id = ed_r.json()["id"]

    inst_r = client.post("/instructors", json={
        "name": "Leo History",
        "email": "leo_history@example.com",
        "role": "primary",
    })
    inst_id = inst_r.json()["id"]

    alloc_r = client.post("/allocations", json={
        "event_date_id": ed_id,
        "instructor_id": inst_id,
        "shift_duration": 8,
        "role": "primary",
    })
    assert alloc_r.status_code == 201
    alloc_id = alloc_r.json()["id"]

    r = client.get(f"/reports/instructor-history?instructor_id={inst_id}")
    assert r.status_code == 200
    results = r.json()
    assert len(results) >= 1
    match = next((item for item in results if item["allocation_id"] == alloc_id), None)
    assert match is not None
    assert match["event_title"] == "History Event"
    assert match["event_id"] == event_id


def test_report_class_schedule(client):
    event_r = client.post("/events", json={
        "title": "Schedule Event",
        "duration": 1,
        "min_primary_instructors": 1,
        "min_secondary_instructors": 0,
        "max_students": 20,
        "location": "Schedule Room",
    })
    event_id = event_r.json()["id"]

    ed_r = client.post("/event-dates", json={
        "event_id": event_id,
        "date": "2026-12-15T00:00:00",
        "start_time": "2026-12-15T09:00:00",
        "end_time": "2026-12-15T17:00:00",
    })
    ed_id = ed_r.json()["id"]

    r = client.get("/reports/class-schedule")
    assert r.status_code == 200
    results = r.json()
    match = next((item for item in results if item["event_date_id"] == ed_id), None)
    assert match is not None
    assert match["event_title"] == "Schedule Event"
    assert match["location"] == "Schedule Room"
