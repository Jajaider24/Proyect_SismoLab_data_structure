from src.core.AvlTree.metodos.insert import insert_node
from src.core.node.node import Node


class AVL_tree:
    """class AVL"""

    def __init__(self):
        """AVL inicializado"""
        self.root = None

    def getRoot(self):
        """Obtener raiz del árbol"""
        return self.root


    def insert(self,node):
        """insertar nodo en el árbol"""
        if self.root is None:
            self.root = node
            node.setParent(None)
            node.setHeight(1)
            return True
        else:
            self.root, inserted = insert_node(self.root,node)
            self.root.setParent(None)
            return inserted

        