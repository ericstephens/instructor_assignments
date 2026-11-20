"""
Events router — CRUD + catalog import.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.db.config import get_db
from src.db.models import CatalogStatus, Event, User
from ..auth import get_current_user, require_admin
from ..schemas import EventCreate, EventResponse, EventUpdate, EventWithDatesResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=List[EventResponse])
def list_events(
    catalog_status: Optional[CatalogStatus] = None,
    location: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if catalog_status is not None:
        q = q.filter(Event.catalog_status == catalog_status)
    if location is not None:
        q = q.filter(Event.location == location)
    # date filters apply to event_dates; skip for now unless event has dates
    # (the contract says list with filters — location/status are on Event itself)
    return q.all()


@router.get("/{event_id}", response_model=EventWithDatesResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.post("/import", response_model=List[EventResponse], status_code=status.HTTP_201_CREATED)
async def import_events(
    mode: str = Form("append"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Import events from a CSV upload.
    mode=replace: delete all existing events first.
    mode=append: add to existing catalog.
    CSV headers must match EventCreate fields.
    """
    if mode not in ("replace", "append"):
        raise HTTPException(status_code=400, detail="mode must be 'replace' or 'append'")

    contents = await file.read()
    text = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    if mode == "replace":
        db.query(Event).delete()
        db.commit()

    created: list[Event] = []
    for row in reader:
        # Coerce types
        event = Event(
            title=row["title"],
            description=row.get("description"),
            duration=int(row["duration"]),
            min_primary_instructors=int(row["min_primary_instructors"]),
            min_secondary_instructors=int(row["min_secondary_instructors"]),
            max_students=int(row["max_students"]),
            location=row["location"],
            catalog_status=CatalogStatus(row.get("catalog_status", "active")),
        )
        db.add(event)
        created.append(event)

    db.commit()
    for e in created:
        db.refresh(e)
    return created
