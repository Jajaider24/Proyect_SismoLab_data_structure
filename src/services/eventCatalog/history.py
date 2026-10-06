"""Historial de acciones del catalogo de eventos."""

from src.core.structures.stack import Stack
from src.services.eventCatalog.exceptions import EventNotFound


class EventHistory:
    """Guarda snapshots para poder deshacer mutaciones del catalogo."""

    def __init__(self):
        """Inicializa una pila vacia de acciones."""
        self._history = Stack()

    def record(self, action, snapshot):
        """Guarda una accion y el estado previo asociado."""
        self._history.push((action, snapshot))

    def pop_snapshot(self):
        """Devuelve el ultimo snapshot o falla si no hay acciones."""
        if not self._history:
            raise EventNotFound("no hay acciones para deshacer")
        _action, snapshot = self._history.pop()
        return snapshot

    def count(self):
        """Devuelve cuantas acciones pueden deshacerse."""
        return len(self._history)

