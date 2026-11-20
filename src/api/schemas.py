"""
Pydantic v2 schemas for all API resources.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from src.db.models import CatalogStatus, RoleEnum, ShiftDuration


# ---------------------------------------------------------------------------
# Event schemas
# ---------------------------------------------------------------------------

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration: int
    min_primary_instructors: int
    min_secondary_instructors: int
    max_students: int
    location: str
    catalog_status: CatalogStatus = CatalogStatus.ACTIVE


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    min_primary_instructors: Optional[int] = None
    min_secondary_instructors: Optional[int] = None
    max_students: Optional[int] = None
    location: Optional[str] = None
    catalog_status: Optional[CatalogStatus] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    duration: int
    min_primary_instructors: int
    min_secondary_instructors: int
    max_students: int
    location: str
    catalog_status: CatalogStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class EventWithDatesResponse(EventResponse):
    event_dates: List["EventDateResponse"] = []


# ---------------------------------------------------------------------------
# EventDate schemas
# ---------------------------------------------------------------------------

class EventDateCreate(BaseModel):
    event_id: int
    date: datetime
    start_time: datetime
    end_time: datetime
    lead_instructor_id: Optional[int] = None
    registered_students: int = 0
    is_cancelled: bool = False


class EventDateUpdate(BaseModel):
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    lead_instructor_id: Optional[int] = None
    registered_students: Optional[int] = None


class EventDateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    date: datetime
    start_time: datetime
    end_time: datetime
    lead_instructor_id: Optional[int]
    registered_students: int
    is_cancelled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class EventDateWithAllocationsResponse(EventDateResponse):
    allocations: List["AllocationResponse"] = []


class StaffingStatusResponse(BaseModel):
    event_date_id: int
    lead_assigned: bool
    lead_instructor_id: Optional[int]
    primary_count: int
    min_primary_instructors: int
    primary_met: bool
    secondary_count: int
    min_secondary_instructors: int
    secondary_met: bool


# ---------------------------------------------------------------------------
# Instructor schemas
# ---------------------------------------------------------------------------

class InstructorCreate(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum


class InstructorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None


class InstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: RoleEnum
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InstructorWithAllocationsResponse(InstructorResponse):
    allocations: List["AllocationResponse"] = []


# ---------------------------------------------------------------------------
# Allocation schemas
# ---------------------------------------------------------------------------

class AllocationCreate(BaseModel):
    event_date_id: int
    instructor_id: int
    shift_duration: ShiftDuration
    role: RoleEnum


class AllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_date_id: int
    instructor_id: int
    shift_duration: ShiftDuration
    role: RoleEnum
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Availability schemas
# ---------------------------------------------------------------------------

class AvailabilityCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    is_available: bool = True


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instructor_id: int
    start_time: datetime
    end_time: datetime
    is_available: bool
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------

class InstructorHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    allocation_id: int
    event_date_id: int
    event_id: int
    event_title: str
    date: datetime
    start_time: datetime
    end_time: datetime
    role: RoleEnum
    shift_duration: ShiftDuration


class ClassScheduleItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_date_id: int
    event_id: int
    event_title: str
    location: str
    date: datetime
    start_time: datetime
    end_time: datetime
    registered_students: int
    lead_assigned: bool
    allocation_count: int


# Update forward references
EventWithDatesResponse.model_rebuild()
EventDateWithAllocationsResponse.model_rebuild()
InstructorWithAllocationsResponse.model_rebuild()
