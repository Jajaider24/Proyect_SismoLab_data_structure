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

    def find_with_comparisons(self, key):
        """Busca una clave y cuenta cuántos nodos compara."""
        current = self.root
        comparisons = 0
        while current is not None:
            comparisons += 1
            if key == current.key:
                return {"found": True, "comparisons": comparisons}
            current = current.left if key < current.key else current.right
        return {"found": False, "comparisons": comparisons}

    def metrics(self):
        """Calcula altura, hojas y cantidad de nodos en una pasada."""
        if self.root is None:
            return {"height": 0, "leaves": 0, "nodes": 0}
        height = leaves = nodes = 0
        pending = [(self.root, 1)]
        while pending:
            node, depth = pending.pop()
            nodes += 1
            height = max(height, depth)
            if node.left is None and node.right is None:
                leaves += 1
            if node.left is not None:
                pending.append((node.left, depth + 1))
            if node.right is not None:
                pending.append((node.right, depth + 1))
        return {"height": height, "leaves": leaves, "nodes": nodes}

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
