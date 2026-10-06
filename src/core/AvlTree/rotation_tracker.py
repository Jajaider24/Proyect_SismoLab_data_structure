"""Contexto opcional para observar rotaciones sin acoplar el dominio al AVL."""

from contextvars import ContextVar


_active_tracker = ContextVar("active_rotation_tracker", default=None)


class RotationTracker:
    def __init__(self):
        self.events = []
        self.cases = []

    def __enter__(self):
        self._token = _active_tracker.set(self)
        return self

    def __exit__(self, _type, _value, _traceback):
        _active_tracker.reset(self._token)


def record_rotation(rotation):
    tracker = _active_tracker.get()
    if tracker is not None:
        tracker.events.append(rotation)


def record_case(case):
    tracker = _active_tracker.get()
    if tracker is not None and case:
        tracker.cases.append(case)
