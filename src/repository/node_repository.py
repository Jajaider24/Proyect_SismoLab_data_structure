"""Lectura y validacion de documentos JSON de nodos."""

import json


def validar_ids_unicos(nodos):
    """Valida que el documento sea una lista de nodos con IDs enteros unicos."""
    if not isinstance(nodos, list):
        return "El JSON debe contener una lista de nodos."

    vistos = set()
    for indice, nodo in enumerate(nodos):
        if not isinstance(nodo, dict):
            return f"El nodo en la posicion {indice + 1} debe ser un objeto JSON."
        node_id = nodo.get("id", nodo.get("identifier", nodo.get("identificador")))
        if isinstance(node_id, bool) or not isinstance(node_id, int):
            return f"El nodo en la posicion {indice + 1} debe tener un ID entero."
        if node_id in vistos:
            return f"Hay nodos repetidos: el ID {node_id} aparece mas de una vez."
        vistos.add(node_id)

    return True


def leer_json_nodos(documento):
    """Lee texto JSON o valida una lista ya decodificada por la API."""
    if isinstance(documento, str):
        try:
            documento = json.loads(documento)
        except json.JSONDecodeError as error:
            raise ValueError(f"El archivo no contiene JSON valido: {error.msg}.") from error

    resultado = validar_ids_unicos(documento)
    if resultado is not True:
        raise ValueError(resultado)
    return documento