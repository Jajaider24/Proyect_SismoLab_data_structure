"""Clave de ordenamiento del catalogo AVL."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class EventKey:
	priority: int
	magnitude: float
	identifier: int
