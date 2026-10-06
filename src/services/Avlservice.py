"""Servicio reutilizable para operar y presentar arboles AVL."""

from src.core.AvlTree.metodos.balance import balance_factor
from src.core.AvlTree.tree import AVL_tree


class AVLTreeService:
    """Mantiene una instancia AVL y centraliza sus operaciones comunes.

    La instancia global al final del modulo es usada por las rutas ``/avl``.
    Otros casos de uso, como el catalogo de eventos, pueden crear su propio
    ``AVLTreeService`` para reutilizar la logica sin compartir estado.
    """

    def __init__(self, tree=None):
        """Inicializa el servicio con un arbol existente o uno nuevo vacio."""
        self.tree = tree or AVL_tree()

    def get_root(self):
        """Devuelve la raiz actual del arbol administrado por el servicio."""
        return self.tree.getRoot()

    def insert_node(self, node, rebalance=True):
        """Inserta un ``Node`` y devuelve False si su identificador ya existe."""
        return self.tree.insert(node, rebalance=rebalance)

    def find_node(self, identifier):
        """Busca por identificador aunque la clave tenga tres componentes."""
        return self.tree._find_by_identifier(self.tree.getRoot(), identifier)

    def delete_node(self, identifier, rebalance=True):
        """Elimina por identificador y deja que el AVL rebalancee ancestros."""
        return self.tree.delete(identifier, rebalance=rebalance)

    def audit(self):
        return self.tree.audit()

    def recover(self):
        return self.tree.recover()

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

    def iter_nodes_in_order(self):
        """Entrega los nodos en recorrido in-order segun la clave AVL."""
        nodes = []

        def traverse(node):
            """Acumula nodos visitando izquierda, raiz y derecha."""
            if node is None:
                return
            traverse(node.getLeftChild())
            nodes.append(node)
            traverse(node.getRightChild())

        traverse(self.get_root())
        return nodes

    def get_values(self):
        """Obtiene identificadores en recorrido in-order."""
        return [node.getIdentifier() for node in self.iter_nodes_in_order()]

    def serialize_tree(self, attributes_factory=None, extra_factory=None):
        """Convierte el AVL a jerarquia D3 con datos base y extensiones.

        Args:
            attributes_factory: Funcion opcional que recibe un nodo y devuelve
                el diccionario de atributos a exponer.
            extra_factory: Funcion opcional que recibe un nodo y devuelve pares
                adicionales para mezclar en cada item serializado.

        Returns:
            dict | None: Arbol serializado desde la raiz o ``None`` si no hay
            nodos.
        """
        def serialize(node):
            """Serializa recursivamente un nodo y sus hijos."""
            if node is None:
                return None
            children = [child for child in (
                serialize(node.getLeftChild()), serialize(node.getRightChild())
            ) if child is not None]
            attributes = (
                attributes_factory(node)
                if attributes_factory is not None
                else node.to_dict()
            )
            data = {
                "id": str(node.getIdentifier()),
                "value": node.getIdentifier(),
                "priority": node.getPriority(),
                "height": node.getHeight(),
                "balance_factor": balance_factor(node),
                "children": children,
                "attributes": attributes,
            }
            if extra_factory is not None:
                data.update(extra_factory(node))
            return data

        return serialize(self.get_root())

    def get_tree(self):
        """Convierte el arbol a jerarquia D3 con todos los datos del nodo."""
        return self.serialize_tree()

    def rebuild(self, nodes):
        """Reinicia el arbol e inserta una coleccion de nodos ya validados."""
        self.clear()
        for node in nodes:
            self.insert_node(node)

    def clear(self):
        """Reinicia la instancia en memoria."""
        self.tree = AVL_tree()


avl_tree_service = AVLTreeService()
