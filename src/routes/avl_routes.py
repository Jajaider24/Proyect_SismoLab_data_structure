"""Rutas HTTP publicas para crear, editar, eliminar y consultar el AVL."""

from typing import Optional

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.controllers.avl_controller import (clear_tree, delete_node,
                                             get_tree, insert_legacy_value,
                                             insert_node, update_node)
from src.core.node.node import Node

router = APIRouter(prefix="/avl", tags=["AVL"])


class NodePayload(BaseModel):
    """Contrato HTTP de los atributos editables de un nodo."""
    identificador: int
    magnitud: float = 0.0
    profundidad_h: float = 0.0
    x: float = 0.0
    y: float = 0.0
    fecha_hora: Optional[str] = None
    revision: str = ""
    procedencia: str = ""
    estado_atencion: bool = False
    zona_poblada: bool = False

    def to_node(self):
        """Entrega el modelo de dominio, donde viven las reglas estrictas."""
        return Node(**self.model_dump())


@router.post("/nodes", status_code=status.HTTP_201_CREATED)
def create_avl_node(payload: NodePayload):
    """Crea un nodo con todos sus atributos."""
    return insert_node(payload)


@router.post("/insert/{value}", status_code=status.HTTP_201_CREATED)
def insert_avl_node(value: int):
    """Ruta de compatibilidad: inserta solo el identificador."""
    return insert_legacy_value(value)


@router.put("/nodes/{identifier}")
def update_avl_node(identifier: int, payload: NodePayload):
    """Edita los atributos del nodo indicado."""
    return update_node(identifier, payload)


@router.delete("/nodes/{identifier}")
def delete_avl_node(identifier: int):
    """Elimina por identificador y rebalancea el arbol."""
    return delete_node(identifier)


@router.get("/tree")
def get_avl_tree():
    """Obtiene la jerarquia completa para D3."""
    return get_tree()


@router.delete("/tree")
def delete_avl_tree():
    """Reinicia el arbol en memoria."""
    return clear_tree()
