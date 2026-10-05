"""Politicas puras del dominio de eventos."""

from datetime import timedelta
from math import hypot


class PriorityPolicy:
    @staticmethod
    def calculate(magnitude, depth_km, populated_zone):
        if magnitude >= 6.0:
            return 3
        if magnitude >= 4.5:
            return 3 if depth_km <= 30.0 and populated_zone else 2
        return 1


class AssociationPolicy:
    """Asocia eventos cercanos en tiempo, espacio y estación."""

    def refresh(self, events):
        for event in events:
            event.associations.clear()
        events = list(events)
        for index, first in enumerate(events):
            for second in events[index + 1:]:
                close_in_time = abs(first.occurred_at - second.occurred_at) <= timedelta(hours=1)
                close_in_space = hypot(
                    first.latitude - second.latitude,
                    first.longitude - second.longitude,
                ) <= 1.0
                if close_in_time and close_in_space and first.station == second.station:
                    first.associations.add(second.identifier)
                    second.associations.add(first.identifier)