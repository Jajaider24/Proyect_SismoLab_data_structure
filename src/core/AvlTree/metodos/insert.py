"""Insercion y eliminacion recursivas de un arbol AVL."""

from src.core.AvlTree.metodos.balance import check_balance, update_height


def insert_node(current_root, node):
    """Inserta por identificador y retorna ``(raiz, insertado)``."""
    if current_root is None:
        node.setParent(None)
        node.setHeight(1)
        return node, True
    if node.getIdentifier() == current_root.getIdentifier():
        return current_root, False
    if node.getIdentifier() < current_root.getIdentifier():
        child_root, inserted = insert_node(current_root.getLeftChild(), node)
        if inserted:
            current_root.LeftChild = child_root
            child_root.setParent(current_root)
    else:
        child_root, inserted = insert_node(current_root.getRightChild(), node)
        if inserted:
            current_root.RightChild = child_root
            child_root.setParent(current_root)
    if not inserted:
        return current_root, False
    update_height(current_root)
    return check_balance(current_root), True


def _minimum(node):
    """Encuentra el menor identificador de un subarbol derecho."""
    while node.getLeftChild() is not None:
        node = node.getLeftChild()
    return node


def delete_node(current_root, identifier):
    """Elimina un identificador y retorna ``(raiz, eliminado)``."""
    if current_root is None:
        return None, False
    if identifier < current_root.getIdentifier():
        child_root, deleted = delete_node(current_root.getLeftChild(), identifier)
        current_root.LeftChild = child_root
        if child_root is not None:
            child_root.setParent(current_root)
    elif identifier > current_root.getIdentifier():
        child_root, deleted = delete_node(current_root.getRightChild(), identifier)
        current_root.RightChild = child_root
        if child_root is not None:
            child_root.setParent(current_root)
    else:
        # Con cero o un hijo, el hijo ocupa directamente el lugar del nodo.
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
        # Con dos hijos, copiamos el sucesor y eliminamos su nodo original.
        successor = _minimum(current_root.getRightChild())
        current_root.copy_data_from(successor)
        current_root.RightChild, deleted = delete_node(
            current_root.getRightChild(), successor.getIdentifier()
        )
        if current_root.RightChild is not None:
            current_root.RightChild.setParent(current_root)

    if not deleted:
        return current_root, False
    update_height(current_root)
    return check_balance(current_root), True
