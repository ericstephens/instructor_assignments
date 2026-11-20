"""
DB model integration tests — require a live PostgreSQL instance.
Run with: pytest src/db/tests/ (database must be started via manage.sh start)

Fixtures (db_engine, db_session) are provided by conftest.py.
"""
from datetime import datetime, timedelta, timezone

import pytest

from ..models import (
    Allocation,
    Availability,
    CatalogStatus,
    Event,
    EventDate,
    Instructor,
    RoleEnum,
    ShiftDuration,
)


# --- Event ---

def test_create_event(db_session):
    event = Event(
        title="Python Fundamentals",
        description="Intro to Python",
        duration=2,
        min_primary_instructors=1,
        min_secondary_instructors=1,
        max_students=20,
        location="Virtual",
        catalog_status=CatalogStatus.ACTIVE,
    )
    db_session.add(event)
    db_session.commit()
    assert event.id is not None
    assert event.catalog_status == CatalogStatus.ACTIVE


def test_event_archived_status(db_session):
    event = Event(
        title="Legacy Course",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=10,
        location="Room A",
        catalog_status=CatalogStatus.ARCHIVED,
    )
    db_session.add(event)
    db_session.commit()
    assert event.catalog_status == CatalogStatus.ARCHIVED


# --- Instructor ---

def test_create_instructor(db_session):
    instructor = Instructor(
        name="Jane Smith",
        email="jane.smith@example.com",
        role=RoleEnum.PRIMARY,
    )
    db_session.add(instructor)
    db_session.commit()
    assert instructor.id is not None


def test_instructor_email_unique(db_session):
    from sqlalchemy.exc import IntegrityError

    db_session.add(Instructor(name="A", email="dupe@example.com", role=RoleEnum.PRIMARY))
    db_session.commit()
    db_session.add(Instructor(name="B", email="dupe@example.com", role=RoleEnum.SECONDARY))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# --- EventDate ---

def test_create_event_date(db_session):
    event = Event(
        title="Advanced Python",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=1,
        max_students=15,
        location="Virtual",
        catalog_status=CatalogStatus.ACTIVE,
    )
    db_session.add(event)
    db_session.commit()

    now = datetime.now(timezone.utc)
    event_date = EventDate(
        event_id=event.id,
        date=now,
        start_time=now,
        end_time=now + timedelta(hours=8),
    )
    db_session.add(event_date)
    db_session.commit()
    assert event_date.id is not None
    assert event_date.lead_instructor_id is None


# --- Allocation ---

def test_create_allocation(db_session):
    event = Event(
        title="Data Science",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=25,
        location="Room B",
        catalog_status=CatalogStatus.ACTIVE,
    )
    instructor = Instructor(name="Bob Lee", email="bob.lee@example.com", role=RoleEnum.PRIMARY)
    db_session.add_all([event, instructor])
    db_session.commit()

    now = datetime.now(timezone.utc)
    event_date = EventDate(
        event_id=event.id,
        date=now,
        start_time=now,
        end_time=now + timedelta(hours=8),
    )
    db_session.add(event_date)
    db_session.commit()

    allocation = Allocation(
        event_date_id=event_date.id,
        instructor_id=instructor.id,
        shift_duration=ShiftDuration.FULL_DAY,
        role=RoleEnum.PRIMARY,
    )
    db_session.add(allocation)
    db_session.commit()
    assert allocation.id is not None


def test_allocation_no_double_booking(db_session):
    """Same instructor cannot be allocated to same event_date twice."""
    from sqlalchemy.exc import IntegrityError

    event = Event(
        title="No Double Book",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=10,
        location="Virtual",
        catalog_status=CatalogStatus.ACTIVE,
    )
    instructor = Instructor(name="Carol Day", email="carol.day@example.com", role=RoleEnum.PRIMARY)
    db_session.add_all([event, instructor])
    db_session.commit()

    now = datetime.now(timezone.utc)
    event_date = EventDate(
        event_id=event.id,
        date=now,
        start_time=now,
        end_time=now + timedelta(hours=8),
    )
    db_session.add(event_date)
    db_session.commit()

    db_session.add(Allocation(
        event_date_id=event_date.id,
        instructor_id=instructor.id,
        shift_duration=ShiftDuration.FULL_DAY,
        role=RoleEnum.PRIMARY,
    ))
    db_session.commit()

    db_session.add(Allocation(
        event_date_id=event_date.id,
        instructor_id=instructor.id,
        shift_duration=ShiftDuration.HALF_DAY,
        role=RoleEnum.SECONDARY,
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# --- Availability ---

def test_create_availability(db_session):
    instructor = Instructor(name="Eve Torres", email="eve.torres@example.com", role=RoleEnum.SECONDARY)
    db_session.add(instructor)
    db_session.commit()

    now = datetime.now(timezone.utc)
    avail = Availability(
        instructor_id=instructor.id,
        start_time=now,
        end_time=now + timedelta(hours=8),
        is_available=True,
    )
    db_session.add(avail)
    db_session.commit()
    assert avail.id is not None
