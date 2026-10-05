"""Reporte recibido desde una estacion."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Report:
	identifier: int
	magnitude: float
	depth_km: float
	x: float
	y: float
	occurred_at: datetime
	station: str
	revision: int
