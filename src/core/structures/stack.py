"""Pila LIFO explicita para acciones reversibles."""


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pila vacia")
        return self._items.pop()

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def items(self):
        """Devuelve una copia ordenada desde el fondo hasta la cima."""
        return list(self._items)

    def restore(self, items):
        """Reemplaza el contenido usando una secuencia desde el fondo."""
        self._items = list(items)
