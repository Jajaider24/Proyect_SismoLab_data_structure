"""Excepciones de dominio usadas por el catalogo de eventos."""


class EventValidationError(ValueError):
    """Error de datos de dominio detectado antes de mutar el catalogo."""


class EventNotFound(LookupError):
    """Error usado cuando un identificador no existe en el estado solicitado."""

