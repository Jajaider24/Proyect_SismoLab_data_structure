"""Validaciones reutilizables para los datos de un nodo."""

from decimal import Decimal, InvalidOperation
import math


def validate_identifier(value):
    """Comprueba que el identificador sea un entero dentro del rango permitido."""
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 999999:
        raise ValueError("identificador debe ser un entero entre 1 y 999999.")


def validate_decimal(name, value, minimum, maximum):
    """Comprueba finitud, rango y como maximo una cifra decimal."""
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError(f"{name} debe ser un numero finito.") from error
    if not decimal_value.is_finite() or not minimum <= float(decimal_value) <= maximum:
        raise ValueError(f"{name} debe estar entre {minimum:.1f} y {maximum:.1f}.")
    if decimal_value.as_tuple().exponent < -1:
        raise ValueError(f"{name} solo puede tener un decimal.")
    if not math.isfinite(float(decimal_value)):
        raise ValueError(f"{name} debe ser finito.")


def validate_finite_number(name, value):
    """Comprueba que un valor numerico sea finito sin imponer un rango."""
    if isinstance(value, bool):
        raise ValueError(f"{name} debe ser un numero finito.")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} debe ser un numero finito.") from error
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} debe ser un numero finito.")
