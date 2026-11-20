"""
Instructor Reservation System — FastAPI application entry point.
Endpoints are defined in routers/. This file wires them together.
"""
from fastapi import FastAPI

from .routers.allocations import router as allocations_router
from .routers.event_dates import router as event_dates_router
from .routers.events import router as events_router
from .routers.instructors import router as instructors_router
from .routers.reports import router as reports_router

app = FastAPI(
    title="Instructor Reservation System",
    version="0.1.0",
    description="API for managing instructor allocations to classes and events.",
)

app.include_router(events_router)
app.include_router(event_dates_router)
app.include_router(instructors_router)
app.include_router(allocations_router)
app.include_router(reports_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
