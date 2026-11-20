"""
Instructors router — CRUD + availability.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.config import get_db
from src.db.models import Availability, Instructor
from ..schemas import (
    AvailabilityCreate,
    AvailabilityResponse,
    InstructorCreate,
    InstructorResponse,
    InstructorUpdate,
    InstructorWithAllocationsResponse,
)

router = APIRouter(prefix="/instructors", tags=["instructors"])


@router.get("", response_model=List[InstructorResponse])
def list_instructors(db: Session = Depends(get_db)):
    return db.query(Instructor).all()


@router.get("/{instructor_id}", response_model=InstructorWithAllocationsResponse)
def get_instructor(instructor_id: int, db: Session = Depends(get_db)):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return inst


@router.post("", response_model=InstructorResponse, status_code=status.HTTP_201_CREATED)
def create_instructor(payload: InstructorCreate, db: Session = Depends(get_db)):
    existing = db.query(Instructor).filter(Instructor.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Instructor with this email already exists")
    inst = Instructor(**payload.model_dump())
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


@router.put("/{instructor_id}", response_model=InstructorResponse)
def update_instructor(instructor_id: int, payload: InstructorUpdate, db: Session = Depends(get_db)):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inst, field, value)
    db.commit()
    db.refresh(inst)
    return inst


@router.get("/{instructor_id}/availability", response_model=List[AvailabilityResponse])
def get_availability(instructor_id: int, db: Session = Depends(get_db)):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    return db.query(Availability).filter(Availability.instructor_id == instructor_id).all()


@router.post(
    "/{instructor_id}/availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_availability(
    instructor_id: int,
    payload: AvailabilityCreate,
    db: Session = Depends(get_db),
):
    inst = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instructor not found")
    avail = Availability(instructor_id=instructor_id, **payload.model_dump())
    db.add(avail)
    db.commit()
    db.refresh(avail)
    return avail
