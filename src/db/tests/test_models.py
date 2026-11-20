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


# --- Cascade delete ---

def test_cascade_delete_event(db_session):
    event = Event(
        title="Cascade Test",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=10,
        location="Virtual",
        catalog_status=CatalogStatus.ACTIVE,
    )
    db_session.add(event)
    db_session.commit()

    now = datetime.now(timezone.utc)
    ed1 = EventDate(
        event_id=event.id,
        date=now,
        start_time=now,
        end_time=now + timedelta(hours=8),
    )
    ed2 = EventDate(
        event_id=event.id,
        date=now + timedelta(days=1),
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=8),
    )
    db_session.add_all([ed1, ed2])
    db_session.commit()

    ed1_id = ed1.id
    ed2_id = ed2.id

    db_session.delete(event)
    db_session.commit()

    assert db_session.get(EventDate, ed1_id) is None
    assert db_session.get(EventDate, ed2_id) is None


# --- Lead instructor assignment ---

def test_lead_instructor_assignment(db_session):
    event = Event(
        title="Lead Instructor Test",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=15,
        location="Room C",
        catalog_status=CatalogStatus.ACTIVE,
    )
    instructor = Instructor(
        name="Frank Rivera",
        email="frank.rivera@example.com",
        role=RoleEnum.LEAD,
    )
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

    event_date.lead_instructor_id = instructor.id
    db_session.commit()

    db_session.expire(event_date)
    fetched = db_session.get(EventDate, event_date.id)
    assert fetched.lead_instructor_id == instructor.id
    assert fetched.lead_instructor.name == instructor.name


# --- Availability blocked ---

def test_availability_blocked(db_session):
    instructor = Instructor(
        name="Grace Kim",
        email="grace.kim@example.com",
        role=RoleEnum.SECONDARY,
    )
    db_session.add(instructor)
    db_session.commit()

    now = datetime.now(timezone.utc)
    avail_open = Availability(
        instructor_id=instructor.id,
        start_time=now,
        end_time=now + timedelta(hours=4),
        is_available=True,
    )
    avail_blocked = Availability(
        instructor_id=instructor.id,
        start_time=now + timedelta(hours=4),
        end_time=now + timedelta(hours=8),
        is_available=False,
    )
    db_session.add_all([avail_open, avail_blocked])
    db_session.commit()

    results = (
        db_session.query(Availability)
        .filter(Availability.instructor_id == instructor.id)
        .all()
    )
    assert len(results) == 2
    is_available_values = {r.id: r.is_available for r in results}
    assert is_available_values[avail_open.id] is True
    assert is_available_values[avail_blocked.id] is False


# --- Half-day shift duration ---

def test_half_day_shift_duration(db_session):
    event = Event(
        title="Half Day Course",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=0,
        max_students=12,
        location="Room D",
        catalog_status=CatalogStatus.ACTIVE,
    )
    instructor = Instructor(
        name="Henry Park",
        email="henry.park@example.com",
        role=RoleEnum.PRIMARY,
    )
    db_session.add_all([event, instructor])
    db_session.commit()

    now = datetime.now(timezone.utc)
    event_date = EventDate(
        event_id=event.id,
        date=now,
        start_time=now,
        end_time=now + timedelta(hours=4),
    )
    db_session.add(event_date)
    db_session.commit()

    allocation = Allocation(
        event_date_id=event_date.id,
        instructor_id=instructor.id,
        shift_duration=ShiftDuration.HALF_DAY,
        role=RoleEnum.PRIMARY,
    )
    db_session.add(allocation)
    db_session.commit()

    db_session.expire(allocation)
    fetched = db_session.get(Allocation, allocation.id)
    assert fetched.shift_duration == ShiftDuration.HALF_DAY


# --- Event dates relationship ---

def test_event_dates_relationship(db_session):
    event = Event(
        title="Multi-Date Event",
        duration=3,
        min_primary_instructors=1,
        min_secondary_instructors=1,
        max_students=20,
        location="Virtual",
        catalog_status=CatalogStatus.ACTIVE,
    )
    db_session.add(event)
    db_session.commit()

    now = datetime.now(timezone.utc)
    for i in range(3):
        ed = EventDate(
            event_id=event.id,
            date=now + timedelta(days=i),
            start_time=now + timedelta(days=i),
            end_time=now + timedelta(days=i, hours=8),
        )
        db_session.add(ed)
    db_session.commit()

    db_session.expire(event)
    fetched_event = db_session.get(Event, event.id)
    assert len(fetched_event.event_dates) == 3
    assert all(ed.event_id == event.id for ed in fetched_event.event_dates)
