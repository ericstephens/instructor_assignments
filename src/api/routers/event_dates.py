"""
EventDates router — CRUD + staffing status.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.config import get_db
from src.db.models import Allocation, Event, EventDate, RoleEnum
from ..schemas import (
    EventDateCreate,
    EventDateResponse,
    EventDateUpdate,
    EventDateWithAllocationsResponse,
    StaffingStatusResponse,
)

router = APIRouter(prefix="/event-dates", tags=["event-dates"])


@router.get("", response_model=List[EventDateResponse])
def list_event_dates(
    event_id: Optional[int] = None,
    date: Optional[datetime] = None,
    instructor_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(EventDate)
    if event_id is not None:
        q = q.filter(EventDate.event_id == event_id)
    if date is not None:
        q = q.filter(EventDate.date == date)
    if instructor_id is not None:
        q = q.join(Allocation).filter(Allocation.instructor_id == instructor_id)
    return q.all()


@router.get("/{event_date_id}", response_model=EventDateWithAllocationsResponse)
def get_event_date(event_date_id: int, db: Session = Depends(get_db)):
    ed = db.query(EventDate).filter(EventDate.id == event_date_id).first()
    if not ed:
        raise HTTPException(status_code=404, detail="EventDate not found")
    return ed


@router.post("", response_model=EventDateResponse, status_code=status.HTTP_201_CREATED)
def create_event_date(payload: EventDateCreate, db: Session = Depends(get_db)):
    # Verify event exists
    event = db.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    ed = EventDate(**payload.model_dump())
    db.add(ed)
    db.commit()
    db.refresh(ed)
    return ed


@router.put("/{event_date_id}", response_model=EventDateResponse)
def update_event_date(event_date_id: int, payload: EventDateUpdate, db: Session = Depends(get_db)):
    ed = db.query(EventDate).filter(EventDate.id == event_date_id).first()
    if not ed:
        raise HTTPException(status_code=404, detail="EventDate not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ed, field, value)
    db.commit()
    db.refresh(ed)
    return ed


@router.get("/{event_date_id}/staffing-status", response_model=StaffingStatusResponse)
def staffing_status(event_date_id: int, db: Session = Depends(get_db)):
    ed = db.query(EventDate).filter(EventDate.id == event_date_id).first()
    if not ed:
        raise HTTPException(status_code=404, detail="EventDate not found")

    event = db.query(Event).filter(Event.id == ed.event_id).first()

    allocations = db.query(Allocation).filter(Allocation.event_date_id == event_date_id).all()

    lead_alloc = next((a for a in allocations if a.role == RoleEnum.LEAD), None)
    primary_count = sum(1 for a in allocations if a.role == RoleEnum.PRIMARY)
    secondary_count = sum(1 for a in allocations if a.role == RoleEnum.SECONDARY)

    return StaffingStatusResponse(
        event_date_id=event_date_id,
        lead_assigned=lead_alloc is not None,
        lead_instructor_id=lead_alloc.instructor_id if lead_alloc else None,
        primary_count=primary_count,
        min_primary_instructors=event.min_primary_instructors,
        primary_met=primary_count >= event.min_primary_instructors,
        secondary_count=secondary_count,
        min_secondary_instructors=event.min_secondary_instructors,
        secondary_met=secondary_count >= event.min_secondary_instructors,
    )
