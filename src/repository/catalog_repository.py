"""Lectura y validacion de catalogos JSON destinados a la cola de reportes."""

from src.repository.node_repository import leer_json_nodos


def leer_json_catalogo(documento):
    """Lee una lista de reportes y exige IDs enteros unicos en el archivo."""
    return leer_json_nodos(documento)
