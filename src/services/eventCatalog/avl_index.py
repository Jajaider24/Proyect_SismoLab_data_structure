"""Indice AVL derivado de los eventos activos."""

from src.core.node.node import Node
from src.core.AvlTree.rotation_tracker import RotationTracker
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
            x=event.x,
            y=event.y,
            fecha_hora=event.occurred_at.isoformat(),
            revision=str(event.revision),
            procedencia=event.station,
            estado_atencion=event.attention == AttentionState.REVIEWED,
            zona_poblada=event.populated_zone,
        )

    def rebuild(self, active_events, rebalance=True):
        """Reconstruye el AVL desde una coleccion de eventos activos."""
        self._nodes_by_id = {}
        nodes = []
        for identifier, event in active_events.items():
            node = self.node_from_event(event)
            nodes.append(node)
            self._nodes_by_id[identifier] = node
        self._avl.rebuild(nodes, rebalance=rebalance)

    def insert(self, event, tracker=None, rebalance=True):
        """Inserta en el AVL el nodo derivado de un evento activo."""
        node = self.node_from_event(event)
        if tracker is None:
            with RotationTracker():
                inserted = self._avl.insert_node(node, rebalance=rebalance)
        else:
            inserted = self._avl.insert_node(node, rebalance=rebalance)
        if not inserted:
            raise EventValidationError("no se pudo insertar la clave del evento.")
        self._nodes_by_id[event.identifier] = node

    def update(self, event, reinsert, tracker=None, rebalance=True):
        """Actualiza un nodo existente o lo reinserta si cambia su clave AVL."""
        current = self._nodes_by_id.get(event.identifier)
        if current is None:
            raise EventNotFound(event.identifier)

        if reinsert:
            self.remove(event.identifier, tracker=tracker, rebalance=rebalance)
            self.insert(event, tracker=tracker, rebalance=rebalance)
            return

        # Los datos no usados por el orden se copian sin cambiar identidad ni enlaces.
        current.copy_data_from(self.node_from_event(event))

    def remove(self, identifier, tracker=None, rebalance=True):
        """Elimina del AVL el nodo de un evento activo por identificador."""
        if tracker is None:
            with RotationTracker():
                deleted = self._avl.delete_node(identifier, rebalance=rebalance)
        else:
            deleted = self._avl.delete_node(identifier, rebalance=rebalance)
        if not deleted:
            raise EventNotFound(identifier)
        self._nodes_by_id.pop(identifier, None)

    def audit(self):
        return self._avl.audit()

    def recover(self):
        result = self._avl.recover()
        self._nodes_by_id = {
            node.getIdentifier(): node for node in self._avl.iter_nodes_in_order()
        }
        return result

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

    def select_old_branch(self, active_events, current_time, threshold_hours):
        """Selecciona la rama antigua elegible de mayor tamaño.

        Un nodo solo es elegible cuando todos los eventos de su subarbol son
        de prioridad 1 y superan estrictamente el umbral de antiguedad. Los
        candidatos se ordenan por cantidad, profundidad y luego identificador.
        """
        candidates = []

        def inspect_subtree(node):
            """Devuelve elegibilidad y cantidad, sin copiar listas por rama."""
            if node is None:
                return True, 0

            left_eligible, left_count = inspect_subtree(node.getLeftChild())
            right_eligible, right_count = inspect_subtree(node.getRightChild())
            event = active_events[node.getIdentifier()]
            age_hours = (
                current_time - event.occurred_at
            ).total_seconds() / 3600
            eligible = (
                event.priority == 1
                and age_hours > threshold_hours
                and left_eligible
                and right_eligible
            )
            node_count = left_count + right_count + 1
            if eligible:
                candidates.append({
                    "root_identifier": node.getIdentifier(),
                    "root_depth": node.getNodeDepth(),
                    "count": node_count,
                })
            return eligible, node_count

        inspect_subtree(self._avl.get_root())
        if not candidates:
            return {
                "eligible": False,
                "root_identifier": None,
                "root_depth": None,
                "count": 0,
                "identifiers": [],
                "eligible_branches": 0,
                "reason": (
                    "No hay subarboles donde todos los eventos tengan prioridad "
                    f"baja y antiguedad estrictamente mayor que {threshold_hours:g} horas."
                ),
            }

        # La tupla aplica en orden los desempates especificados por el dominio.
        selected = max(
            candidates,
            key=lambda candidate: (
                candidate["count"],
                candidate["root_depth"],
                candidate["root_identifier"],
            ),
        )
        identifiers = self.branch_identifiers(selected["root_identifier"])
        largest_count = selected["count"]
        largest_candidates = [
            candidate for candidate in candidates
            if candidate["count"] == largest_count
        ]
        reason = (
            "Todos sus eventos tienen prioridad baja (P1) y antiguedad "
            f"estrictamente mayor que {threshold_hours:g} horas. Se eligio la "
            f"rama con mas nodos ({largest_count}) entre {len(candidates)} "
            "subarboles elegibles."
        )
        if len(largest_candidates) > 1:
            deepest = max(candidate["root_depth"] for candidate in largest_candidates)
            depth_candidates = [
                candidate for candidate in largest_candidates
                if candidate["root_depth"] == deepest
            ]
            reason += f" Empate de tamano: se priorizo la mayor profundidad ({deepest})."
            if len(depth_candidates) > 1:
                reason += (
                    " Persistio el empate: se eligio la raiz con mayor identificador "
                    f"({selected['root_identifier']})."
                )

        return {
            "eligible": True,
            **selected,
            "identifiers": identifiers,
            "eligible_branches": len(candidates),
            "reason": reason,
        }

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
