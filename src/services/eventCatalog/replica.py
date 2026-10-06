"""Busqueda de eventos cercanos por tiempo y distancia tridimensional."""

from math import sqrt

from src.services.eventCatalog.exceptions import EventValidationError
from src.services.event_presenter import EventPresenter


class EventReplicaService:
    """Calcula replicas candidatas usando ventana temporal y radio espacial."""

    def find_replicas(self, base_event, radius_km, window_hours, active_events, archived_events):
        """Devuelve eventos activos/archivados cercanos al evento base.

        Args:
            base_event: Evento usado como punto de comparacion.
            radius_km: Radio maximo R en kilometros.
            window_hours: Ventana maxima W en horas.
            active_events: Diccionario de eventos activos por identificador.
            archived_events: Diccionario de eventos archivados por identificador.

        Returns:
            list[dict]: Coincidencias ordenadas de menor a mayor distancia.
        """
        self._validate_parameters(radius_km, window_hours)
        time_filtered = self._filter_by_time(
            base_event,
            active_events,
            archived_events,
            window_hours,
        )
        replicas = []
        for event in time_filtered:
            distance = self._distance(base_event, event)
            if distance <= radius_km:
                replicas.append({
                    "identifier": event.identifier,
                    "state": event.state.value,
                    "distance_km": round(distance, 4),
                    "time_delta_hours": round(
                        abs(event.occurred_at - base_event.occurred_at).total_seconds() / 3600,
                        4,
                    ),
                    "event": EventPresenter.as_dict(event),
                })
        return sorted(
            replicas,
            key=lambda item: (item["distance_km"], item["time_delta_hours"], item["identifier"]),
        )

    @staticmethod
    def _validate_parameters(radius_km, window_hours):
        """Valida que R y W sean enteros no negativos."""
        if isinstance(radius_km, bool) or not isinstance(radius_km, int) or radius_km < 0:
            raise EventValidationError("R debe ser un entero mayor o igual a 0.")
        if isinstance(window_hours, bool) or not isinstance(window_hours, int) or window_hours < 0:
            raise EventValidationError("W debe ser un entero mayor o igual a 0.")

    @staticmethod
    def _filter_by_time(base_event, active_events, archived_events, window_hours):
        """Filtra eventos cuya diferencia horaria no excede W."""
        candidates = list(active_events.values()) + list(archived_events.values())
        filtered = []
        for event in candidates:
            if event.identifier == base_event.identifier:
                continue
            delta_hours = abs(event.occurred_at - base_event.occurred_at).total_seconds() / 3600
            if delta_hours <= window_hours:
                filtered.append(event)
        return filtered

    @staticmethod
    def _distance(first, second):
        """Calcula distancia euclidiana 3D usando X, Y y profundidad como Z."""
        return sqrt(
            (second.x - first.x) ** 2
            + (second.y - first.y) ** 2
            + (second.depth_km - first.depth_km) ** 2
        )
