"""Estructura publica del arbol AVL."""

from src.core.AvlTree.metodos.insert import delete_node, insert_node


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
        """Elimina por identificador y rebalancea todos los ancestros."""
        self.root, deleted = delete_node(self.root, identifier)
        if self.root is not None:
            self.root.setParent(None)
        return deleted
