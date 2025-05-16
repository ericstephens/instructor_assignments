import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from ..config import Base
from ..models import Event, EventDate, Instructor, Allocation, Availability, RoleEnum

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_create_event(test_db):
    event = Event(
        title="Test Event",
        description="A test event",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=1,
        max_students=20,
        location="Virtual",
        catalog_status="active"
    )
    test_db.add(event)
    test_db.commit()
    assert event.id is not None

def test_create_instructor(test_db):
    instructor = Instructor(
        name="Test Instructor",
        email="test@example.com",
        role=RoleEnum.PRIMARY
    )
    test_db.add(instructor)
    test_db.commit()
    assert instructor.id is not None

def test_create_event_date(test_db):
    event = Event(
        title="Test Event",
        duration=1,
        min_primary_instructors=1,
        min_secondary_instructors=1,
        max_students=20,
        location="Virtual",
        catalog_status="active"
    )
    test_db.add(event)
    test_db.commit()

    event_date = EventDate(
        event_id=event.id,
        date=datetime.now(),
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=8)
    )
    test_db.add(event_date)
    test_db.commit()
    assert event_date.id is not None
