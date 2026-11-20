"""
Instructor Reservation System — FastAPI application entry point.
Endpoints are defined in routers/. This file wires them together.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.allocations import router as allocations_router
from .routers.auth import router as auth_router
from .routers.event_dates import router as event_dates_router
from .routers.events import router as events_router
from .routers.instructors import router as instructors_router
from .routers.reports import router as reports_router

app = FastAPI(
    title="Instructor Reservation System",
    version="0.1.0",
    description="API for managing instructor allocations to classes and events.",
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(event_dates_router)
app.include_router(instructors_router)
app.include_router(allocations_router)
app.include_router(reports_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
