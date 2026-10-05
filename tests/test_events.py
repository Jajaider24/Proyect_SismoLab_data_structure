"""Pruebas de los casos de uso del catalogo de eventos."""

import unittest
from datetime import datetime, timedelta, timezone

from src.models.event import AttentionState, Event, EventState
from src.services.event_catalog import EventCatalog, EventNotFound, EventValidationError


class TestEventCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog = EventCatalog()
        self.when = datetime(2026, 10, 5, tzinfo=timezone.utc)

    def event(self, identifier=1, revision=1, magnitude=4.0, station="STA-1", when=None):
        return Event(
            identifier, magnitude, 20.0, 0.0, 0.0,
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
        stale = self.event(revision=0, station="STA-4")
        self.assertEqual(self.catalog.process_report(stale)['status'], 'stale')
        newer = self.event(revision=2, magnitude=5.0, station="STA-5")
        self.assertEqual(self.catalog.process_report(newer)['status'], 'updated')

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


if __name__ == "__main__":
    unittest.main()