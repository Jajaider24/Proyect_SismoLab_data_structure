"""Modelo de un nodo AVL y validacion de sus datos de negocio."""

from datetime import datetime
from src.core.node.metodos.validaciones import (
    validate_decimal,
    validate_identifier,
)


class Node:
    """Nodo ordenado por ``identificador`` y con metadatos editables."""

    def __init__(self, identificador, prioridad=None, magnitud=0.0, profundidad_h=0.0,
                 fecha_hora=None, revision="", procedencia="",
                 estado_atencion=False, zona_poblada=False):
        # Validamos antes de guardar para que ningun nodo invalido entre al AVL.
        validate_identifier(identificador)
        validate_decimal("magnitud", magnitud, -2.0, 10.0)
        validate_decimal("profundidad_h", profundidad_h, 0.0, 700.0)
        if fecha_hora is not None and not isinstance(fecha_hora, str):
            raise ValueError("fecha_hora debe ser un string.")
        if not isinstance(revision, str):
            raise ValueError("revision debe ser un string.")
        if not isinstance(procedencia, str):
            raise ValueError("procedencia debe ser un string.")
        if not isinstance(estado_atencion, bool):
            raise ValueError("estado_atencion debe ser booleano.")
        if not isinstance(zona_poblada, bool):
            raise ValueError("zona_poblada debe ser booleano.")

        # Los seis atributos publicos forman la informacion editable del nodo.
        self.identificador = identificador
        self.magnitud = float(magnitud)
        self.profundidad_h = float(profundidad_h)
        self.zona_poblada = zona_poblada
        # La prioridad nunca viene del usuario: se deriva de estos tres datos.
        self.prioridad = self.calculate_priority()
        # Si no llega fecha, guardamos el momento exacto de creacion en ISO-8601.
        self.fecha_hora = fecha_hora or datetime.now().astimezone().isoformat(timespec="seconds")
        self.revision = revision
        self.procedencia = procedencia
        self.estado_atencion = estado_atencion

        # Estos atributos son internos y sostienen la estructura AVL.
        self.parent = None
        # Una hoja mide un nivel; los hijos inexistentes tienen altura cero.
        self.height = 1
        self.LeftChild = None
        self.RightChild = None

    def copy_data_from(self, other):
        """Copia solo datos de negocio, conservando enlaces y altura."""
        self.identificador = other.identificador
        self.magnitud = other.magnitud
        self.profundidad_h = other.profundidad_h
        self.zona_poblada = other.zona_poblada
        self.prioridad = self.calculate_priority()
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
        validate_identifier(value)
        self.identificador = value

    def getIdentifier(self):
        return self.identificador

    def getPriority(self):
        """Devuelve la prioridad usada como primer criterio de orden."""
        return self.prioridad

    def getMagnitude(self):
        """Devuelve la magnitud usada como segundo criterio de orden."""
        return self.magnitud

    def getZonaPoblada(self):
        """Devuelve si el nodo pertenece a una zona poblada."""
        return self.zona_poblada

    def setZonaPoblada(self, value):
        """Actualiza la zona y recalcula la prioridad derivada."""
        if not isinstance(value, bool):
            raise ValueError("zona_poblada debe ser booleano.")
        self.zona_poblada = value
        self.prioridad = self.calculate_priority()

    def calculate_priority(self):
        """Calcula prioridad 1, 2 o 3 usando las reglas de atencion."""
        high_magnitude = self.magnitud >= 6.0
        populated_high_risk = (
            self.magnitud >= 4.5
            and self.profundidad_h <= 30.0
            and self.zona_poblada
        )
        if high_magnitude or populated_high_risk:
            return 3
        if self.magnitud >= 4.5:
            return 2
        return 1

    def get_order_key(self):
        """Devuelve la clave completa usada por insercion y eliminacion."""
        return (self.prioridad, self.magnitud, self.identificador)

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
            "prioridad": self.prioridad,
            "magnitud": self.magnitud,
            "profundidad_h": self.profundidad_h,
            "zona_poblada": self.zona_poblada,
            "fecha_hora": self.fecha_hora,
            "revision": self.revision,
            "procedencia": self.procedencia,
            "estado_atencion": self.estado_atencion,
        }
