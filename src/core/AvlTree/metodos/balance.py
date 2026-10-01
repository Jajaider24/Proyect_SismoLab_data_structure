"""Calculo de alturas, factores de balance y reparacion de un AVL."""

from .rotaciones import giroSimpleDerecha, giroSimpleIzquierda


def get_height(node):
    """Devuelve cero para un enlace vacio y la altura real para un nodo."""
    # Tratar un enlace vacio como altura cero evita condicionales en cada formula.
    return 0 if node is None else node.getHeight()


def update_height(node):
    """Actualiza la altura del nodo usando las alturas de sus hijos."""
    # Una referencia vacia no tiene altura que actualizar.
    if node is None:
        return 0
    # La altura es uno mas que el hijo de mayor profundidad.
    height = 1 + max(get_height(node.getLeftChild()), get_height(node.getRightChild()))
    # Guardamos el resultado para que las siguientes operaciones sean O(1).
    node.setHeight(height)
    return height


def balance_factor(node):
    """Calcula izquierda menos derecha; un AVL valido queda entre -1 y 1."""
    # Un nodo inexistente no puede desbalancear a su padre.
    if node is None:
        return 0
    # El signo indica hacia que lado debe girarse el subarbol.
    return get_height(node.getLeftChild()) - get_height(node.getRightChild())


def balance_case(node):
    """Identifica LL, RR, LR o RL a partir del nodo desbalanceado."""
    factor = balance_factor(node)
    if factor > 1:
        return "LL" if balance_factor(node.getLeftChild()) >= 0 else "LR"
    if factor < -1:
        return "RR" if balance_factor(node.getRightChild()) <= 0 else "RL"
    return ""


def check_balance(node):
    """Rebalancea un nodo y devuelve la nueva raiz de su subarbol."""
    # La recursion de insercion/eliminacion puede llegar a un enlace vacio.
    if node is None:
        return None
    # Primero recalculamos: el factor debe representar el estado actual.
    update_height(node)
    # Una sola cadena puede requerir una rotacion simple o doble.
    case = balance_case(node)
    if case == "LL":
        return giroSimpleDerecha(node)
    if case == "RR":
        return giroSimpleIzquierda(node)
    if case == "LR":
        giroSimpleIzquierda(node.getLeftChild())
        return giroSimpleDerecha(node)
    if case == "RL":
        giroSimpleDerecha(node.getRightChild())
        return giroSimpleIzquierda(node)
    return node
