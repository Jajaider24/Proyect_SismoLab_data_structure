"""Clasificacion de pertenencia a zonas pobladas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
	name: str
	min_latitude: float
	max_latitude: float
	min_longitude: float
	max_longitude: float

	def contains(self, latitude: float, longitude: float) -> bool:
		return (
			self.min_latitude <= latitude <= self.max_latitude
			and self.min_longitude <= longitude <= self.max_longitude
		)


class ZoneClassifier:
	def __init__(self, zones=()):
		self._zones = tuple(zones)

	def is_populated(self, latitude: float, longitude: float) -> bool:
		return any(zone.contains(latitude, longitude) for zone in self._zones)
