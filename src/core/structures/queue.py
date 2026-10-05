"""Cola FIFO explicita para reportes pendientes."""

from collections import deque


class Queue:
    def __init__(self):
        self._items = deque()

    def enqueue(self, item):
        self._items.append(item)

    def dequeue(self):
        if not self._items:
            raise IndexError("cola vacia")
        return self._items.popleft()

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)