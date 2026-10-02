"""Casos de uso del arbol AVL para la capa HTTP."""

from src.core.AvlTree.metodos.balance import balance_factor
from src.core.AvlTree.tree import AVL_tree
from src.core.node.node import Node


class AVLTreeService:
    """Mantiene la instancia del arbol y oculta sus detalles al controlador."""

    def __init__(self):
        self.tree = AVL_tree()

    def insert_node(self, node):
        """Inserta un ``Node`` y devuelve False si su identificador ya existe."""
        return self.tree.insert(node)

    def find_node(self, identifier):
        """Busca por identificador aunque la clave tenga tres componentes."""
        return self.tree._find_by_identifier(self.tree.getRoot(), identifier)

    def delete_node(self, identifier):
        """Elimina por identificador y deja que el AVL rebalancee ancestros."""
        return self.tree.delete(identifier)

    def update_node(self, original_identifier, node):
        """Edita atributos; si cambia la clave, elimina e inserta de nuevo."""
        current = self.find_node(original_identifier)
        if current is None:
            return "not_found"
        duplicate = self.find_node(node.getIdentifier())
        if duplicate is not None and duplicate is not current:
            return "duplicate"
        if duplicate is current and node.get_order_key() == current.get_order_key():
            current.copy_data_from(node)
            return "updated"
        self.tree.delete(original_identifier)
        self.tree.insert(node)
        return "updated"

    def get_values(self):
        """Obtiene identificadores en recorrido in-order."""
        values = []

        def traverse(node):
            if node is None:
                return
            traverse(node.getLeftChild())
            values.append(node.getIdentifier())
            traverse(node.getRightChild())

        traverse(self.tree.getRoot())
        return values

    def get_tree(self):
        """Convierte el arbol a jerarquia D3 con todos los datos del nodo."""
        def serialize(node):
            if node is None:
                return None
            children = [child for child in (
                serialize(node.getLeftChild()), serialize(node.getRightChild())
            ) if child is not None]
            return {
                "id": str(node.getIdentifier()),
                "value": node.getIdentifier(),
                "priority": node.getPriority(),
                "height": node.getHeight(),
                "balance_factor": balance_factor(node),
                "children": children,
                "attributes": node.to_dict(),
            }
        return serialize(self.tree.getRoot())

    def clear(self):
        """Reinicia la instancia en memoria."""
        self.tree = AVL_tree()


avl_tree_service = AVLTreeService()
