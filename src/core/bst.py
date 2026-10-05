"""BST manual para comparaciones del escenario."""


class _Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, key):
        if self.root is None:
            self.root = _Node(key)
            return True
        current = self.root
        while True:
            if key == current.key:
                return False
            if key < current.key:
                if current.left is None:
                    current.left = _Node(key)
                    return True
                current = current.left
            else:
                if current.right is None:
                    current.right = _Node(key)
                    return True
                current = current.right

    def contains(self, key):
        current = self.root
        while current is not None:
            if key == current.key:
                return True
            current = current.left if key < current.key else current.right
        return False

    def inorder(self):
        values = []

        def visit(node):
            if node is None:
                return
            visit(node.left)
            values.append(node.key)
            visit(node.right)

        visit(self.root)
        return values