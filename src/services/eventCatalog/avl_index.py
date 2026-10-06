"""Indice AVL derivado de los eventos activos."""

from src.core.node.node import Node
from src.models.event import AttentionState
from src.services.Avlservice import AVLTreeService
from src.services.eventCatalog.exceptions import EventNotFound, EventValidationError


class EventAvlIndex:
    """Sincroniza eventos activos con nodos dentro de un AVL propio."""

    def __init__(self, avl_service=None):
        """Inicializa el indice con un servicio AVL dedicado."""
        self._avl = avl_service or AVLTreeService()
        self._nodes_by_id = {}

    @property
    def tree(self):
        """Expone el arbol interno para compatibilidad de bajo nivel."""
        return self._avl.tree

    @staticmethod
    def node_from_event(event):
        """Convierte un evento activo en el ``Node`` que entiende el AVL."""
        return Node(
            event.identifier,
            magnitud=event.magnitude,
            profundidad_h=event.depth_km,
            fecha_hora=event.occurred_at.isoformat(),
            revision=str(event.revision),
            procedencia=event.station,
            estado_atencion=event.attention == AttentionState.REVIEWED,
            zona_poblada=event.populated_zone,
        )

    def rebuild(self, active_events):
        """Reconstruye el AVL desde una coleccion de eventos activos."""
        self._nodes_by_id = {}
        nodes = []
        for identifier, event in active_events.items():
            node = self.node_from_event(event)
            nodes.append(node)
            self._nodes_by_id[identifier] = node
        self._avl.rebuild(nodes)

    def insert(self, event):
        """Inserta en el AVL el nodo derivado de un evento activo."""
        node = self.node_from_event(event)
        if not self._avl.insert_node(node):
            raise EventValidationError("no se pudo insertar la clave del evento.")
        self._nodes_by_id[event.identifier] = node

    def remove(self, identifier):
        """Elimina del AVL el nodo de un evento activo por identificador."""
        if not self._avl.delete_node(identifier):
            raise EventNotFound(identifier)
        self._nodes_by_id.pop(identifier, None)

    def branch_identifiers(self, identifier):
        """Devuelve los identificadores del subarbol que nace en identifier."""
        root = self._nodes_by_id.get(identifier)
        if root is None:
            raise EventNotFound(identifier)
        identifiers = []

        def collect(node):
            """Acumula identificadores de un subarbol por recorrido pre-order."""
            if node is None:
                return
            identifiers.append(node.getIdentifier())
            collect(node.getLeftChild())
            collect(node.getRightChild())

        collect(root)
        return identifiers

    def values(self):
        """Devuelve identificadores en recorrido in-order."""
        return self._avl.get_values()

    def tree_data(self, active_events, event_serializer):
        """Serializa el AVL con los datos de dominio de cada evento."""
        def event_dict_for(node):
            """Obtiene la representacion JSON del evento asociado a un nodo."""
            event = active_events[node.getIdentifier()]
            return event_serializer(event)

        def event_extra_for(node):
            """Agrega el alias ``event`` esperado por la respuesta de eventos."""
            return {"event": event_dict_for(node)}

        return self._avl.serialize_tree(
            attributes_factory=event_dict_for,
            extra_factory=event_extra_for,
        )

