"""Pruebas de los casos de uso del catalogo de eventos."""

import unittest
from datetime import datetime, timedelta, timezone

from src.models.event import AttentionState, Event, EventState
from src.services.eventCatalog_Service import EventCatalog
from src.services.eventCatalog.exceptions import EventNotFound, EventValidationError


class TestEventCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = EventCatalog()
        self.when = datetime(2026, 10, 5, tzinfo=timezone.utc)

    def event(self, identifier=1, revision=1, magnitude=4.0, station="STA-1",
              when=None, x=0.0, y=0.0, depth=20.0):
        return Event(
            identifier, magnitude, depth, x, y,
            when or self.when, station, revision=revision,
        )

    def test_create_review_update_and_undo_delete(self):
        self.catalog.create(self.event())
        self.assertEqual(self.catalog.review(1).attention, AttentionState.REVIEWED)
        updated = self.catalog.update(1, self.event(magnitude=5.0))
        self.assertEqual(updated.revision, 2)
        self.assertEqual(updated.attention, AttentionState.PENDING)
        self.catalog.delete(1)
        self.assertEqual(self.catalog.get(1).state, EventState.DELETED)
        self.catalog.undo()
        self.assertEqual(self.catalog.get(1).state, EventState.ACTIVE)

    def test_identifier_is_immutable_and_not_reusable(self):
        self.catalog.create(self.event())
        with self.assertRaises(EventValidationError):
            self.catalog.update(1, self.event(identifier=2))
        self.catalog.delete(1)
        with self.assertRaises(EventValidationError):
            self.catalog.create(self.event())

    def test_report_revision_rules(self):
        self.assertEqual(self.catalog.process_report(self.event())['status'], 'created')
        same = self.event(station="STA-2")
        self.assertEqual(self.catalog.process_report(same)['status'], 'confirmed')
        conflict = self.event(magnitude=4.1, station="STA-3")
        self.assertEqual(self.catalog.process_report(conflict)['status'], 'conflict')
        self.assertEqual(
            self.catalog.process_report(
                self.event(revision=2, magnitude=5.0, station="STA-5")
            )['status'],
            'updated',
        )
        stale = self.event(revision=1, station="STA-4")
        self.assertEqual(self.catalog.process_report(stale)['status'], 'stale')

    def test_first_report_can_start_above_revision_one(self):
        result = self.catalog.process_report(self.event(revision=4))
        self.assertEqual(result['status'], 'created')
        self.assertEqual(result['event'].revision, 4)

    def test_archived_event_reactivates_only_with_newer_report(self):
        self.catalog.create(self.event())
        self.catalog.archive_branch(1)
        self.assertEqual(self.catalog.get(1).state, EventState.ARCHIVED)
        old = self.event(station="STA-2")
        self.assertEqual(self.catalog.process_report(old)['status'], 'confirmed')
        self.assertEqual(self.catalog.get(1).state, EventState.ARCHIVED)
        newer = self.event(revision=2, station="STA-2")
        self.assertEqual(self.catalog.process_report(newer)['status'], 'updated')
        self.assertEqual(self.catalog.get(1).state, EventState.ACTIVE)

    def test_associations_are_recomputed(self):
        self.catalog.create(self.event())
        self.catalog.create(self.event(identifier=2, when=self.when + timedelta(minutes=10)))
        self.assertEqual(self.catalog.get(1).associations, {2})
        self.assertEqual(self.catalog.get(2).associations, {1})

    def test_stress_queue_processes_one_report_and_keeps_fifo_order(self):
        first = self.event(identifier=20, station="STA-1")
        second = self.event(identifier=10, station="STA-2")
        self.catalog.enqueue_report(first)
        self.catalog.enqueue_report(second)
        self.assertEqual(
            [item["identificador"] for item in self.catalog.pending_reports()], [20, 10]
        )
        result = self.catalog.process_next_report()
        self.assertEqual(result["report"]["identifier"], 20)
        self.assertEqual(result["status"], "created")
        self.assertEqual(
            [item["identificador"] for item in self.catalog.pending_reports()], [10]
        )

    def test_stress_mode_defers_rotations_and_recovery_preserves_order(self):
        self.catalog.set_stress_mode(True)
        for identifier in (1, 2, 3, 4, 5):
            self.catalog.create(self.event(identifier=identifier))
        before = self.catalog.status()
        self.assertEqual(before["mode"], "stress")
        self.assertFalse(before["audit"]["balanced"])
        with self.assertRaises(EventValidationError):
            self.catalog.set_stress_mode(False)
        result = self.catalog.recover()
        self.assertEqual(result["mode"], "normal")
        self.assertTrue(result["after"]["balanced"])
        self.assertTrue(result["after"]["valid_bst"])
        self.assertEqual(self.catalog.response()["values"], [1, 2, 3, 4, 5])

    def test_report_trace_contains_rotations(self):
        self.catalog.create(self.event(identifier=50, magnitude=4.0))
        self.catalog.create(self.event(identifier=20, magnitude=4.0))
        self.catalog.enqueue_report(self.event(identifier=10, magnitude=4.0, revision=1))
        result = self.catalog.process_next_report()
        self.assertIn("rotations", result)
        self.assertTrue(result["rotations"])

    def test_event_coordinates_are_saved_in_avl_node_attributes(self):
        self.catalog.create(self.event(identifier=9, x=123.4, y=567.8))
        data = self.catalog.response(9)
        self.assertEqual(self.catalog.tree.getRoot().getX(), 123.4)
        self.assertEqual(self.catalog.tree.getRoot().getY(), 567.8)
        self.assertEqual(data["tree"]["attributes"]["x"], 123.4)
        self.assertEqual(data["tree"]["attributes"]["y"], 567.8)

    def test_replicas_filter_active_and_archived_by_time_and_distance(self):
        self.catalog.create(self.event(identifier=1, x=0, y=0, depth=0))
        self.catalog.create(self.event(identifier=2, x=3, y=4, depth=0))
        self.catalog.create(self.event(
            identifier=3,
            x=6,
            y=8,
            depth=0,
            when=self.when + timedelta(hours=1),
        ))
        self.catalog.create(self.event(
            identifier=4,
            x=1,
            y=1,
            depth=1,
            when=self.when + timedelta(hours=3),
        ))
        self.catalog.create(self.event(identifier=5, x=2, y=0, depth=0))
        self.catalog.archive_branch(5)
        self.catalog.create(self.event(identifier=6, x=1, y=0, depth=0))
        self.catalog.delete(6)

        result = self.catalog.find_replicas(1, radius_km=10, window_hours=2)
        self.assertEqual(
            [item["identifier"] for item in result["replicas"]],
            [5, 2, 3],
        )
        self.assertEqual(result["replicas"][0]["state"], EventState.ARCHIVED)
        self.assertEqual(result["replicas"][1]["distance_km"], 5.0)
        self.assertNotIn(4, [item["identifier"] for item in result["replicas"]])
        self.assertNotIn(6, [item["identifier"] for item in result["replicas"]])


if __name__ == "__main__":
    unittest.main()
