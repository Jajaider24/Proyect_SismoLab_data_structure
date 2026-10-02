"""Insercion recursiva de nodos en el arbol AVL."""

from src.core.AvlTree.metodos.balance import check_balance, update_height


def left(current_node, node_to_insert):
    """Indica si el nodo nuevo debe ubicarse a la izquierda.

    El orden se decide por prioridad, despues por magnitud y finalmente por
    identificador. De esta forma todos los nodos tienen una posicion unica.
    """
    current_key = (
        current_node.getPriority(),
        current_node.getMagnitude(),
        current_node.getIdentifier(),
    )
    insert_key = (
        node_to_insert.getPriority(),
        node_to_insert.getMagnitude(),
        node_to_insert.getIdentifier(),
    )
    return insert_key < current_key


def _same_order_values(first_node, second_node):
    """Evita insertar dos nodos con los tres criterios identicos."""
    return (
        first_node.getPriority() == second_node.getPriority()
        and first_node.getMagnitude() == second_node.getMagnitude()
        and first_node.getIdentifier() == second_node.getIdentifier()
    )


def insert_node(current_root, node):
    """Inserta ``node`` y devuelve ``(nueva_raiz, insertado)``."""
    if current_root is None:
        node.setParent(None)
        node.setHeight(1)
        return node, True
    if _same_order_values(current_root, node):
        return current_root, False
    if left(current_root, node):
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
