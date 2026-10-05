"""Configuracion inmutable del escenario de simulacion."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.models.station import Station
from src.models.zone import Zone


@dataclass(frozen=True)
class ScenarioConfig:
	stations: tuple[Station, ...] = field(default_factory=tuple)
	zones: tuple[Zone, ...] = field(default_factory=tuple)
	simulation_time: datetime = field(
		default_factory=lambda: datetime.now(timezone.utc)
	)
