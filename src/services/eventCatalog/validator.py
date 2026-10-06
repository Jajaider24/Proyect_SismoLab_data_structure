"""Validaciones de dominio para eventos sismicos."""

from src.services.eventCatalog.exceptions import EventValidationError


class EventValidator:
    """Valida que un evento pueda entrar al catalogo."""

    def __init__(self, clock):
        """Recibe el reloj usado para rechazar ocurrencias futuras."""
        self._clock = clock

    def validate(self, event):
        """Valida rangos, finitud, estacion, tiempo y revision del evento."""
        if not isinstance(event.identifier, int) or not 1 <= event.identifier <= 999999:
            raise EventValidationError("identificador debe ser un entero entre 1 y 999999.")
        if not isinstance(event.station, str) or not event.station.strip():
            raise EventValidationError("station es obligatorio.")
        if not -2.0 <= event.magnitude <= 10.0:
            raise EventValidationError("magnitud fuera de rango.")
        if not 0.0 <= event.depth_km <= 700.0:
            raise EventValidationError("profundidad fuera de rango.")
        if not 0.0 <= event.x <= 1000.0:
            raise EventValidationError("x debe estar entre 0 y 1000 km.")
        if not 0.0 <= event.y <= 1000.0:
            raise EventValidationError("y debe estar entre 0 y 1000 km.")
        for name, value in (
            ("magnitud", event.magnitude),
            ("profundidad", event.depth_km),
            ("x", event.x),
            ("y", event.y),
        ):
            text = str(value).lower()
            if "nan" in text or "inf" in text:
                raise EventValidationError(f"{name} debe ser finito.")
            if "." in text and len(text.split(".", 1)[1]) > 1:
                raise EventValidationError(f"{name} solo puede tener un decimal.")
        event.normalize_time()
        try:
            self._clock.validate_occurrence(event.occurred_at)
        except ValueError as error:
            raise EventValidationError(str(error)) from error
        if event.revision < 1:
            raise EventValidationError("revision debe ser positiva.")

