"""Rotaciones AVL y reconexion de subarboles."""


def _replace_child(parent, old_child, new_child):
    """Reemplaza el enlace que apunta al subarbol que acaba de girar."""
    if parent is None:
        return
    if parent.getLeftChild() is old_child:
        parent.LeftChild = new_child
    elif parent.getRightChild() is old_child:
        parent.RightChild = new_child
    if new_child is not None:
        new_child.setParent(parent)


def giroSimpleDerecha(superior):
    """Gira a la derecha y devuelve la nueva raiz del subarbol LL."""
    if superior is None or superior.getLeftChild() is None:
        return superior
    # Import local: balance importa estas rotaciones y asi evitamos un ciclo.
    from .balance import update_height
    mitad = superior.getLeftChild()
    aux = mitad.getRightChild()
    parent = superior.getParent()
    _replace_child(parent, superior, mitad)
    mitad.RightChild = superior
    mitad.setParent(parent)
    superior.LeftChild = aux
    superior.setParent(mitad)
    if aux is not None:
        aux.setParent(superior)
    # La altura se actualiza desde la unica implementacion del modulo balance.
    update_height(superior)
    update_height(mitad)
    return mitad


def giroSimpleIzquierda(superior):
    """Gira a la izquierda y devuelve la nueva raiz del subarbol RR."""
    if superior is None or superior.getRightChild() is None:
        return superior
    from .balance import update_height
    mitad = superior.getRightChild()
    aux = mitad.getLeftChild()
    parent = superior.getParent()
    _replace_child(parent, superior, mitad)
    mitad.LeftChild = superior
    mitad.setParent(parent)
    superior.RightChild = aux
    superior.setParent(mitad)
    if aux is not None:
        aux.setParent(superior)
    update_height(superior)
    update_height(mitad)
    return mitad
