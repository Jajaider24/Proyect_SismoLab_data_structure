"""Conversiones entre estado operativo y valores JSON sin referencias mutables."""

from datetime import datetime
from copy import deepcopy

from src.models.event import AttentionState, Event, EventState
from src.models.zone import Zone


def _event_to_dict(event):
    return {
        "identifier": event.identifier,
        "magnitude": event.magnitude,
        "depth_km": event.depth_km,
        "x": event.x,
        "y": event.y,
        "occurred_at": event.occurred_at.isoformat(),
        "station": event.station,
        "revision": event.revision,
        "populated_zone": event.populated_zone,
        "priority": event.priority,
        "attention": event.attention.value,
        "state": event.state.value,
        "accepted_stations": sorted(event.accepted_stations),
        "associations": sorted(event.associations),
    }


def _event_from_dict(data):
    return Event(
        identifier=data["identifier"],
        magnitude=data["magnitude"],
        depth_km=data["depth_km"],
        x=data["x"],
        y=data["y"],
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
        station=data["station"],
        revision=data["revision"],
        populated_zone=data["populated_zone"],
        priority=data["priority"],
        attention=AttentionState(data["attention"]),
        state=EventState(data["state"]),
        accepted_stations=set(data["accepted_stations"]),
        associations=set(data["associations"]),
    )


def encode_snapshot(snapshot):
    store = snapshot["store"]
    return {
        "store": {
            state: [_event_to_dict(event) for event in events.values()]
            for state, events in store.items()
        },
        "pending_reports": [_event_to_dict(event) for event in snapshot["pending_reports"]],
        "clock": snapshot["clock"].isoformat() if snapshot["clock"] else None,
        "parameters": {
            "archive_threshold_hours": snapshot["parameters"]["archive_threshold_hours"],
            "zones": [
                {
                    "name": zone.name,
                    "min_x": zone.min_x,
                    "max_x": zone.max_x,
                    "min_y": zone.min_y,
                    "max_y": zone.max_y,
                    "populated": zone.populated,
                }
                for zone in snapshot["parameters"]["zones"]
            ],
        },
        "stress_mode": snapshot["stress_mode"],
        "topology": snapshot["topology"],
        "height_convention": "empty-minus-one-leaf-zero",
        "metrics": snapshot["metrics"],
        "indicators": snapshot.get("indicators", {}),
    }


def decode_snapshot(data):
    parameters = data["parameters"]
    topology = deepcopy(data["topology"])
    if data.get("height_convention") is None:
        # Snapshots escritos antes del requisito 14 guardaban hoja=1.
        pending = [topology] if topology is not None else []
        while pending:
            branch = pending.pop()
            branch["height"] -= 1
            if branch["left"] is not None:
                pending.append(branch["left"])
            if branch["right"] is not None:
                pending.append(branch["right"])
    return {
        "store": {
            state: {event.identifier: event for event in map(_event_from_dict, events)}
            for state, events in data["store"].items()
        },
        "pending_reports": [_event_from_dict(event) for event in data["pending_reports"]],
        "clock": datetime.fromisoformat(data["clock"]) if data["clock"] else None,
        "parameters": {
            "archive_threshold_hours": parameters["archive_threshold_hours"],
            "zones": [Zone(**zone) for zone in parameters["zones"]],
        },
        "stress_mode": data["stress_mode"],
        "topology": topology,
        "metrics": data["metrics"],
        "indicators": data.get("indicators", {}),
    }
