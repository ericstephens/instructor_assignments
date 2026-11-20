"""
Allocations router — create with conflict checking, delete.

Business rules enforced here:
  1. No double-booking: instructor cannot be allocated to two EventDates whose
     time windows overlap.
  2. Lead uniqueness: each EventDate may have at most one lead allocation.
  3. ShiftDuration must be 4 or 8 (enforced by Pydantic enum in schemas.py).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.config import get_db
from src.db.models import Allocation, EventDate, RoleEnum
from ..schemas import AllocationCreate, AllocationResponse

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.get("", response_model=List[AllocationResponse])
def list_allocations(
    event_date_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Allocation)
    if event_date_id is not None:
        q = q.filter(Allocation.event_date_id == event_date_id)
    if instructor_id is not None:
        q = q.filter(Allocation.instructor_id == instructor_id)
    return q.all()


@router.post("", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(payload: AllocationCreate, db: Session = Depends(get_db)):
    # Fetch the target EventDate
    target_ed = db.query(EventDate).filter(EventDate.id == payload.event_date_id).first()
    if not target_ed:
        raise HTTPException(status_code=404, detail="EventDate not found")
    if target_ed.is_cancelled:
        raise HTTPException(status_code=409, detail="Cannot allocate to a cancelled EventDate")

    # Rule 1: No double-booking — check if instructor has any allocation on an
    # EventDate whose time window overlaps target_ed's window.
    # Overlap: existing.start_time < target.end_time AND existing.end_time > target.start_time
    overlapping_event_dates = (
        db.query(EventDate)
        .join(Allocation, Allocation.event_date_id == EventDate.id)
        .filter(
            Allocation.instructor_id == payload.instructor_id,
            EventDate.start_time < target_ed.end_time,
            EventDate.end_time > target_ed.start_time,
            EventDate.id != target_ed.id,  # exclude the same event date (handled by unique constraint)
        )
        .first()
    )
    if overlapping_event_dates:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Instructor {payload.instructor_id} is already allocated to an overlapping "
                f"event date (id={overlapping_event_dates.id})."
            ),
        )

    # Also check if there's already an allocation for this exact event_date + instructor combo
    existing_same = (
        db.query(Allocation)
        .filter(
            Allocation.event_date_id == payload.event_date_id,
            Allocation.instructor_id == payload.instructor_id,
        )
        .first()
    )
    if existing_same:
        raise HTTPException(
            status_code=409,
            detail="Instructor is already allocated to this event date.",
        )

    # Rule 2: Lead uniqueness — only one lead per EventDate
    if payload.role == RoleEnum.LEAD:
        existing_lead = (
            db.query(Allocation)
            .filter(
                Allocation.event_date_id == payload.event_date_id,
                Allocation.role == RoleEnum.LEAD,
            )
            .first()
        )
        if existing_lead:
            raise HTTPException(
                status_code=409,
                detail=f"EventDate {payload.event_date_id} already has a lead instructor assigned.",
            )

    alloc = Allocation(**payload.model_dump())
    db.add(alloc)
    db.commit()
    db.refresh(alloc)
    return alloc


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allocation(allocation_id: int, db: Session = Depends(get_db)):
    alloc = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")
    db.delete(alloc)
    db.commit()
