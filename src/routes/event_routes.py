"""Rutas HTTP de eventos, reportes y ciclo de vida historico."""

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from src.controllers import event_controller
from src.models.event import Event


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

    threshold_hours: float = Field(default=72, gt=0)


class OldArchivePayload(OldArchivePreviewPayload):
    """Confirmacion de una rama con la lista exacta mostrada al usuario."""

    expected_identifiers: list[int]


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
