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