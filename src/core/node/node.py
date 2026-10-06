"""Modelo de un nodo AVL y validacion de sus datos de negocio."""

from datetime import datetime
from src.core.node.metodos.validaciones import (
    validate_decimal,
    validate_identifier,
)
from src.core.node.metodos.priority import calculate_attention_priority


class Node:
    """Nodo ordenado por ``identificador`` y con metadatos editables."""

    def __init__(self, identificador, prioridad=None, magnitud=0.0, profundidad_h=0.0,
                 x=0.0, y=0.0, fecha_hora=None, revision="", procedencia="",
                 estado_atencion=False, zona_poblada=False):
        """Valida datos de negocio e inicializa enlaces internos del AVL."""
        # Validamos antes de guardar para que ningun nodo invalido entre al AVL.
        validate_identifier(identificador)
        validate_decimal("magnitud", magnitud, -2.0, 10.0)
        validate_decimal("profundidad_h", profundidad_h, 0.0, 700.0)
        validate_decimal("x", x, 0.0, 1000.0)
        validate_decimal("y", y, 0.0, 1000.0)
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
        self.x = float(x)
        self.y = float(y)
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
        # La raiz inicia en 1; cada hijo suma uno respecto a su padre.
        self.profundidad_nodo = 1
        self.LeftChild = None
        self.RightChild = None

    def copy_data_from(self, other):
        """Copia solo datos de negocio, conservando enlaces y altura."""
        self.identificador = other.identificador
        self.magnitud = other.magnitud
        self.profundidad_h = other.profundidad_h
        self.x = other.x
        self.y = other.y
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
        """Devuelve el identificador canonico del nodo."""
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

    def getX(self):
        """Devuelve la coordenada X en kilometros."""
        return self.x

    def setX(self, value):
        """Actualiza la coordenada X validando el rango del escenario."""
        validate_decimal("x", value, 0.0, 1000.0)
        self.x = float(value)

    def getY(self):
        """Devuelve la coordenada Y en kilometros."""
        return self.y

    def setY(self, value):
        """Actualiza la coordenada Y validando el rango del escenario."""
        validate_decimal("y", value, 0.0, 1000.0)
        self.y = float(value)

    def setZonaPoblada(self, value):
        """Actualiza la zona y recalcula la prioridad derivada."""
        if not isinstance(value, bool):
            raise ValueError("zona_poblada debe ser booleano.")
        self.zona_poblada = value
        self.prioridad = self.calculate_priority()

    def calculate_priority(self):
        """Calcula prioridad 1, 2 o 3 usando la regla compartida del AVL."""
        return calculate_attention_priority(
            self.magnitud,
            self.profundidad_h,
            self.zona_poblada,
        )

    def get_order_key(self):
        """Devuelve la clave completa usada por insercion y eliminacion."""
        return (self.prioridad, self.magnitud, self.identificador)

    def getParent(self):
        """Devuelve el padre actual del nodo dentro del AVL."""
        return self.parent

    def setParent(self, parent):
        """Asigna el padre actual del nodo dentro del AVL."""
        self.parent = parent
        self.profundidad_nodo = 1 if parent is None else parent.getNodeDepth() + 1

    def getLeftChild(self):
        """Devuelve el hijo izquierdo del nodo."""
        return self.LeftChild

    def setLeftChild(self, left_child):
        """Asigna el hijo izquierdo y sincroniza su padre."""
        self.LeftChild = left_child
        if left_child is not None:
            left_child.setParent(self)

    def getRightChild(self):
        """Devuelve el hijo derecho del nodo."""
        return self.RightChild

    def setRightChild(self, right_child):
        """Asigna el hijo derecho y sincroniza su padre."""
        self.RightChild = right_child
        if right_child is not None:
            right_child.setParent(self)

    def getHeight(self):
        """Devuelve la altura AVL almacenada en el nodo."""
        return self.height

    def setHeight(self, height):
        """Actualiza la altura AVL almacenada en el nodo."""
        self.height = height

    def getNodeDepth(self):
        """Devuelve la profundidad estructural del nodo dentro del AVL."""
        return self.profundidad_nodo

    def setNodeDepth(self, depth):
        """Actualiza la profundidad estructural del nodo dentro del AVL."""
        if not isinstance(depth, int) or depth < 1:
            raise ValueError("profundidad_nodo debe ser un entero positivo.")
        self.profundidad_nodo = depth

    def to_dict(self):
        """Devuelve los atributos de negocio para API y formulario de edicion."""
        return {
            "identificador": self.identificador,
            "prioridad": self.prioridad,
            "magnitud": self.magnitud,
            "profundidad_h": self.profundidad_h,
            "x": self.x,
            "y": self.y,
            "profundidad_nodo": self.profundidad_nodo,
            "zona_poblada": self.zona_poblada,
            "fecha_hora": self.fecha_hora,
            "revision": self.revision,
            "procedencia": self.procedencia,
            "estado_atencion": self.estado_atencion,
        }
