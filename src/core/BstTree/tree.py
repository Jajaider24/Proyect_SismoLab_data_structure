from collections import deque

from src.core.node.node import Node


class BST:
    """Binary search tree that stores values through shared Node objects."""

    def __init__(self):
        self.root = None

    def insert(self, node):
        if not isinstance(node, Node):
            raise TypeError("node must be an instance of Node")
        node.setParent(None)
        node.setLeftChild(None)
        node.setRightChild(None)

        if self.root is None:
            self.root = node
            return node

        current = self.root
        while True:
            if node.getValue() == current.getValue():
                raise ValueError(f"El valor {node.getValue()} ya existe en el árbol.")
            if node.getValue() < current.getValue():
                if current.getLeftChild() is None:
                    current.setLeftChild(node)
                    node.setParent(current)
                    return node
                current = current.getLeftChild()
            else:
                if current.getRightChild() is None:
                    current.setRightChild(node)
                    node.setParent(current)
                    return node
                current = current.getRightChild()

    def search(self, value):
        current = self.root
        while current is not None:
            if value == current.getValue():
                return current
            current = (
                current.getLeftChild()
                if value < current.getValue()
                else current.getRightChild()
            )
        return None

    def delete(self, value):
        node = self.search(value)
        if node is None:
            return None

        if node.getLeftChild() is not None and node.getRightChild() is not None:
            predecessor = self.getPredecessor(node)
            node.setValue(predecessor.getValue())
            node = predecessor

        child = node.getLeftChild() or node.getRightChild()
        self._replace_in_parent(node, child)
        node.setParent(None)
        node.setLeftChild(None)
        node.setRightChild(None)
        return node

    def _replace_in_parent(self, node, replacement):
        parent = node.getParent()
        if parent is None:
            self.root = replacement
        elif parent.getLeftChild() is node:
            parent.setLeftChild(replacement)
        else:
            parent.setRightChild(replacement)
        if replacement is not None:
            replacement.setParent(parent)

    def getPredecessor(self, node):
        current = node.getLeftChild()
        if current is None:
            raise ValueError("El nodo no tiene subárbol izquierdo.")
        while current.getRightChild() is not None:
            current = current.getRightChild()
        return current

    def getMin(self):
        self._require_root()
        current = self.root
        while current.getLeftChild() is not None:
            current = current.getLeftChild()
        return current

    def getMax(self):
        self._require_root()
        current = self.root
        while current.getRightChild() is not None:
            current = current.getRightChild()
        return current

    def breadthFirstSearch(self):
        self._require_root()
        queue = deque([self.root])
        result = []
        while queue:
            current = queue.popleft()
            result.append(current.getValue())
            if current.getLeftChild() is not None:
                queue.append(current.getLeftChild())
            if current.getRightChild() is not None:
                queue.append(current.getRightChild())
        return result

    def preOrderTraversal(self):
        self._require_root()
        return self._traverse("pre")

    def inOrderTraversal(self):
        self._require_root()
        return self._traverse("in")

    def posOrderTraversal(self):
        self._require_root()
        return self._traverse("post")

    def _traverse(self, order):
        result = []

        def visit(node):
            if node is None:
                return
            if order == "pre":
                result.append(node.getValue())
            visit(node.getLeftChild())
            if order == "in":
                result.append(node.getValue())
            visit(node.getRightChild())
            if order == "post":
                result.append(node.getValue())

        visit(self.root)
        return result

    def calculateHeight(self, node):
        if node is None:
            return -1
        return 1 + max(
            self.calculateHeight(node.getLeftChild()),
            self.calculateHeight(node.getRightChild()),
        )

    def draw(self):
        if self.root is None:
            print("El árbol está vacío.")
            return
        self._draw(self.root, "", "R")

    def _draw(self, node, space, position):
        if node is None:
            return
        self._draw(node.getRightChild(), space + "     ", "D")
        print(space + position + "-- " + str(node.getValue()))
        self._draw(node.getLeftChild(), space + "     ", "I")

    def _require_root(self):
        if self.root is None:
            raise ValueError("El árbol está vacío.")