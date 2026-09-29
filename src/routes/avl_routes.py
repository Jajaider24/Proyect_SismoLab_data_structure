from fastapi import APIRouter
from pydantic import BaseModel

from src.controllers.avl_controller import insert_value

router = APIRouter(prefix="/avl", tags=["AVL"])




@router.post("/insert/{value}")
def insert_avl_node(value:int):
    return insert_value(value)