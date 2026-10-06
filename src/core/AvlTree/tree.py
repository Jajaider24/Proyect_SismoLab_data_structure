"""Estructura publica del arbol AVL."""

from src.core.AvlTree.metodos.eliminar import delete_node
from src.core.AvlTree.metodos.insert import insert_node
from src.core.AvlTree.metodos.balance import balance_factor, update_depths, update_height
from src.core.AvlTree.metodos.rotaciones import giroSimpleDerecha, giroSimpleIzquierda
from src.core.AvlTree.rotation_tracker import RotationTracker


class AVL_tree:
    """Arbol AVL ordenado por identificador."""

    def __init__(self):
        # La raiz cambia cuando una rotacion ocurre en el nivel superior.
        self.root = None

    def getRoot(self):
        """Obtiene la raiz actual del arbol."""
        return self.root

    def insert(self, node, rebalance=True):
        """Inserta un nodo; False indica identificador duplicado."""
        self.root, inserted = insert_node(self.root, node, rebalance)
        if self.root is not None:
            self.root.setParent(None)
            update_depths(self.root)
        return inserted

    def delete(self, identifier, rebalance=True):
        """Elimina el primer nodo con el identificador indicado."""
        target = self._find_by_identifier(self.root, identifier)
        if target is None:
            return False
        self.root, deleted = delete_node(self.root, target, rebalance)
        if self.root is not None:
            self.root.setParent(None)
            update_depths(self.root)
        return deleted

    def _find_by_identifier(self, current_root, identifier):
        """Busca por todo el arbol porque el orden ya no depende solo del id."""
        if current_root is None:
            return None
        if current_root.getIdentifier() == identifier:
            return current_root
        return (self._find_by_identifier(current_root.getLeftChild(), identifier)
                or self._find_by_identifier(current_root.getRightChild(), identifier))

    def audit(self):
        """Audita orden BST, alturas, profundidades y balance sin modificar."""
        violations = []
        nodes = 0

        def visit(node, lower=None, upper=None, expected_depth=1):
            nonlocal nodes
            if node is None:
                return 0
            nodes += 1
            key = node.get_order_key()
            if lower is not None and key <= lower:
                violations.append("bst-left-right")
            if upper is not None and key >= upper:
                violations.append("bst-order")
            left_height = visit(
                node.getLeftChild(), lower, key, expected_depth + 1
            )
            right_height = visit(
                node.getRightChild(), key, upper, expected_depth + 1
            )
            if node.getNodeDepth() != expected_depth:
                violations.append("depth")
            expected = 1 + max(left_height, right_height)
            if node.getHeight() != expected:
                violations.append("height")
            if abs(left_height - right_height) > 1:
                violations.append("balance")
            return expected

        visit(self.root)
        return {
            "balanced": not any(item == "balance" for item in violations),
            "valid_bst": not any(item.startswith("bst") for item in violations),
            "valid_heights": "height" not in violations,
            "valid_depths": "depth" not in violations,
            "nodes": nodes,
            "violations": violations,
        }

    def recover(self):
        """Equilibra localmente el mismo BST mediante rotaciones repetidas."""
        tracker = RotationTracker()
        visited = 0

        def recover_subtree(node):
            nonlocal visited
            if node is None:
                return None
            recover_subtree(node.getLeftChild())
            recover_subtree(node.getRightChild())
            visited += 1
            update_height(node)
            while abs(balance_factor(node)) > 1:
                if balance_factor(node) > 1:
                    if balance_factor(node.getLeftChild()) < 0:
                        giroSimpleIzquierda(node.getLeftChild())
                    node = giroSimpleDerecha(node)
                else:
                    if balance_factor(node.getRightChild()) > 0:
                        giroSimpleDerecha(node.getRightChild())
                    node = giroSimpleIzquierda(node)
                update_height(node)
            return node

        with tracker:
            while True:
                self.root = recover_subtree(self.root)
                if self.root is not None:
                    self.root.setParent(None)
                    update_depths(self.root)
                audit = self.audit()
                if (audit["valid_bst"] and audit["balanced"]
                        and audit["valid_heights"] and audit["valid_depths"]):
                    break
        return {"rotations": tracker.events, "visited": visited, "audit": self.audit()}
