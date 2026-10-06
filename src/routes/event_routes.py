"""Rutas HTTP de eventos, reportes y ciclo de vida historico."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.controllers import event_controller
from src.models.event import Event
from src.models.zone import Zone


router = APIRouter(prefix="/events", tags=["Events"])


class EventPayload(BaseModel):
    """Contrato HTTP con los datos necesarios para crear o reportar eventos."""

    identifier: int = Field(ge=1, le=999999)
    magnitude: float = Field(ge=-2, le=10)
    depth_km: float = Field(ge=0, le=700)
    x: float = Field(ge=0, le=1000)
    y: float = Field(ge=0, le=1000)
    occurred_at: datetime
    station: str = Field(min_length=1)
    revision: int = Field(default=1, ge=1)

    def to_event(self):
        """Convierte el payload validado por FastAPI en un evento de dominio."""
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


class ReplicaPayload(BaseModel):
    """Parametros HTTP para buscar replicas cercanas de un evento."""

    r: int = Field(ge=0)
    w: int = Field(ge=0)


class ModePayload(BaseModel):
    stress: bool


class OldArchivePreviewPayload(BaseModel):
    """Umbral configurable para buscar ramas de eventos antiguos."""

    threshold_hours: float | None = Field(default=None, gt=0)


class OldArchivePayload(OldArchivePreviewPayload):
    """Confirmacion de una rama con la lista exacta mostrada al usuario."""

    expected_identifiers: list[int]


class ZonePayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    min_x: float = Field(ge=0, le=1000)
    max_x: float = Field(ge=0, le=1000)
    min_y: float = Field(ge=0, le=1000)
    max_y: float = Field(ge=0, le=1000)
    populated: bool = False

    def to_zone(self):
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise HTTPException(status_code=422, detail="Los limites de zona no son validos.")
        return Zone(**self.model_dump())


class ScenarioParametersPayload(BaseModel):
    archive_threshold_hours: float | None = Field(default=None, gt=0)
    zones: list[ZonePayload] | None = None


class ClockAdvancePayload(BaseModel):
    seconds: float = Field(ge=0)


class VersionPayload(BaseModel):
    name: str = Field(min_length=1, max_length=60)


@router.get("/analysis/pending")
def query_pending_top(k: int = Query(gt=0)):
    return event_controller.query_pending_top(k)


@router.get("/analysis/magnitude")
def query_magnitude_range(
    minimum: float = Query(ge=-2, le=10),
    maximum: float = Query(ge=-2, le=10),
):
    if minimum > maximum:
        raise HTTPException(status_code=422, detail="minimum debe ser menor o igual a maximum")
    return event_controller.query_magnitude_range(minimum, maximum)


@router.get("/analysis/depth")
def query_shallow_depth(
    maximum_depth: float = Query(ge=0, le=700),
    start: datetime = Query(),
    end: datetime = Query(),
):
    start = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start.astimezone(timezone.utc)
    end = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end.astimezone(timezone.utc)
    if start > end:
        raise HTTPException(status_code=422, detail="start debe ser anterior o igual a end")
    return event_controller.query_shallow_depth(maximum_depth, start, end)


@router.get("/analysis/associations/{identifier}")
def query_associations(identifier: int):
    return event_controller.query_associations(identifier)


@router.get("/analysis/costly-high-priority")
def query_costly_high_priority(depth_limit: int = Query(ge=0)):
    return event_controller.query_costly_high_priority(depth_limit)


@router.get("/analysis/compare")
def compare_event_structures():
    return event_controller.compare_event_structures()


@router.get("/scenario")
def get_scenario():
    return event_controller.get_scenario()


@router.put("/scenario/parameters")
def update_scenario_parameters(payload: ScenarioParametersPayload):
    zones = None if payload.zones is None else [zone.to_zone() for zone in payload.zones]
    return event_controller.update_scenario_parameters(
        payload.archive_threshold_hours,
        zones,
    )


@router.post("/clock/advance")
def advance_scenario_clock(payload: ClockAdvancePayload):
    return event_controller.advance_scenario_clock(payload.seconds)


@router.get("/export")
def export_scenario_state():
    return event_controller.export_scenario_state()


@router.post("/import")
def load_scenario_state(payload: dict):
    return event_controller.load_scenario_state(payload)


@router.get("/versions")
def list_scenario_versions():
    return event_controller.list_scenario_versions()


@router.post("/versions", status_code=status.HTTP_201_CREATED)
def save_scenario_version(payload: VersionPayload):
    return event_controller.save_scenario_version(payload.name)


@router.post("/versions/{name}/restore")
def restore_scenario_version(name: str):
    return event_controller.restore_scenario_version(name)


@router.delete("/versions/{name}")
def delete_scenario_version(name: str):
    return event_controller.delete_scenario_version(name)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventPayload):
    """Crea un evento y devuelve el arbol AVL de eventos actualizado."""
    return event_controller.create_event(payload)


@router.get("/tree")
def get_event_tree():
    """Consulta la jerarquia AVL de eventos activos."""
    return event_controller.get_event_tree()


@router.get("/history")
def get_event_history():
    """Consulta conteos de historial y metricas del catalogo."""
    return event_controller.get_event_history()


@router.get("/mode")
def get_event_mode():
    return event_controller.get_event_mode()


@router.get("/verify")
def verify_event_structure():
    """Audita estructura y referencias tanto en modo normal como en estrés."""
    return event_controller.verify_event_structure()


@router.post("/mode")
def set_event_mode(payload: ModePayload):
    return event_controller.set_event_mode(payload.stress)


@router.post("/recover")
def recover_event_tree():
    return event_controller.recover_event_tree()


@router.post("/archive/old/preview")
def preview_old_event_branch_archive(payload: OldArchivePreviewPayload):
    """Devuelve candidatos y justificacion sin cambiar el estado del catalogo."""
    return event_controller.preview_old_branch_archive(payload.threshold_hours)


@router.post("/archive/old")
def archive_old_event_branch(payload: OldArchivePayload):
    """Archiva la rama antigua confirmada en su previsualizacion."""
    return event_controller.archive_old_branch(
        payload.threshold_hours,
        payload.expected_identifiers,
    )


@router.get("/{identifier}")
def get_event(identifier: int):
    """Consulta un evento por identificador."""
    return event_controller.get_event(identifier)


@router.put("/{identifier}")
def update_event(identifier: int, payload: EventPayload):
    """Actualiza los datos editables de un evento activo."""
    return event_controller.update_event(identifier, payload)


@router.post("/{identifier}/review")
def review_event(identifier: int):
    """Marca un evento activo como revisado."""
    return event_controller.review_event(identifier)


@router.post("/{identifier}/replicas")
def find_event_replicas(identifier: int, payload: ReplicaPayload):
    """Busca eventos activos o archivados cercanos al evento indicado."""
    return event_controller.find_event_replicas(identifier, payload)


@router.delete("/{identifier}")
def delete_event(identifier: int):
    """Elimina logicamente un evento activo."""
    return event_controller.delete_event(identifier)


@router.post("/{identifier}/archive")
def archive_event_branch(identifier: int):
    """Archiva la rama AVL que inicia en el evento indicado."""
    return event_controller.archive_event_branch(identifier)


@router.post("/undo")
def undo_event_action():
    """Deshace la ultima accion registrada en el catalogo."""
    return event_controller.undo_event_action()


@router.post("/reports")
def process_event_report(payload: EventPayload):
    """Encola un reporte para procesarlo posteriormente."""
    return event_controller.enqueue_event_report(payload)


@router.post("/reports/process")
def process_pending_event_reports():
    """Procesa todos los reportes pendientes en orden de llegada."""
    return event_controller.process_pending_event_reports()


@router.post("/reports/process/step")
def process_next_event_report():
    """Procesa exactamente un reporte FIFO."""
    return event_controller.process_next_event_report()
