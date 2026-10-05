"""Pruebas de estructuras y reglas nuevas del escenario."""

import unittest
from datetime import datetime, timedelta, timezone

from src.core.bst import BinarySearchTree
from src.core.structures.queue import Queue
from src.core.structures.stack import Stack
from src.models.event import Event
from src.models.simulation_clock import SimulationClock
from src.models.zone import Zone, ZoneClassifier
from src.services.event_catalog import EventCatalog, EventValidationError


class TestScenarioStructures(unittest.TestCase):
    def test_bst_queue_and_stack(self):
        tree = BinarySearchTree()
        for value in (4, 2, 6, 1, 3):
            self.assertTrue(tree.insert(value))
        self.assertEqual(tree.inorder(), [1, 2, 3, 4, 6])
        self.assertTrue(tree.contains(3))
        self.assertFalse(tree.insert(3))

        queue = Queue()
        queue.enqueue("a")
        queue.enqueue("b")
        self.assertEqual(queue.dequeue(), "a")
        stack = Stack()
        stack.push("a")
        stack.push("b")
        self.assertEqual(stack.pop(), "b")

    def test_coordinate_boundaries_and_zone_overlap(self):
        classifier = ZoneClassifier((
            Zone("poblada", 0, 10, 0, 10, populated=True),
            Zone("no_poblada", 10, 20, 0, 10, populated=False),
        ))
        self.assertTrue(classifier.is_populated(10, 5))
        catalog = EventCatalog(classifier)
        when = datetime.now(timezone.utc)
        event = catalog.create(Event(1, 4.5, 20, 10, 5, when, "STA"))
        self.assertEqual(event.priority, 3)
        with self.assertRaises(EventValidationError):
            catalog.create(Event(2, 4.5, 20, 1000.1, 5, when, "STA"))

    def test_clock_rejects_future_occurrence(self):
        now = datetime(2026, 10, 5, tzinfo=timezone.utc)
        clock = SimulationClock(now)
        with self.assertRaises(ValueError):
            clock.validate_occurrence(now + timedelta(seconds=1))