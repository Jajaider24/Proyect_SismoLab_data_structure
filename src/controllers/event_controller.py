"""Controlador HTTP para el catalogo de eventos sismicos."""

from fastapi import HTTPException

from src.services.event_catalog import EventCatalog, EventNotFound, EventValidationError


event_catalog = EventCatalog()


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
    return {"actions": event_catalog.history_count(), "metrics": event_catalog.metrics()}


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
            "data": event_catalog.response(),
        }
    except (EventNotFound, EventValidationError) as error:
        _handle_event_error(error)
