"""Conversores de dominio a respuestas JSON."""

from copy import deepcopy

from src.models.event import AttentionState
from src.models.event_key import EventKey


class EventPresenter:
    @staticmethod
    def as_dict(event):
        result = deepcopy(event.__dict__)
        result["attention"] = event.attention.value
        result["state"] = event.state.value
        result["occurred_at"] = event.occurred_at.isoformat()
        result["accepted_stations"] = sorted(event.accepted_stations)
        result["associations"] = sorted(event.associations)
        result["key"] = EventKey(event.priority, event.magnitude, event.identifier).__dict__
        result.update({
            "identificador": event.identifier,
            "profundidad_h": event.depth_km,
            "fecha_hora": event.occurred_at.isoformat(),
            "procedencia": event.station,
            "zona_poblada": event.populated_zone,
            "estado_atencion": event.attention == AttentionState.REVIEWED,
            "revision_text": str(event.revision),
        })
        return result