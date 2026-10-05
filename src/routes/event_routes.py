"""API de eventos, reportes y ciclo de vida historico."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.models.event import Event
from src.services.event_catalog import EventCatalog, EventNotFound, EventValidationError


router = APIRouter(prefix="/events", tags=["Events"])
event_catalog = EventCatalog()


class EventPayload(BaseModel):
    identifier: int = Field(ge=1, le=999999)
    magnitude: float = Field(ge=-2, le=10)
    depth_km: float = Field(ge=0, le=700)
    x: float = Field(ge=0, le=1000)
    y: float = Field(ge=0, le=1000)
    occurred_at: datetime
    station: str = Field(min_length=1)
    revision: int = Field(default=1, ge=1)

    def to_event(self):
        return Event(
            identifier=self.identifier,
            magnitude=self.magnitude,
            depth_km=self.depth_km,
            x=self.x,
            y=self.y,
            occurred_at=self.occurred_at,
            station=self.station,
            revision=self.revision,
        )


def _error(error):
    if isinstance(error, EventNotFound):
        raise HTTPException(status_code=404, detail="El evento no existe.") from error
    raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventPayload):
    try:
        return event_catalog.response(event_catalog.create(payload.to_event()).identifier)
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.get("/tree")
def get_event_tree():
    return event_catalog.response()


@router.get("/history")
def get_event_history():
    return {"actions": len(event_catalog._history), "metrics": event_catalog.metrics()}


@router.get("/{identifier}")
def get_event(identifier: int):
    try:
        return event_catalog.response(identifier)
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.put("/{identifier}")
def update_event(identifier: int, payload: EventPayload):
    try:
        event = event_catalog.update(identifier, payload.to_event())
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.post("/{identifier}/review")
def review_event(identifier: int):
    try:
        event = event_catalog.review(identifier)
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.delete("/{identifier}")
def delete_event(identifier: int):
    try:
        event = event_catalog.delete(identifier)
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.post("/{identifier}/archive")
def archive_event_branch(identifier: int):
    try:
        event_catalog.archive_branch(identifier)
        return event_catalog.response()
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.post("/undo")
def undo_event_action():
    try:
        return event_catalog.undo()
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.post("/reports")
def process_event_report(payload: EventPayload):
    try:
        event_catalog.enqueue_report(payload.to_event())
        return {"status": "queued", "pending_reports": len(event_catalog._pending_reports)}
    except (EventNotFound, EventValidationError) as error:
        _error(error)


@router.post("/reports/process")
def process_pending_event_reports():
    try:
        results = event_catalog.process_pending_reports()
        for result in results:
            result["event"] = event_catalog.as_dict(result["event"])
        return {
            "status": "processed",
            "results": results,
            "data": event_catalog.response(),
        }
    except (EventNotFound, EventValidationError) as error:
        _error(error)

