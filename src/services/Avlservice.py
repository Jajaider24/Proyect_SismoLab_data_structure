from src.core.AvlTree.tree import AVL_tree
from src.core.node.node import Node


class AVLTreeService:
    def __init__(self):
        self.tree = AVL_tree()

    def insert_node(self, value: int):
        return self.tree.insert(Node(value))

    def get_values(self):
        values = []

        def traverse(node):
            if node is None:
                return
            traverse(node.getLeftChild())
            values.append(node.getValue())
            traverse(node.getRightChild())

        traverse(self.tree.getRoot())
        return values


avl_tree_service = AVLTreeService()