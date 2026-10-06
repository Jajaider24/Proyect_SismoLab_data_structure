"""Cobertura de consultas de desempeño sobre eventos y estructuras."""

import unittest
from datetime import datetime, timedelta, timezone

from main import app
from src.models.event import Event, EventState
from src.services.eventCatalog_Service import EventCatalog


class TestPerformanceQueries(unittest.TestCase):
    def setUp(self):
        self.catalog = EventCatalog()
        self.when = datetime(2026, 10, 1, tzinfo=timezone.utc)

    def test_analysis_routes_are_registered(self):
        paths = {route.path for route in app.routes}
        self.assertTrue({
            "/events/analysis/pending",
            "/events/analysis/magnitude",
            "/events/analysis/depth",
            "/events/analysis/associations/{identifier}",
            "/events/analysis/costly-high-priority",
            "/events/analysis/compare",
        }.issubset(paths))

    def add_event(self, identifier, magnitude=3.0, depth=20.0, minutes=0, station="STA"):
        return self.catalog.create(Event(
            identifier=identifier,
            magnitude=magnitude,
            depth_km=depth,
            x=0,
            y=0,
            occurred_at=self.when + timedelta(minutes=minutes),
            station=station,
        ))

    def test_top_k_uses_descending_event_key_and_review_keeps_key(self):
        self.add_event(3, magnitude=3.0)
        self.add_event(1, magnitude=4.0)
        self.add_event(2, magnitude=3.0)
        key_before = self.catalog._avl_index.tree.getRoot().get_order_key()
        root_before = self.catalog.tree.getRoot()

        result = self.catalog.query_pending_top(2)

        self.assertEqual([item["identifier"] for item in result["events"]], [1, 3])
        self.assertLessEqual(result["nodes_examined"], 3)
        self.catalog.review(1)
        self.assertIs(root_before, self.catalog.tree.getRoot())
        self.assertEqual(key_before, self.catalog.tree.getRoot().get_order_key())
        self.assertEqual(
            [item["identifier"] for item in self.catalog.query_pending_top(10)["events"]],
            [3, 2],
        )

    def test_inclusive_magnitude_and_depth_date_ranges(self):
        self.add_event(1, magnitude=3.0, depth=10, minutes=0)
        self.add_event(2, magnitude=4.0, depth=20, minutes=30)
        self.add_event(3, magnitude=5.0, depth=21, minutes=60)

        magnitude = self.catalog.query_magnitude_range(3.0, 4.0)
        depth = self.catalog.query_shallow_depth(
            20,
            self.when,
            self.when + timedelta(minutes=30),
        )

        self.assertEqual({event["identifier"] for event in magnitude["events"]}, {1, 2})
        self.assertEqual({event["identifier"] for event in depth["events"]}, {1, 2})
        self.assertEqual(magnitude["nodes_examined"], 3)
        self.assertEqual(depth["nodes_examined"], 3)

    def test_associations_include_archived_candidates_and_states(self):
        self.add_event(2, minutes=10)
        self.add_event(1, minutes=0)
        self.catalog.archive_branch(1)

        result = self.catalog.query_associations(1)

        self.assertEqual(result["selected_reference"]["identifier"], 1)
        self.assertEqual(result["selected_reference"]["state"], EventState.ARCHIVED.value)
        self.assertEqual(result["candidates"][0]["identifier"], 2)
        self.assertEqual(result["candidates"][0]["state"], EventState.ACTIVE.value)
        self.assertEqual(result["nodes_examined"], 0)

    def test_costly_priority_search_and_structure_comparison(self):
        for identifier in range(1, 8):
            self.add_event(identifier, magnitude=6.0)

        costly = self.catalog.query_costly_high_priority(1)
        comparison = self.catalog.compare_structures()

        self.assertTrue(costly["events"])
        self.assertTrue(all(item["search_nodes_visited"] > 0 for item in costly["events"]))
        self.assertEqual(
            [item["order"] for item in comparison["results"]],
            ["catalog_order", "ascending", "descending"],
        )
        ascending = comparison["results"][1]
        descending = comparison["results"][2]
        self.assertEqual(ascending["avl"]["nodes"], ascending["bst"]["nodes"])
        self.assertEqual(descending["avl"]["nodes"], descending["bst"]["nodes"])
        self.assertGreaterEqual(
            descending["bst"]["height"], descending["avl"]["height"]
        )
        self.assertTrue(all(
            search["avl_comparisons"] > 0 and search["bst_comparisons"] > 0
            for search in descending["searches"]
        ))


if __name__ == "__main__":
    unittest.main()
