from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class RoleEnum(str, Enum):
    LEAD = "lead"
    PRIMARY = "primary"
    SECONDARY = "secondary"

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
    catalog_status = Column(String, nullable=False)  # active or archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event_dates = relationship("EventDate", back_populates="event")

class EventDate(Base):
    __tablename__ = "event_dates"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    lead_instructor_id = Column(Integer, ForeignKey("instructors.id"))
    registered_students = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="event_dates")
    lead_instructor = relationship("Instructor", foreign_keys=[lead_instructor_id])
    allocations = relationship("Allocation", back_populates="event_date")

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    allocations = relationship("Allocation", back_populates="instructor")
    availabilities = relationship("Availability", back_populates="instructor")

class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True)
    event_date_id = Column(Integer, ForeignKey("event_dates.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    shift_duration = Column(Integer, nullable=False)  # in hours
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event_date = relationship("EventDate", back_populates="allocations")
    instructor = relationship("Instructor", back_populates="allocations")

class Availability(Base):
    __tablename__ = "availabilities"

    id = Column(Integer, primary_key=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    instructor = relationship("Instructor", back_populates="availabilities")
