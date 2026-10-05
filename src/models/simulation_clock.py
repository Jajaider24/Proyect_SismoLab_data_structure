"""Reloj UTC explicito del escenario."""

from datetime import datetime, timedelta, timezone


class SimulationClock:
	def __init__(self, current_time: datetime):
		self.current_time = self._utc(current_time)

	@staticmethod
	def _utc(value):
		if value.tzinfo is None:
			return value.replace(tzinfo=timezone.utc)
		return value.astimezone(timezone.utc)

	def advance(self, delta: timedelta):
		if delta.total_seconds() < 0:
			raise ValueError("el reloj no puede retroceder")
		self.current_time += delta

	def validate_occurrence(self, occurred_at: datetime):
		if self._utc(occurred_at) > self.current_time:
			raise ValueError("la ocurrencia no puede estar en el futuro")
