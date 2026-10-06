"""Almacenamiento de eventos por estado de ciclo de vida."""

from src.models.event import EventState
from src.services.eventCatalog.exceptions import EventNotFound, EventValidationError


class EventStateStore:
    """Guarda eventos activos, archivados y eliminados por identificador."""

    def __init__(self):
        """Inicializa los contenedores de estado vacios."""
        self.active = {}
        self.archived = {}
        self.deleted = {}

    def ensure_identifier_available(self, identifier):
        """Rechaza identificadores ya usados en cualquier estado."""
        if identifier in self.active or identifier in self.archived or identifier in self.deleted:
            raise EventValidationError("el identificador ya existe en el catalogo.")

    def get(self, identifier):
        """Obtiene una copia de un evento activo, archivado o eliminado."""
        if identifier in self.active:
            return self.active[identifier].copy()
        if identifier in self.archived:
            return self.archived[identifier].copy()
        if identifier in self.deleted:
            return self.deleted[identifier].copy()
        raise EventNotFound(identifier)

    def active_event(self, identifier):
        """Devuelve el evento activo mutable o levanta error si no existe."""
        current = self.active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        return current

    def current_report_target(self, identifier):
        """Devuelve el evento activo o archivado asociado a un reporte."""
        return self.active.get(identifier) or self.archived.get(identifier)

    def add_active(self, event):
        """Registra un evento como activo."""
        self.active[event.identifier] = event

    def remove_active(self, identifier):
        """Retira y devuelve un evento activo."""
        try:
            return self.active.pop(identifier)
        except KeyError as error:
            raise EventNotFound(identifier) from error

    def move_active_to_deleted(self, identifier):
        """Mueve un evento activo al contenedor de eliminados."""
        event = self.remove_active(identifier)
        event.state = EventState.DELETED
        self.deleted[identifier] = event
        return event

    def move_active_to_archived(self, identifier):
        """Mueve un evento activo al contenedor de archivados."""
        event = self.remove_active(identifier)
        event.state = EventState.ARCHIVED
        self.archived[identifier] = event
        return event

    def reactivate(self, event):
        """Mueve o registra un evento como activo."""
        self.archived.pop(event.identifier, None)
        self.active[event.identifier] = event

    def snapshot(self):
        """Toma una copia profunda del estado de eventos."""
        return {
            "active": {key: event.copy() for key, event in self.active.items()},
            "archived": {key: event.copy() for key, event in self.archived.items()},
            "deleted": {key: event.copy() for key, event in self.deleted.items()},
        }

    def restore(self, snapshot):
        """Restaura los contenedores desde un snapshot."""
        self.active = {key: event.copy() for key, event in snapshot["active"].items()}
        self.archived = {key: event.copy() for key, event in snapshot["archived"].items()}
        self.deleted = {key: event.copy() for key, event in snapshot["deleted"].items()}

