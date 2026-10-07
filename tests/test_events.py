"""Pruebas de los casos de uso del catalogo de eventos."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from src.core.AvlTree.rotation_tracker import RotationTracker
from src.controllers import event_controller
from src.models.event import AttentionState, Event, EventState
from src.models.simulation_clock import SimulationClock
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

    def test_import_events_is_iterative_and_undone_as_one_action(self):
        imported = self.catalog.import_events([
            self.event(identifier=3),
            self.event(identifier=1),
            self.event(identifier=2),
        ])

        self.assertEqual([event.identifier for event in imported], [3, 1, 2])
        self.assertEqual(self.catalog.metrics()["active"], 3)
        self.assertEqual(self.catalog.history_count(), 1)
        audit = self.catalog.status()["audit"]
        self.assertTrue(audit["valid_bst"])
        self.assertTrue(audit["valid_heights"])
        self.assertTrue(audit["valid_depths"])
        self.assertTrue(audit["balanced"])

        self.catalog.undo()
        self.assertEqual(self.catalog.metrics()["active"], 0)
        self.assertEqual(self.catalog.history_count(), 0)

    def test_import_events_rejects_invalid_batch_without_partial_insertion(self):
        with self.assertRaises(EventValidationError):
            self.catalog.import_events([
                self.event(identifier=3),
                self.event(identifier=3),
            ])

        self.assertEqual(self.catalog.metrics()["active"], 0)
        self.assertEqual(self.catalog.history_count(), 0)

    def test_catalog_does_not_load_or_save_automatically(self):
        class RepositorySpy:
            loads = 0
            saves = 0

            def load(self):
                self.loads += 1
                return {"schema_version": 1, "state": None, "versions": []}

            def save(self, _document):
                self.saves += 1

        repository = RepositorySpy()
        catalog = EventCatalog(repository=repository)

        self.assertEqual(catalog.metrics()["active"], 0)
        catalog.create(self.event())
        self.assertEqual(repository.loads, 0)
        self.assertEqual(repository.saves, 0)

    def test_complete_export_import_preserves_state_history_and_versions(self):
        self.catalog.create(self.event(identifier=1))
        self.catalog.save_version("base")
        self.catalog.create(self.event(identifier=2))
        exported = self.catalog.export_state()

        restored = EventCatalog()
        restored.load_state(exported)

        self.assertEqual(restored.metrics()["active"], 2)
        self.assertEqual([version["name"] for version in restored.list_versions()], ["base"])
        self.assertEqual(restored.history_count(), self.catalog.history_count() + 1)
        restored.restore_version("base")
        self.assertEqual(restored.metrics()["active"], 1)
        self.assertIsNotNone(restored.get(1))

    def test_controller_imports_json_nodes_and_rejects_duplicate_ids(self):
        catalog = EventCatalog(clock=SimulationClock(self.when))
        nodes = [
            {
                "id": 2,
                "magnitud": 4.2,
                "profundidad_h": 30,
                "fecha_hora": self.when.isoformat(),
                "procedencia": "STA-2",
            },
            {"id": 1, "magnitude": 3.5, "station": "STA-1"},
        ]
        with patch.object(event_controller, "event_catalog", catalog):
            event_controller.import_json_nodes(nodes)
            self.assertEqual(catalog.metrics()["active"], 2)
            self.assertEqual(catalog.get(2).magnitude, 4.2)
            self.assertEqual(catalog.get(1).station, "STA-1")
            self.assertEqual(catalog.history_count(), 1)

            with self.assertRaises(HTTPException) as error:
                event_controller.import_json_nodes([{"id": 4}, {"id": 4}])
            self.assertEqual(error.exception.status_code, 422)
            self.assertEqual(catalog.metrics()["active"], 2)

            with self.assertRaises(HTTPException) as error:
                event_controller.import_json_nodes([{"id": 4, "fecha_hora": 123}])
            self.assertEqual(error.exception.status_code, 422)
            self.assertEqual(catalog.metrics()["active"], 2)

    def test_update_only_reinserts_when_priority_inputs_change(self):
        self.catalog.create(self.event())
        original_node = self.catalog.tree._find_by_identifier(
            self.catalog.tree.getRoot(), 1
        )

        updated = self.catalog.update(
            1,
            self.event(
                station="STA-2",
                when=self.when + timedelta(minutes=5),
                x=10,
                y=10,
            ),
        )
        same_node = self.catalog.tree._find_by_identifier(
            self.catalog.tree.getRoot(), 1
        )
        self.assertIs(same_node, original_node)
        self.assertEqual(same_node.getNodeDepth(), 1)
        self.assertEqual(updated.station, "STA-2")
        self.assertEqual(same_node.procedencia, "STA-2")
        self.assertEqual(same_node.x, 10)
        self.assertEqual(same_node.fecha_hora, updated.occurred_at.isoformat())

        self.catalog.update(1, self.event(magnitude=5.0))
        reinserted_node = self.catalog.tree._find_by_identifier(
            self.catalog.tree.getRoot(), 1
        )
        self.assertIsNot(reinserted_node, original_node)

        self.catalog.update(1, self.event(magnitude=5.0, depth=25.0))
        depth_updated_node = self.catalog.tree._find_by_identifier(
            self.catalog.tree.getRoot(), 1
        )
        self.assertIsNot(depth_updated_node, reinserted_node)
        self.assertEqual(depth_updated_node.profundidad_h, 25.0)

    def test_update_reinserts_when_coordinates_change_priority_zone(self):
        from src.models.zone import Zone, ZoneClassifier

        zone_catalog = EventCatalog(
            zone_classifier=ZoneClassifier((
                Zone("populated", 10, 20, 10, 20, populated=True),
            ))
        )
        zone_catalog.create(self.event(magnitude=5.0, depth=20, x=0, y=0))
        original_node = zone_catalog.tree._find_by_identifier(
            zone_catalog.tree.getRoot(), 1
        )
        self.assertEqual(zone_catalog.get(1).priority, 2)

        zone_catalog.update(
            1,
            self.event(magnitude=5.0, depth=20, x=15, y=15),
        )
        updated_node = zone_catalog.tree._find_by_identifier(
            zone_catalog.tree.getRoot(), 1
        )
        self.assertIsNot(updated_node, original_node)
        self.assertTrue(zone_catalog.get(1).populated_zone)
        self.assertEqual(zone_catalog.get(1).priority, 3)

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

    def test_old_archive_uses_strict_age_and_validates_threshold(self):
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        catalog = EventCatalog(clock=SimulationClock(now))
        catalog.create(self.event(when=now - timedelta(hours=72)))
        actions_before = catalog.history_count()

        preview = catalog.preview_old_branch_archive()
        self.assertFalse(preview["eligible"])
        self.assertEqual(preview["threshold_hours"], 72)
        result = catalog.archive_old_branch(72, [])
        self.assertFalse(result["archived"])
        self.assertEqual(catalog.metrics()["active"], 1)
        self.assertEqual(catalog.metrics()["archived"], 0)
        self.assertEqual(catalog.history_count(), actions_before)

        with self.assertRaises(EventValidationError):
            catalog.preview_old_branch_archive(0)
        with self.assertRaises(EventValidationError):
            catalog.preview_old_branch_archive(float("inf"))
        with self.assertRaises(EventValidationError):
            catalog.preview_old_branch_archive(10 ** 10000)

        fresh_catalog = EventCatalog(clock=SimulationClock(now))
        fresh_catalog.create(self.event(when=now - timedelta(hours=72, seconds=1)))
        self.assertTrue(fresh_catalog.preview_old_branch_archive()["eligible"])

        priority_catalog = EventCatalog(clock=SimulationClock(now))
        priority_catalog.create(
            self.event(
                magnitude=4.5,
                depth=100,
                when=now - timedelta(hours=100),
            )
        )
        self.assertEqual(priority_catalog.get(1).priority, 2)
        self.assertFalse(priority_catalog.preview_old_branch_archive()["eligible"])

        whole_tree_catalog = EventCatalog(clock=SimulationClock(now))
        whole_tree_catalog.create(
            self.event(when=now - timedelta(hours=100))
        )
        whole_tree_preview = whole_tree_catalog.preview_old_branch_archive()
        self.assertEqual(whole_tree_preview["identifiers"], [1])
        whole_tree_catalog.archive_old_branch(
            72, whole_tree_preview["identifiers"]
        )
        self.assertIsNone(whole_tree_catalog.response()["tree"])
        whole_tree_catalog.undo()
        self.assertEqual(whole_tree_catalog.metrics()["active"], 1)

    def test_old_archive_selects_largest_branch_and_uses_id_tiebreak(self):
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        catalog = EventCatalog(clock=SimulationClock(now))
        for identifier in (4, 2, 6, 1, 3, 5, 7):
            age = 24 if identifier == 4 else 100
            catalog.create(
                self.event(
                    identifier=identifier,
                    when=now - timedelta(hours=age),
                )
            )

        preview = catalog.preview_old_branch_archive(72)
        self.assertEqual(preview["eligible_branches"], 6)
        self.assertEqual(preview["root_identifier"], 6)
        self.assertEqual(preview["count"], 3)
        self.assertEqual(preview["identifiers"], [6, 5, 7])
        self.assertIn("mayor identificador (6)", preview["reason"])

        archived_associations = {
            identifier: catalog.get(identifier).associations
            for identifier in preview["identifiers"]
        }
        actions_before = catalog.history_count()
        rotations = RotationTracker()
        catalog._rotation_tracker = rotations
        with rotations:
            result = catalog.archive_old_branch(72, preview["identifiers"])
        catalog._rotation_tracker = None
        self.assertTrue(result["archived"])
        self.assertEqual(result["archived_identifiers"], [6, 5, 7])
        self.assertEqual(catalog.metrics()["active"], 4)
        self.assertEqual(catalog.metrics()["archived"], 3)
        self.assertEqual(catalog.history_count(), actions_before + 1)
        self.assertTrue(rotations.events)
        for identifier in preview["identifiers"]:
            archived_event = catalog.get(identifier)
            self.assertEqual(archived_event.state, EventState.ARCHIVED)
            self.assertEqual(archived_event.associations, archived_associations[identifier])

        catalog.undo()
        self.assertEqual(catalog.metrics()["active"], 7)
        self.assertEqual(catalog.metrics()["archived"], 0)
        self.assertEqual(catalog.get(6).state, EventState.ACTIVE)

    def test_old_archive_prefers_deeper_subtree_when_sizes_tie(self):
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        catalog = EventCatalog(clock=SimulationClock(now))
        recent_identifiers = {4, 6, 8}
        for identifier in (8, 4, 12, 2, 6, 10, 1, 5, 7):
            age = 24 if identifier in recent_identifiers else 100
            catalog.create(
                self.event(
                    identifier=identifier,
                    when=now - timedelta(hours=age),
                )
            )

        preview = catalog.preview_old_branch_archive(72)
        self.assertEqual(preview["count"], 2)
        self.assertEqual(preview["root_identifier"], 2)
        self.assertEqual(preview["root_depth"], 3)
        self.assertEqual(preview["identifiers"], [2, 1])
        self.assertIn("mayor profundidad (3)", preview["reason"])

    def test_old_archive_keeps_stress_order_and_rejects_stale_preview(self):
        now = datetime(2026, 10, 6, tzinfo=timezone.utc)
        catalog = EventCatalog(clock=SimulationClock(now))
        catalog.set_stress_mode(True)
        for identifier in range(1, 6):
            age = 24 if identifier == 1 else 100
            catalog.create(
                self.event(
                    identifier=identifier,
                    when=now - timedelta(hours=age),
                )
            )

        preview = catalog.preview_old_branch_archive(72)
        self.assertEqual(preview["identifiers"], [2, 3, 4, 5])
        catalog.create(
            self.event(
                identifier=6,
                when=now - timedelta(hours=100),
            )
        )
        with self.assertRaises(EventValidationError):
            catalog.archive_old_branch(72, preview["identifiers"])
        self.assertEqual(catalog.metrics()["active"], 6)

        refreshed_preview = catalog.preview_old_branch_archive(72)
        self.assertEqual(refreshed_preview["identifiers"], [2, 3, 4, 5, 6])
        result = catalog.archive_old_branch(
            72, refreshed_preview["identifiers"]
        )
        self.assertEqual(result["archived_identifiers"], [2, 3, 4, 5, 6])
        self.assertEqual(catalog.tree.getRoot().getIdentifier(), 1)
        self.assertEqual(catalog.status()["mode"], "stress")
        catalog.undo()
        self.assertFalse(catalog.status()["audit"]["balanced"])
        self.assertEqual(catalog.metrics()["active"], 6)

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

    def test_enqueue_reports_batch_preserves_fifo_and_is_one_undo_action(self):
        self.catalog.enqueue_report(self.event(identifier=30))
        before_actions = self.catalog.history_count()
        count = self.catalog.enqueue_reports([
            self.event(identifier=20, station="STA-2"),
            self.event(identifier=10, station="STA-3"),
        ])

        self.assertEqual(count, 3)
        self.assertEqual(
            [item["identificador"] for item in self.catalog.pending_reports()],
            [30, 20, 10],
        )
        self.assertEqual(self.catalog.history_count(), before_actions + 1)

        self.catalog.undo()
        self.assertEqual(
            [item["identificador"] for item in self.catalog.pending_reports()],
            [30],
        )

    def test_import_json_catalog_rejects_duplicates_and_invalid_batch_atomically(self):
        catalog = EventCatalog(clock=SimulationClock(self.when))
        valid_report = {
            "id": 5,
            "magnitud": 4.0,
            "profundidad_h": 12.0,
            "fecha_hora": self.when.isoformat(),
            "procedencia": "STA-5",
        }
        with patch.object(event_controller, "event_catalog", catalog):
            with self.assertRaises(HTTPException) as error:
                event_controller.import_json_catalog([
                    valid_report,
                    {**valid_report},
                ])
            self.assertEqual(error.exception.status_code, 422)
            self.assertEqual(catalog.pending_reports_count(), 0)

            invalid_report = {**valid_report, "id": 6, "magnitud": 100}
            with self.assertRaises(HTTPException) as error:
                event_controller.import_json_catalog([valid_report, invalid_report])
            self.assertEqual(error.exception.status_code, 422)
            self.assertEqual(catalog.pending_reports_count(), 0)

            result = event_controller.import_json_catalog([
                {**valid_report, "id": 7},
                {**valid_report, "id": 8},
            ])
            self.assertEqual(result["imported_reports"], 2)
            self.assertEqual(
                [report["identificador"] for report in result["queue"]],
                [7, 8],
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
        self.assertEqual(data["tree"]["profundidad_nodo"], 1)

    def test_tree_response_serializes_depth_after_rotations(self):
        for identifier in (1, 2, 3):
            self.catalog.create(self.event(identifier=identifier))

        tree = self.catalog.response()["tree"]
        self.assertEqual(tree["value"], 2)
        self.assertEqual(tree["profundidad_nodo"], 1)
        self.assertTrue(all(child["profundidad_nodo"] == 2 for child in tree["children"]))

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
