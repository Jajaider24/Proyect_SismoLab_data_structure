"""Entidades y valores de dominio para la gestion de eventos sismicos."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class EventState(str, Enum):
	ACTIVE = "active"
	ARCHIVED = "archived"
	DELETED = "deleted"


class AttentionState(str, Enum):
	PENDING = "pending"
	REVIEWED = "reviewed"


@dataclass
class Event:
	"""Estado de negocio de un evento, independiente de su nodo AVL."""

	identifier: int
	magnitude: float
	depth_km: float
	x: float
	y: float
	occurred_at: datetime
	station: str
	revision: int = 1
	populated_zone: bool = False
	priority: int = 1
	attention: AttentionState = AttentionState.PENDING
	state: EventState = EventState.ACTIVE
	accepted_stations: set[str] = field(default_factory=set)
	associations: set[int] = field(default_factory=set)

	def same_report_data(self, other: "Event") -> bool:
		"""Compara solamente los datos definidos por el contrato de reportes."""
		return (
			self.magnitude == other.magnitude
			and self.depth_km == other.depth_km
			and self.x == other.x
			and self.y == other.y
			and self.occurred_at == other.occurred_at
		)

	def normalize_time(self) -> None:
		if self.occurred_at.tzinfo is None:
			self.occurred_at = self.occurred_at.replace(tzinfo=timezone.utc)
		else:
			self.occurred_at = self.occurred_at.astimezone(timezone.utc)

	def copy(self) -> "Event":
		"""Devuelve una copia desacoplada para historial y transacciones."""
		return Event(
			identifier=self.identifier,
			magnitude=self.magnitude,
			depth_km=self.depth_km,
			x=self.x,
			y=self.y,
			occurred_at=self.occurred_at,
			station=self.station,
			revision=self.revision,
			populated_zone=self.populated_zone,
			priority=self.priority,
			attention=self.attention,
			state=self.state,
			accepted_stations=set(self.accepted_stations),
			associations=set(self.associations),
		)
