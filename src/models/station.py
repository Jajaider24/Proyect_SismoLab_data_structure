"""Representacion minima de una estacion emisora."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
	identifier: str
