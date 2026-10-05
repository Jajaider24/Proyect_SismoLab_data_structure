"""Politicas puras del dominio de eventos."""

from datetime import timedelta
from math import hypot

from src.core.node.metodos.priority import calculate_attention_priority


class PriorityPolicy:
    """Expone la prioridad de atencion usada por eventos y nodos AVL."""

    @staticmethod
    def calculate(magnitude, depth_km, populated_zone):
        """Devuelve prioridad 1, 2 o 3 desde datos sismicos ya validados."""
        return calculate_attention_priority(magnitude, depth_km, populated_zone)


class AssociationPolicy:
    """Relaciona eventos cercanos en tiempo, espacio y estacion."""

    def refresh(self, events):
        """Recalcula asociaciones mutuas entre todos los eventos recibidos."""
        for event in events:
            event.associations.clear()
        events = list(events)
        for index, first in enumerate(events):
            for second in events[index + 1:]:
                close_in_time = abs(first.occurred_at - second.occurred_at) <= timedelta(hours=1)
                close_in_space = hypot(
                    first.x - second.x,
                    first.y - second.y,
                ) <= 1.0
                if close_in_time and close_in_space and first.station == second.station:
                    first.associations.add(second.identifier)
                    second.associations.add(first.identifier)
