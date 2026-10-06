"""Controlador HTTP para el catalogo de eventos sismicos."""

import os
from pathlib import Path
from datetime import datetime, timezone

from fastapi import HTTPException

from src.services.eventCatalog_Service import EventCatalog
from src.services.eventCatalog.exceptions import EventNotFound, EventValidationError
from src.services.eventCatalog.persistence import JsonStateRepository
from src.models.simulation_clock import SimulationClock


state_path = Path(os.environ.get(
    "SISMOLAB_STATE_PATH",
    Path(__file__).resolve().parents[2] / "data" / "sismolab-state.json",
))
event_catalog = EventCatalog(
    clock=SimulationClock(datetime.now(timezone.utc)),
    repository=JsonStateRepository(state_path),
)


def _handle_event_error(error):
    """Convierte errores de dominio del catalogo en respuestas HTTP."""
    if isinstance(error, EventNotFound):
        raise HTTPException(status_code=404, detail="El evento no existe.") from error
    raise HTTPException(status_code=409, detail=str(error)) from error


def create_event(payload):
    """Crea un evento desde el payload HTTP y devuelve el estado del catalogo."""
    try:
        event = event_catalog.create(payload.to_event())
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def get_event_tree():
    """Devuelve el arbol AVL de eventos activos y sus metricas."""
    return event_catalog.response()


def get_event_history():
    """Devuelve conteos del historial de acciones y metricas actuales."""
    return {
        "actions": event_catalog.history_count(),
        "metrics": event_catalog.metrics(),
        "explanations": event_catalog.history_report(),
    }


def get_event_mode():
    return event_catalog.status()


def verify_event_structure():
    return event_catalog.verify_structure()


def set_event_mode(stress):
    try:
        return event_catalog.set_stress_mode(stress)
    except EventValidationError as error:
        _handle_event_error(error)


def recover_event_tree():
    try:
        return event_catalog.recover()
    except EventValidationError as error:
        _handle_event_error(error)


def get_event(identifier):
    """Busca un evento por identificador en activos, archivados o eliminados."""
    try:
        return event_catalog.response(identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def update_event(identifier, payload):
    """Actualiza un evento activo manteniendo inmutable su identificador."""
    try:
        event = event_catalog.update(identifier, payload.to_event())
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def review_event(identifier):
    """Marca un evento activo como revisado y devuelve su arbol actualizado."""
    try:
        event = event_catalog.review(identifier)
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def delete_event(identifier):
    """Elimina logicamente un evento activo y lo retira del AVL."""
    try:
        event = event_catalog.delete(identifier)
        return event_catalog.response(event.identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def archive_event_branch(identifier):
    """Archiva la rama AVL que inicia en el evento indicado."""
    try:
        event_catalog.archive_branch(identifier)
        return event_catalog.response()
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def preview_old_branch_archive(threshold_hours):
    """Previsualiza la seleccion automatica sin registrar una mutacion."""
    try:
        return event_catalog.preview_old_branch_archive(threshold_hours)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def archive_old_branch(threshold_hours, expected_identifiers):
    """Confirma la seleccion antigua y devuelve su resumen y arbol actualizado."""
    try:
        archive = event_catalog.archive_old_branch(
            threshold_hours,
            expected_identifiers,
        )
        return {"archive": archive, "data": event_catalog.response()}
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def undo_event_action():
    """Deshace la ultima accion registrada en el catalogo de eventos."""
    try:
        return event_catalog.undo()
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def enqueue_event_report(payload):
    """Agrega un reporte de evento a la cola pendiente."""
    try:
        event_catalog.enqueue_report(payload.to_event())
        return {
            "status": "queued",
            "pending_reports": event_catalog.pending_reports_count(),
            "queue": event_catalog.pending_reports(),
        }
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def process_pending_event_reports():
    """Procesa la cola de reportes y devuelve resultados serializados."""
    try:
        results = event_catalog.process_pending_reports()
        for result in results:
            result["event"] = event_catalog.as_dict(result["event"])
        return {
            "status": "processed",
            "results": results,
            "queue": event_catalog.pending_reports(),
            "data": event_catalog.response(),
        }
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def process_next_event_report():
    """Procesa un solo reporte FIFO y devuelve su traza completa."""
    try:
        result = event_catalog.process_next_report()
        if result is None:
            return {
                "status": "idle",
                "result": None,
                "queue": [],
                "data": event_catalog.response(),
            }
        result["event"] = event_catalog.as_dict(result["event"])
        return {
            "status": "processed",
            "result": result,
            "queue": event_catalog.pending_reports(),
            "data": event_catalog.response(),
        }
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def find_event_replicas(identifier, payload):
    """Busca replicas cercanas a un evento activo o archivado."""
    try:
        return event_catalog.find_replicas(identifier, payload.r, payload.w)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def query_pending_top(k):
    return event_catalog.query_pending_top(k)


def query_magnitude_range(minimum, maximum):
    return event_catalog.query_magnitude_range(minimum, maximum)


def query_shallow_depth(maximum_depth, start, end):
    return event_catalog.query_shallow_depth(maximum_depth, start, end)


def query_associations(identifier):
    try:
        return event_catalog.query_associations(identifier)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def query_costly_high_priority(depth_limit):
    return event_catalog.query_costly_high_priority(depth_limit)


def compare_event_structures():
    return event_catalog.compare_structures()


def get_scenario():
    return event_catalog.scenario()


def update_scenario_parameters(archive_threshold_hours=None, zones=None):
    try:
        return event_catalog.update_parameters(archive_threshold_hours, zones)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def advance_scenario_clock(seconds):
    try:
        return {"clock": event_catalog.advance_clock(seconds)}
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def export_scenario_state():
    return event_catalog.export_state()


def load_scenario_state(payload):
    try:
        return event_catalog.load_state(payload)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def save_scenario_version(name):
    try:
        return event_catalog.save_version(name)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def list_scenario_versions():
    return event_catalog.list_versions()


def restore_scenario_version(name):
    try:
        return event_catalog.restore_version(name)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)


def delete_scenario_version(name):
    try:
        return event_catalog.delete_version(name)
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)
