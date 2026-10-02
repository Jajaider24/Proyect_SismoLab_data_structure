"""Eliminacion AVL separada de la logica de insercion."""

from src.core.AvlTree.metodos.balance import check_balance, update_height


def _minimun(node):
    """Obtiene el nodo con menor identificador de un subarbol."""
    # El sucesor in-order siempre esta en el extremo izquierdo del subarbol.
    while node.getLeftChild() is not None:
        node = node.getLeftChild()
    return node


def delete_node(current_root, identifier):
    """Elimina por clave de orden y devuelve ``(nueva_raiz, eliminado)``."""
    if current_root is None:
        return None, False
    # El llamador entrega el nodo completo para conservar los tres criterios.
    if identifier.get_order_key() < current_root.get_order_key():
        child_root, deleted = delete_node(current_root.getLeftChild(), identifier)
        current_root.LeftChild = child_root
        if child_root is not None:
            child_root.setParent(current_root)
    elif identifier.get_order_key() > current_root.get_order_key():
        child_root, deleted = delete_node(current_root.getRightChild(), identifier)
        current_root.RightChild = child_root
        if child_root is not None:
            child_root.setParent(current_root)
    else:
        if current_root.getLeftChild() is None:
            replacement = current_root.getRightChild()
            if replacement is not None:
                replacement.setParent(current_root.getParent())
            return replacement, True
        if current_root.getRightChild() is None:
            replacement = current_root.getLeftChild()
            if replacement is not None:
                replacement.setParent(current_root.getParent())
            return replacement, True
        successor = _minimun(current_root.getRightChild())
        current_root.copy_data_from(successor)
        current_root.RightChild, deleted = delete_node(
            current_root.getRightChild(), successor
        )
        if current_root.RightChild is not None:
            current_root.RightChild.setParent(current_root)

    if not deleted:
        return current_root, False
    update_height(current_root)
    return check_balance(current_root), True
