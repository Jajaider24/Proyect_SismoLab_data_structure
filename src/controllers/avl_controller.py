"""Controladores: validan casos de uso y traducen errores a HTTP."""

import logging

from fastapi import HTTPException, status

from src.services.Avlservice import avl_tree_service

logger = logging.getLogger(__name__)


def _node_from_payload(payload):
    """Construye el modelo y convierte errores de dominio a respuestas 422."""
    try:
        return payload.to_node()
    except ValueError as error:
        logger.error("[422] Datos del nodo invalidos: %s", error)
        raise HTTPException(status_code=422, detail=str(error)) from error


def insert_node(payload):
    """Inserta el nodo completo recibido desde la UI."""
    node = _node_from_payload(payload)
    try:
        if not avl_tree_service.insert_node(node):
            logger.warning("[409] El identificador %s ya existe", node.getIdentifier())
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"El identificador {node.getIdentifier()} ya existe.")
        logger.info("[201] Nodo %s insertado y arbol balanceado", node.getIdentifier())
        return _tree_response(201, f"Nodo {node.getIdentifier()} insertado correctamente.")
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[500] Error insertando nodo: %s", error)
        raise HTTPException(status_code=500, detail="No fue posible insertar el nodo.") from error


def insert_legacy_value(value):
    """Conserva la ruta anterior creando un nodo con datos por defecto."""
    from src.core.node.node import Node
    return insert_node(_LegacyPayload(Node(value)))


def update_node(identifier, payload):
    """Actualiza atributos, permitiendo cambiar tambien el identificador."""
    node = _node_from_payload(payload)
    try:
        result = avl_tree_service.update_node(identifier, node)
        if result == "not_found":
            logger.warning("[404] No existe el identificador %s", identifier)
            raise HTTPException(status_code=404, detail="El nodo no existe.")
        if result == "duplicate":
            logger.warning("[409] El identificador %s ya existe", node.getIdentifier())
            raise HTTPException(status_code=409, detail="El nuevo identificador ya existe.")
        logger.info("[200] Nodo %s actualizado", identifier)
        return _tree_response(200, "Nodo actualizado correctamente.")
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[500] Error actualizando nodo %s: %s", identifier, error)
        raise HTTPException(status_code=500, detail="No fue posible actualizar el nodo.") from error


def delete_node(identifier):
    """Elimina un nodo y deja el rebalanceo en la estructura AVL."""
    try:
        if not avl_tree_service.delete_node(identifier):
            logger.warning("[404] No existe el identificador %s", identifier)
            raise HTTPException(status_code=404, detail="El nodo no existe.")
        logger.info("[200] Nodo %s eliminado y arbol balanceado", identifier)
        return _tree_response(200, "Nodo eliminado correctamente.")
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("[500] Error eliminando nodo %s: %s", identifier, error)
        raise HTTPException(status_code=500, detail="No fue posible eliminar el nodo.") from error


def get_tree():
    """Entrega el estado serializado para D3 y la seleccion de nodos."""
    return _tree_response(200, "Arbol AVL obtenido correctamente.")


def clear_tree():
    """Elimina todos los nodos de la instancia en memoria."""
    avl_tree_service.clear()
    logger.info("[200] Arbol AVL reiniciado")
    return _tree_response(200, "Arbol AVL reiniciado.")


def _tree_response(code, message):
    """Centraliza el formato que consumen API y UI."""
    return {"status_code": code, "message": message,
            "data": {"values": avl_tree_service.get_values(),
                     "tree": avl_tree_service.get_tree()}}


class _LegacyPayload:
    """Adaptador interno para no duplicar la logica de insercion antigua."""
    def __init__(self, node):
        self.node = node

    def to_node(self):
        return self.node
