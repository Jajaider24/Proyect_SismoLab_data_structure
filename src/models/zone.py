"""Clasificacion de pertenencia a zonas del escenario."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
	name: str
	min_x: float
	max_x: float
	min_y: float
	max_y: float
	populated: bool = False

	def contains(self, x: float, y: float) -> bool:
		return (
			self.min_x <= x <= self.max_x
			and self.min_y <= y <= self.max_y
		)


class ZoneClassifier:
	def __init__(self, zones=()):
		self._zones = tuple(zones)

	def is_populated(self, x: float, y: float) -> bool:
		return any(zone.populated for zone in self._zones if zone.contains(x, y))
