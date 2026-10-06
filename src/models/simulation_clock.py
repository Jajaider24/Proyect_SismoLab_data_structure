"""Reloj UTC explicito del escenario."""

from datetime import datetime, timedelta, timezone


class SimulationClock:
    """Valida ocurrencias contra un tiempo UTC fijo o contra el tiempo actual."""

    def __init__(self, current_time: datetime | None = None):
        """Crea un reloj fijo si recibe fecha o uno vivo si queda vacio."""
        self.current_time = self._utc(current_time) if current_time is not None else None

    @staticmethod
    def _utc(value):
        """Normaliza una fecha naive o aware a UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def now(self):
        """Devuelve el tiempo de referencia actual del reloj."""
        return self.current_time or datetime.now(timezone.utc)

    def advance(self, delta: timedelta):
        """Avanza un reloj fijo sin permitir retrocesos."""
        if delta.total_seconds() < 0:
            raise ValueError("el reloj no puede retroceder")
        if self.current_time is None:
            self.current_time = datetime.now(timezone.utc)
        self.current_time += delta

    def snapshot(self):
        """Devuelve el instante UTC fijado, o None si el reloj sigue en vivo."""
        return self.current_time

    def restore(self, current_time):
        """Restaura el instante conservando el modo vivo o fijo del reloj."""
        self.current_time = self._utc(current_time) if current_time is not None else None

    def validate_occurrence(self, occurred_at: datetime):
        """Rechaza fechas de ocurrencia posteriores al tiempo de referencia."""
        if self._utc(occurred_at) > self.now():
            raise ValueError("la ocurrencia no puede estar en el futuro")
