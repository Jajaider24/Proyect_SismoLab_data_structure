"""Pruebas para la lectura y validacion de listas JSON de nodos."""

import unittest

from src.repository.node_repository import leer_json_nodos, validar_ids_unicos
from src.repository.catalog_repository import leer_json_catalogo


class TestNodeRepository(unittest.TestCase):
    def test_accepts_unique_ids_and_json_text(self):
        nodes = '[{"id": 10}, {"id": 11}]'
        self.assertEqual(leer_json_nodos(nodes), [{"id": 10}, {"id": 11}])
        self.assertIs(validar_ids_unicos([{"id": 10}, {"id": 11}]), True)

    def test_rejects_duplicate_ids_and_invalid_shapes(self):
        self.assertIn("repetidos", validar_ids_unicos([{"id": 7}, {"id": 7}]))
        self.assertIsInstance(validar_ids_unicos([{"id": "7"}]), str)
        self.assertIsInstance(validar_ids_unicos({"id": 7}), str)
        with self.assertRaises(ValueError):
            leer_json_nodos("{mal json")

    def test_catalog_repository_reuses_unique_identifier_validation(self):
        self.assertEqual(
            leer_json_catalogo([{"identifier": 21}, {"identifier": 22}]),
            [{"identifier": 21}, {"identifier": 22}],
        )
        with self.assertRaisesRegex(ValueError, "repetidos"):
            leer_json_catalogo([{"id": 21}, {"id": 21}])


if __name__ == "__main__":
    unittest.main()
