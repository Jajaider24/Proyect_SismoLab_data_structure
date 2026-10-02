"""Estructura publica del arbol AVL."""

from src.core.AvlTree.metodos.eliminar import delete_node
from src.core.AvlTree.metodos.insert import insert_node


class AVL_tree:
    """Arbol AVL ordenado por identificador."""

    def __init__(self):
        # La raiz cambia cuando una rotacion ocurre en el nivel superior.
        self.root = None

    def getRoot(self):
        """Obtiene la raiz actual del arbol."""
        return self.root

    def insert(self, node):
        """Inserta un nodo; False indica identificador duplicado."""
        self.root, inserted = insert_node(self.root, node)
        if self.root is not None:
            self.root.setParent(None)
        return inserted

    def delete(self, identifier):
        """Elimina el primer nodo con el identificador indicado."""
        target = self._find_by_identifier(self.root, identifier)
        if target is None:
            return False
        self.root, deleted = delete_node(self.root, target)
        if self.root is not None:
            self.root.setParent(None)
        return deleted

    def _find_by_identifier(self, current_root, identifier):
        """Busca por todo el arbol porque el orden ya no depende solo del id."""
        if current_root is None:
            return None
        if current_root.getIdentifier() == identifier:
            return current_root
        return (self._find_by_identifier(current_root.getLeftChild(), identifier)
                or self._find_by_identifier(current_root.getRightChild(), identifier))
