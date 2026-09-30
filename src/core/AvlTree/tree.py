from collections import deque

from src.core.node.node import Node


class AVL:
    """Self-balancing binary search tree backed by shared Node objects."""

    def __init__(self):
        self.root = None

    def getRoot(self):
        return self.root

    def insert(self, node):
        self._validate_node(node)
        node.setParent(None)
        node.setLeftChild(None)
        node.setRightChild(None)
        node.setHeight(0)

        if self.root is None:
            self.root = node
            return True

        current = self.root
        while True:
            if node.getValue() == current.getValue():
                raise ValueError(f"El valor {node.getValue()} ya existe en el árbol.")
            if node.getValue() < current.getValue():
                child = current.getLeftChild()
                if child is None:
                    current.setLeftChild(node)
                    node.setParent(current)
                    self._rebalance_from(current)
                    return True
            else:
                child = current.getRightChild()
                if child is None:
                    current.setRightChild(node)
                    node.setParent(current)
                    self._rebalance_from(current)
                    return True
            current = child

    def search(self, value):
        if self.root is None:
            raise ValueError("El árbol está vacío.")

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
        if self.root is None:
            return None

        node = self.search(value)
        if node is None:
            return None

        if node.getLeftChild() is not None and node.getRightChild() is not None:
            predecessor = self.getPredecessor(node)
            node.setValue(predecessor.getValue())
            node = predecessor

        parent = node.getParent()
        child = node.getLeftChild() or node.getRightChild()
        self._replace_child_in_parent(parent, node, child)

        node.setParent(None)
        node.setLeftChild(None)
        node.setRightChild(None)
        node.setHeight(0)
        self._rebalance_from(parent)
        return node

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

    def calculateHeight(self, node):
        if node is None:
            return -1
        return node.getHeight()

    def getBalanceFactor(self, node):
        if node is None:
            return 0
        return self.calculateHeight(node.getLeftChild()) - self.calculateHeight(
            node.getRightChild()
        )

    def draw(self):
        if self.root is None:
            print("El árbol está vacío.")
            return
        print("\nÁrbol AVL:")
        print("-----------")
        self._draw(self.root, "", "R")

    def _rebalance_from(self, node):
        current = node
        while current is not None:
            self._update_height(current)
            balance = self.getBalanceFactor(current)
            if balance > 1:
                if self.getBalanceFactor(current.getLeftChild()) < 0:
                    self._rotate_left(current.getLeftChild())
                current = self._rotate_right(current)
            elif balance < -1:
                if self.getBalanceFactor(current.getRightChild()) > 0:
                    self._rotate_right(current.getRightChild())
                current = self._rotate_left(current)
            current = current.getParent()

    def _rotate_right(self, top_node):
        middle_node = top_node.getLeftChild()
        if middle_node is None:
            raise RuntimeError("No se puede girar a la derecha sin hijo izquierdo.")

        parent = top_node.getParent()
        middle_right = middle_node.getRightChild()
        self._replace_child_in_parent(parent, top_node, middle_node)
        middle_node.setRightChild(top_node)
        top_node.setParent(middle_node)
        top_node.setLeftChild(middle_right)
        if middle_right is not None:
            middle_right.setParent(top_node)

        self._update_height(top_node)
        self._update_height(middle_node)
        return middle_node

    def _rotate_left(self, top_node):
        middle_node = top_node.getRightChild()
        if middle_node is None:
            raise RuntimeError("No se puede girar a la izquierda sin hijo derecho.")

        parent = top_node.getParent()
        middle_left = middle_node.getLeftChild()
        self._replace_child_in_parent(parent, top_node, middle_node)
        middle_node.setLeftChild(top_node)
        top_node.setParent(middle_node)
        top_node.setRightChild(middle_left)
        if middle_left is not None:
            middle_left.setParent(top_node)

        self._update_height(top_node)
        self._update_height(middle_node)
        return middle_node

    def _replace_child_in_parent(self, parent, old_child, new_child):
        if parent is None:
            self.root = new_child
        elif parent.getLeftChild() is old_child:
            parent.setLeftChild(new_child)
        else:
            parent.setRightChild(new_child)
        if new_child is not None:
            new_child.setParent(parent)

    def _update_height(self, node):
        node.setHeight(
            1
            + max(
                self.calculateHeight(node.getLeftChild()),
                self.calculateHeight(node.getRightChild()),
            )
        )

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

    def _draw(self, node, space, position):
        if node is None:
            return
        self._draw(node.getRightChild(), space + "     ", "D")
        print(space + position + "-- " + str(node.getValue()))
        self._draw(node.getLeftChild(), space + "     ", "I")

    def _require_root(self):
        if self.root is None:
            raise ValueError("El árbol está vacío.")

    @staticmethod
    def _validate_node(node):
        if not isinstance(node, Node):
            raise TypeError("node must be an instance of Node")


AVL_tree = AVL

