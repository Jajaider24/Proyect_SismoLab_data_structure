"""Consultas de desempeño del catálogo y comparación de estructuras."""

from datetime import timezone

from src.core.AvlTree.tree import AVL_tree
from src.core.bst import BinarySearchTree
from src.core.node.node import Node
from src.models.event import AttentionState


class EventPerformanceQueries:
    """Lee el almacén y el índice AVL sin modificar el estado del catálogo."""

    def __init__(self, store, avl_index):
        self._store = store
        self._avl_index = avl_index

    @staticmethod
    def _event_data(event):
        return {
            "identifier": event.identifier,
            "priority": event.priority,
            "magnitude": event.magnitude,
            "depth_km": event.depth_km,
            "occurred_at": event.occurred_at.isoformat(),
            "attention": event.attention.value,
            "state": event.state.value,
        }

    def pending_top(self, k):
        results = []
        examined = 0

        stack = []
        current = self._avl_index.tree.getRoot()
        while (current is not None or stack) and len(results) < k:
            while current is not None:
                stack.append(current)
                current = current.getRightChild()
            current = stack.pop()
            examined += 1
            event = self._store.active[current.getIdentifier()]
            if event.attention == AttentionState.PENDING:
                results.append(self._event_data(event))
            current = current.getLeftChild() if len(results) < k else None

        return {
            "events": results,
            "requested": k,
            "nodes_examined": examined,
            "order": "descending EventKey (priority, magnitude, identifier)",
        }

    def magnitude_range(self, minimum, maximum):
        results = []
        examined = 0

        for node in self._inorder_nodes(self._avl_index.tree.getRoot()):
            examined += 1
            event = self._store.active[node.getIdentifier()]
            if minimum <= event.magnitude <= maximum:
                results.append(self._event_data(event))
        return {
            "events": results,
            "minimum": minimum,
            "maximum": maximum,
            "nodes_examined": examined,
        }

    def shallow_depth_range(self, maximum_depth, start, end):
        start = self._as_utc(start)
        end = self._as_utc(end)
        results = []
        examined = 0

        for node in self._inorder_nodes(self._avl_index.tree.getRoot()):
            examined += 1
            event = self._store.active[node.getIdentifier()]
            if start <= event.occurred_at <= end and event.depth_km <= maximum_depth:
                results.append(self._event_data(event))
        return {
            "events": results,
            "maximum_depth_km": maximum_depth,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "nodes_examined": examined,
        }

    @staticmethod
    def _as_utc(value):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _inorder_nodes(root):
        """Recorre el AVL iterativamente para soportar el modo de estrés."""
        stack = []
        current = root
        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.getLeftChild()
            current = stack.pop()
            yield current
            current = current.getRightChild()

    def associations(self, identifier):
        event = self._store.get(identifier)
        events_by_id = {**self._store.active, **self._store.archived}
        associated_ids = set(event.associations)
        associated_ids.update(
            candidate_id
            for candidate_id, candidate in events_by_id.items()
            if identifier in candidate.associations
        )
        candidates = [
            self._event_data(events_by_id[candidate_id])
            for candidate_id in sorted(associated_ids)
            if candidate_id in events_by_id
        ]
        used_by = [
            self._event_data(candidate)
            for candidate in events_by_id.values()
            if identifier in candidate.associations or candidate.identifier in event.associations
        ]
        reference = self._event_data(event)
        return {
            "event": reference,
            "selected_reference": reference,
            "candidates": candidates,
            "used_by": used_by,
            "nodes_examined": 0,
            "note": (
                "La referencia es el evento indicado en la consulta. El modelo "
                "actual guarda asociaciones mutuas, no una referencia direccional."
            ),
        }

    def costly_high_priority(self, depth_limit):
        results = []
        examined = 0

        stack = [self._avl_index.tree.getRoot()]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            examined += 1
            priority = node.getPriority()
            if priority < 3:
                # La clave inicia con prioridad; a la izquierda no puede haber P3.
                stack.append(node.getRightChild())
                continue
            if priority > 3:
                stack.append(node.getLeftChild())
                continue
            stack.append(node.getRightChild())
            event = self._store.active[node.getIdentifier()]
            if node.getNodeDepth() > depth_limit:
                results.append({
                    **self._event_data(event),
                    "node_depth": node.getNodeDepth(),
                    "depth_limit": depth_limit,
                    "search_nodes_visited": self._search_key(node.get_order_key()),
                })
            stack.append(node.getLeftChild())
        return {
            "events": results,
            "depth_limit": depth_limit,
            "nodes_examined": examined,
        }

    def _search_key(self, key):
        current = self._avl_index.tree.getRoot()
        visited = 0
        while current is not None:
            visited += 1
            current_key = current.get_order_key()
            if current_key == key:
                return visited
            current = current.getLeftChild() if key < current_key else current.getRightChild()
        return visited

    @staticmethod
    def compare_structures(events):
        events = list(events)
        order_key = lambda event: (event.priority, event.magnitude, event.identifier)
        ascending = sorted(events, key=order_key)
        orders = {
            "catalog_order": events,
            "ascending": ascending,
            "descending": list(reversed(ascending)),
        }
        keys = [order_key(event) for event in events]
        comparisons = []

        for order_name, insertion_order in orders.items():
            avl = AVL_tree()
            bst = BinarySearchTree()
            for event in insertion_order:
                node = Node(
                    event.identifier,
                    magnitud=event.magnitude,
                    profundidad_h=event.depth_km,
                    zona_poblada=event.populated_zone,
                )
                avl.insert(node)
                bst.insert(order_key(event))

            avl_metrics = EventPerformanceQueries._avl_metrics(avl.getRoot())
            comparisons.append({
                "order": order_name,
                "insertion_order": [event.identifier for event in insertion_order],
                "avl": avl_metrics,
                "bst": bst.metrics(),
                "searches": [
                    EventPerformanceQueries._compare_search(avl, bst, key)
                    for key in keys
                ],
            })

        return {"keys": [list(key) for key in keys], "results": comparisons}

    @staticmethod
    def _avl_search(tree, key):
        current = tree.getRoot()
        comparisons = 0
        while current is not None:
            comparisons += 1
            current_key = current.get_order_key()
            if current_key == key:
                return comparisons
            current = current.getLeftChild() if key < current_key else current.getRightChild()
        return comparisons

    @staticmethod
    def _compare_search(avl, bst, key):
        avl_comparisons = EventPerformanceQueries._avl_search(avl, key)
        return {
            "key": list(key),
            "avl_comparisons": avl_comparisons,
            "avl_nodes_examined": avl_comparisons,
            "bst_comparisons": bst.find_with_comparisons(key)["comparisons"],
        }

    @staticmethod
    def _avl_metrics(root):
        def visit(node):
            if node is None:
                return 0, 0, 0
            left_height, left_leaves, left_nodes = visit(node.getLeftChild())
            right_height, right_leaves, right_nodes = visit(node.getRightChild())
            leaves = (1 if node.getLeftChild() is None and node.getRightChild() is None
                      else left_leaves + right_leaves)
            return 1 + max(left_height, right_height), leaves, left_nodes + right_nodes + 1

        height, leaves, nodes = visit(root)
        return {"height": height, "leaves": leaves, "nodes": nodes}
