"""Pruebas de invariantes y de las cuatro rotaciones AVL."""

import unittest

from src.core.AvlTree.tree import AVL_tree
from src.core.AvlTree.metodos.insert import left
from src.core.node.node import Node
from src.services.Avlservice import AVLTreeService


class TestAVL(unittest.TestCase):
    def assert_valid_avl(self, tree):
        def visit(node, lower=None, upper=None, expected_depth=1):
            if node is None:
                return 0
            key = node.get_order_key()
            self.assertTrue(lower is None or key > lower)
            self.assertTrue(upper is None or key < upper)
            self.assertEqual(node.getNodeDepth(), expected_depth)
            left = visit(node.getLeftChild(), lower, key, expected_depth + 1)
            right = visit(node.getRightChild(), key, upper, expected_depth + 1)
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
        node = Node(7, prioridad=2.5, magnitud=1.0, profundidad_h=100.0,
                    x=12.3, y=45.6,
                    fecha_hora="2026-09-30T18:00:00-05:00", revision="r1",
                    procedencia="sensor", estado_atencion=True)
        self.assertEqual(node.to_dict()["identificador"], 7)
        self.assertEqual(node.to_dict()["profundidad_nodo"], 1)
        self.assertEqual(node.getX(), 12.3)
        self.assertEqual(node.getY(), 45.6)
        node.setX(100.0)
        node.setY(200.0)
        self.assertEqual(node.to_dict()["x"], 100.0)
        self.assertEqual(node.to_dict()["y"], 200.0)
        with self.assertRaises(ValueError):
            Node(0)
        with self.assertRaises(ValueError):
            Node(7, magnitud=2.55)
        with self.assertRaises(ValueError):
            Node(7, profundidad_h=701.0)
        with self.assertRaises(ValueError):
            Node(7, x=1000.1)
        with self.assertRaises(ValueError):
            node.setY(-0.1)

    def test_left_uses_priority_magnitude_and_identifier(self):
        current = Node(20, magnitud=4.5, profundidad_h=100.0)
        self.assertTrue(left(current, Node(30, magnitud=2.0)))
        self.assertTrue(left(current, Node(10, magnitud=4.5, profundidad_h=100.0)))
        self.assertFalse(left(current, Node(30, magnitud=6.0)))
        self.assertFalse(left(current, Node(20, magnitud=4.5, profundidad_h=100.0)))

    def test_priority_is_part_of_avl_order_and_duplicate_key(self):
        tree = AVL_tree()
        self.assertTrue(tree.insert(Node(10, magnitud=4.5, profundidad_h=100.0)))
        self.assertTrue(tree.insert(Node(20, magnitud=2.0)))
        self.assertFalse(tree.insert(Node(10, magnitud=4.5, profundidad_h=100.0)))
        self.assert_valid_avl(tree)

    def test_priority_is_calculated_from_business_data(self):
        self.assertEqual(Node(1, magnitud=6.0).getPriority(), 3)
        self.assertEqual(Node(2, magnitud=4.5, profundidad_h=30.0,
                              zona_poblada=True).getPriority(), 3)
        self.assertEqual(Node(3, magnitud=4.5, profundidad_h=30.1,
                              zona_poblada=True).getPriority(), 2)
        self.assertEqual(Node(4, magnitud=4.4, zona_poblada=True).getPriority(), 1)

    def test_service_update_preserves_node_for_non_priority_inputs(self):
        service = AVLTreeService()
        service.insert_node(Node(10))
        service.insert_node(Node(20))
        original = service.find_node(10)

        self.assertEqual(
            service.update_node(
                10,
                Node(
                    10,
                    x=50,
                    y=60,
                    fecha_hora="2026-10-06T10:00:00+00:00",
                    revision="2",
                    procedencia="STA-2",
                ),
            ),
            "updated",
        )
        self.assertIs(service.find_node(10), original)
        self.assertEqual(original.getX(), 50)
        self.assertEqual(original.getY(), 60)
        self.assertEqual(original.procedencia, "STA-2")

        self.assertEqual(
            service.update_node(10, Node(10, profundidad_h=40)),
            "updated",
        )
        self.assertIsNot(service.find_node(10), original)
        self.assertEqual(service.find_node(10).profundidad_h, 40)


if __name__ == "__main__":
    unittest.main()
