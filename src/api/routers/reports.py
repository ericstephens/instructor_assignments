"""
Reports router — instructor history, class schedule.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.config import get_db
from src.db.models import Allocation, Event, EventDate, Instructor
from ..schemas import ClassScheduleItem, InstructorHistoryItem

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/instructor-history", response_model=List[InstructorHistoryItem])
def instructor_history(
    instructor_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")

    q = (
        db.query(Allocation, EventDate, Event)
        .join(EventDate, Allocation.event_date_id == EventDate.id)
        .join(Event, EventDate.event_id == Event.id)
        .filter(Allocation.instructor_id == instructor_id)
    )
    if date_from:
        q = q.filter(EventDate.date >= date_from)
    if date_to:
        q = q.filter(EventDate.date <= date_to)

    results = []
    for alloc, ed, event in q.all():
        results.append(
            InstructorHistoryItem(
                allocation_id=alloc.id,
                event_date_id=ed.id,
                event_id=event.id,
                event_title=event.title,
                date=ed.date,
                start_time=ed.start_time,
                end_time=ed.end_time,
                role=alloc.role,
                shift_duration=alloc.shift_duration,
            )
        )
    return results


@router.get("/class-schedule", response_model=List[ClassScheduleItem])
def class_schedule(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(EventDate, Event)
        .join(Event, EventDate.event_id == Event.id)
    )
    if date_from:
        q = q.filter(EventDate.date >= date_from)
    if date_to:
        q = q.filter(EventDate.date <= date_to)
    if location:
        q = q.filter(Event.location == location)

    results = []
    for ed, event in q.all():
        alloc_count = (
            db.query(Allocation).filter(Allocation.event_date_id == ed.id).count()
        )
        results.append(
            ClassScheduleItem(
                event_date_id=ed.id,
                event_id=event.id,
                event_title=event.title,
                location=event.location,
                date=ed.date,
                start_time=ed.start_time,
                end_time=ed.end_time,
                registered_students=ed.registered_students,
                lead_assigned=ed.lead_instructor_id is not None,
                allocation_count=alloc_count,
            )
        )
    return results
