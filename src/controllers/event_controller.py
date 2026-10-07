"""Controlador HTTP para el catalogo de eventos sismicos."""

from datetime import datetime, timezone

from fastapi import HTTPException

from src.models.event import AttentionState, Event
from src.repository.catalog_repository import leer_json_catalogo
from src.repository.node_repository import leer_json_nodos
from src.services.eventCatalog_Service import EventCatalog
from src.services.eventCatalog.exceptions import EventNotFound, EventValidationError
from src.models.simulation_clock import SimulationClock


event_catalog = EventCatalog(
    clock=SimulationClock(datetime.now(timezone.utc)),
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


def _imported_event(node):
    """Convierte los nombres del JSON de nodos al modelo de eventos activo."""
    def value(*keys, default=None):
        for key in keys:
            if key in node and node[key] is not None:
                return node[key]
        return default

    identifier = value("id", "identifier", "identificador")
    occurred_at = value("occurred_at", "fecha_hora", default=event_catalog.now())
    if isinstance(occurred_at, str):
        occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    if not isinstance(occurred_at, datetime):
        raise ValueError("fecha_hora debe ser una fecha y hora ISO 8601.")

    revision = value("revision", "revision_text", default=1)
    if isinstance(revision, str):
        revision = int(revision[1:] if revision.lower().startswith("r") else revision)
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise ValueError("revision debe ser un entero positivo.")

    attention = value("attention")
    if attention is None:
        legacy_attention = value("estado_atencion", default=False)
        if not isinstance(legacy_attention, bool):
            raise ValueError("estado_atencion debe ser booleano.")
        attention = (
            AttentionState.REVIEWED
            if legacy_attention
            else AttentionState.PENDING
        )
    elif isinstance(attention, str):
        attention = AttentionState(attention)
    elif isinstance(attention, bool):
        attention = (
            AttentionState.REVIEWED if attention else AttentionState.PENDING
        )
    else:
        raise ValueError("attention debe ser 'pending' o 'reviewed'.")

    station = value("station", "procedencia", default="IMPORTACION_JSON")
    if not isinstance(station, str) or not station.strip():
        station = "IMPORTACION_JSON"

    return Event(
        identifier=identifier,
        magnitude=float(value("magnitude", "magnitud", default=0)),
        depth_km=float(value("depth_km", "profundidad_h", default=0)),
        x=float(value("x", default=0)),
        y=float(value("y", default=0)),
        occurred_at=occurred_at,
        station=station,
        revision=revision,
        attention=attention,
    )


def import_json_nodes(document):
    """Valida el documento completo y delega su insercion iterativa al catalogo."""
    try:
        nodes = leer_json_nodos(document)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        events = [_imported_event(node) for node in nodes]
    except (TypeError, ValueError, OverflowError) as error:
        raise HTTPException(
            status_code=422,
            detail=f"Los datos de un nodo no son validos: {error}",
        ) from error

    for event in events:
        try:
            event_catalog.get(event.identifier)
        except EventNotFound:
            continue
        raise HTTPException(
            status_code=409,
            detail=f"El identificador {event.identifier} ya existe en el catalogo.",
        )

    try:
        event_catalog.import_events(events)
        return event_catalog.response()
    except EventValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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


def import_json_catalog(document):
    """Valida y encola un archivo completo de reportes conservando su orden."""
    try:
        entries = leer_json_catalogo(document)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        reports = [_imported_event(entry) for entry in entries]
        pending_reports = event_catalog.enqueue_reports(reports)
    except (TypeError, ValueError, OverflowError) as error:
        if isinstance(error, EventValidationError):
            raise HTTPException(status_code=422, detail=str(error)) from error
        raise HTTPException(
            status_code=422,
            detail=f"Los datos de un reporte no son validos: {error}",
        ) from error

    return {
        "status": "queued",
        "imported_reports": len(reports),
        "pending_reports": pending_reports,
        "queue": event_catalog.pending_reports(),
    }


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
