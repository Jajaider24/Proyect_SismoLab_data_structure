"""Modelo de un nodo AVL y validacion de sus datos de negocio."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import math


class Node:
    """Nodo ordenado por ``identificador`` y con metadatos editables."""

    def __init__(self, identificador, magnitud=0.0, profundidad_h=0.0,
                 fecha_hora=None, revision="", procedencia="",
                 estado_atencion=False):
        # Validamos antes de guardar para que ningun nodo invalido entre al AVL.
        self._validate_identifier(identificador)
        self._validate_decimal("magnitud", magnitud, -2.0, 10.0)
        self._validate_decimal("profundidad_h", profundidad_h, 0.0, 700.0)
        if fecha_hora is not None and not isinstance(fecha_hora, str):
            raise ValueError("fecha_hora debe ser un string.")
        if not isinstance(revision, str):
            raise ValueError("revision debe ser un string.")
        if not isinstance(procedencia, str):
            raise ValueError("procedencia debe ser un string.")
        if not isinstance(estado_atencion, bool):
            raise ValueError("estado_atencion debe ser booleano.")

        # Los seis atributos publicos forman la informacion editable del nodo.
        self.identificador = identificador
        self.magnitud = float(magnitud)
        self.profundidad_h = float(profundidad_h)
        # Si no llega fecha, guardamos el momento exacto de creacion en ISO-8601.
        self.fecha_hora = fecha_hora or datetime.now().astimezone().isoformat(timespec="seconds")
        self.revision = revision
        self.procedencia = procedencia
        self.estado_atencion = estado_atencion

        # Estos atributos son internos y sostienen la estructura AVL.
        self.parent = None
        self.height = 1
        self.LeftChild = None
        self.RightChild = None

    @staticmethod
    def _validate_identifier(value):
        """Rechaza bool y valores fuera del intervalo entero permitido."""
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 999999:
            raise ValueError("identificador debe ser un entero entre 1 y 999999.")

    @staticmethod
    def _validate_decimal(name, value, minimum, maximum):
        """Valida finitud, rango y un maximo de una cifra decimal."""
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

    def copy_data_from(self, other):
        """Copia solo datos de negocio, conservando enlaces y altura."""
        self.identificador = other.identificador
        self.magnitud = other.magnitud
        self.profundidad_h = other.profundidad_h
        self.fecha_hora = other.fecha_hora
        self.revision = other.revision
        self.procedencia = other.procedencia
        self.estado_atencion = other.estado_atencion

    # Estos aliases conservan la interfaz usada por la primera version.
    def getValue(self):
        """Devuelve el identificador, que es la clave de ordenamiento."""
        return self.identificador

    def setValue(self, value):
        """Actualiza la clave aplicando las mismas reglas del constructor."""
        self._validate_identifier(value)
        self.identificador = value

    def getIdentifier(self):
        return self.identificador

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def getLeftChild(self):
        return self.LeftChild

    def setLeftChild(self, left_child):
        self.LeftChild = left_child
        if left_child is not None:
            left_child.setParent(self)

    def getRightChild(self):
        return self.RightChild

    def setRightChild(self, right_child):
        self.RightChild = right_child
        if right_child is not None:
            right_child.setParent(self)

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        self.height = height

    def to_dict(self):
        """Devuelve los atributos de negocio para API y formulario de edicion."""
        return {
            "identificador": self.identificador,
            "magnitud": self.magnitud,
            "profundidad_h": self.profundidad_h,
            "fecha_hora": self.fecha_hora,
            "revision": self.revision,
            "procedencia": self.procedencia,
            "estado_atencion": self.estado_atencion,
        }
