"""Pruebas de invariantes y de las cuatro rotaciones AVL."""

import unittest

from src.core.AvlTree.tree import AVL_tree
from src.core.node.node import Node


class TestAVL(unittest.TestCase):
    def assert_valid_avl(self, tree):
        def visit(node, lower=None, upper=None):
            if node is None:
                return 0
            self.assertTrue(lower is None or node.getValue() > lower)
            self.assertTrue(upper is None or node.getValue() < upper)
            left = visit(node.getLeftChild(), lower, node.getValue())
            right = visit(node.getRightChild(), node.getValue(), upper)
            self.assertLessEqual(abs(left - right), 1)
            self.assertEqual(node.getHeight(), 1 + max(left, right))
            if node is tree.getRoot():
                self.assertIsNone(node.getParent())
            return node.getHeight()

        visit(tree.getRoot())

    def build(self, values):
        tree = AVL_tree()
        for value in values:
            self.assertTrue(tree.insert(Node(value)))
        self.assert_valid_avl(tree)
        return tree

    def test_four_rotation_cases(self):
        for values in ([30, 20, 10], [10, 20, 30], [30, 10, 20], [10, 30, 20]):
            tree = self.build(values)
            self.assertEqual(tree.getRoot().getValue(), 20)

    def test_balance_propagates_to_root(self):
        tree = self.build(range(1, 100))
        self.assert_valid_avl(tree)

    def test_duplicate_is_not_inserted(self):
        tree = self.build([10, 5, 15])
        self.assertFalse(tree.insert(Node(10)))
        self.assert_valid_avl(tree)

    def test_delete_leaf_one_child_and_two_children(self):
        tree = self.build([50, 30, 70, 20, 40, 60, 80, 10, 35])
        for identifier in (10, 60, 30, 50):
            self.assertTrue(tree.delete(identifier))
            self.assert_valid_avl(tree)
        self.assertFalse(tree.delete(999))

    def test_node_business_attributes_are_validated(self):
        node = Node(7, 2.5, 100.0, "2026-09-30T18:00:00-05:00", "r1", "sensor", True)
        self.assertEqual(node.to_dict()["identificador"], 7)
        with self.assertRaises(ValueError):
            Node(0)
        with self.assertRaises(ValueError):
            Node(7, 2.55)
        with self.assertRaises(ValueError):
            Node(7, 2.0, 701.0)


if __name__ == "__main__":
    unittest.main()
