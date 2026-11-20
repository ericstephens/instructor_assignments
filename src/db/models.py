import enum
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .config import Base


class RoleEnum(str, enum.Enum):
    LEAD = "lead"
    PRIMARY = "primary"
    SECONDARY = "secondary"


class ShiftDuration(int, enum.Enum):
    HALF_DAY = 4
    FULL_DAY = 8


class CatalogStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    duration = Column(Integer, nullable=False)  # in days
    min_primary_instructors = Column(Integer, nullable=False)
    min_secondary_instructors = Column(Integer, nullable=False)
    max_students = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    catalog_status = Column(Enum(CatalogStatus), nullable=False, default=CatalogStatus.ACTIVE)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    event_dates = relationship("EventDate", back_populates="event", cascade="all, delete-orphan")


class EventDate(Base):
    __tablename__ = "event_dates"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    lead_instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    registered_students = Column(Integer, default=0)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    event = relationship("Event", back_populates="event_dates")
    lead_instructor = relationship("Instructor", foreign_keys=[lead_instructor_id])
    allocations = relationship("Allocation", back_populates="event_date", cascade="all, delete-orphan")


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    allocations = relationship("Allocation", back_populates="instructor", cascade="all, delete-orphan")
    availabilities = relationship("Availability", back_populates="instructor", cascade="all, delete-orphan")


class Allocation(Base):
    __tablename__ = "allocations"
    __table_args__ = (
        # Prevent double-booking: one instructor per event_date
        UniqueConstraint("event_date_id", "instructor_id", name="uq_allocation_event_date_instructor"),
    )

    id = Column(Integer, primary_key=True)
    event_date_id = Column(Integer, ForeignKey("event_dates.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    shift_duration = Column(Enum(ShiftDuration), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    event_date = relationship("EventDate", back_populates="allocations")
    instructor = relationship("Instructor", back_populates="allocations")


class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    instructor = relationship("Instructor", back_populates="availabilities")
