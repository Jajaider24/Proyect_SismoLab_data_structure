"""Estructura publica del arbol AVL."""

from src.core.AvlTree.metodos.eliminar import delete_node
from src.core.AvlTree.metodos.insert import insert_node
from src.core.AvlTree.metodos.balance import balance_factor, update_depths, update_height
from src.core.AvlTree.metodos.rotaciones import giroSimpleDerecha, giroSimpleIzquierda
from src.core.AvlTree.rotation_tracker import RotationTracker, record_case


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
        """Revisa limites globales, ids unicos, alturas y balance por nodo."""
        reports = {}
        identifiers = set()
        visited = set()
        heights = {}
        node_count = 0
        unbalanced = False
        stack = [(self.root, None, None, 1, False)]
        while stack:
            node, lower, upper, expected_depth, postorder = stack.pop()
            if node is None:
                continue
            marker = id(node)
            identifier = node.getIdentifier()
            if not postorder:
                if marker in visited:
                    reports.setdefault(identifier, {"identifier": identifier, "issues": []})["issues"].append(
                        "cycle_or_shared_node"
                    )
                    continue
                visited.add(marker)
                node_count += 1
                reports[marker] = {"identifier": identifier, "issues": []}
                issues = reports[marker]["issues"]
                key = node.get_order_key()
                if (lower is not None and key <= lower) or (upper is not None and key >= upper):
                    issues.append("global_order")
                if identifier in identifiers:
                    issues.append("duplicate_identifier")
                identifiers.add(identifier)
                if (node.getLeftChild() is not None and node.getLeftChild().getParent() is not node
                        or node.getRightChild() is not None and node.getRightChild().getParent() is not node):
                    issues.append("parent_reference")
                if expected_depth == 1 and node.getParent() is not None:
                    issues.append("root_parent_reference")
                stack.append((node, lower, upper, expected_depth, True))
                stack.append((node.getRightChild(), key, upper, expected_depth + 1, False))
                stack.append((node.getLeftChild(), lower, key, expected_depth + 1, False))
                continue

            left = node.getLeftChild()
            right = node.getRightChild()
            left_height = heights.get(id(left), -1) if left is not None else -1
            right_height = heights.get(id(right), -1) if right is not None else -1
            expected_height = 1 + max(left_height, right_height)
            factor = left_height - right_height
            heights[marker] = expected_height
            issues = reports[marker]["issues"]
            if node.getHeight() != expected_height:
                issues.append("height")
            if node.getNodeDepth() != expected_depth:
                issues.append("depth")
            if abs(factor) > 1:
                unbalanced = True
                issues.append("balance")
            if issues:
                reports[marker].update({
                    "stored_height": node.getHeight(),
                    "expected_height": expected_height,
                    "balance_factor": factor,
                    "depth": node.getNodeDepth(),
                    "expected_depth": expected_depth,
                })

        event_reports = [report for report in reports.values() if report["issues"]]
        issue_codes = {issue for report in event_reports for issue in report["issues"]}
        return {
            "balanced": not unbalanced,
            "valid_bst": not bool(issue_codes & {"global_order", "duplicate_identifier", "cycle_or_shared_node"}),
            "valid_heights": "height" not in issue_codes,
            "valid_depths": not bool(issue_codes & {"depth", "parent_reference", "root_parent_reference"}),
            "nodes": node_count,
            "violations": sorted(issue_codes),
            "events": event_reports,
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
                        record_case("LR")
                        giroSimpleIzquierda(node.getLeftChild())
                    else:
                        record_case("LL")
                    node = giroSimpleDerecha(node)
                else:
                    if balance_factor(node.getRightChild()) > 0:
                        record_case("RL")
                        giroSimpleDerecha(node.getRightChild())
                    else:
                        record_case("RR")
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
        return {
            "rotations": tracker.events,
            "cases": tracker.cases,
            "visited": visited,
            "audit": self.audit(),
        }
