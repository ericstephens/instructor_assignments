"""
Instructor Reservation System — FastAPI application entry point.
Endpoints are defined in routers/. This file wires them together.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Instructor Reservation System",
    version="0.1.0",
    description="API for managing instructor allocations to classes and events.",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
