"""Construccion de respuestas JSON del catalogo de eventos."""

from src.services.event_presenter import EventPresenter


class EventResponseBuilder:
    """Serializa eventos, arboles y metricas para la API HTTP."""

    @staticmethod
    def as_dict(event):
        """Convierte un evento de dominio en el contrato JSON de la API."""
        return EventPresenter.as_dict(event)

    def tree_data(self, store, avl_index):
        """Serializa el AVL de eventos activos con datos de dominio completos."""
        return avl_index.tree_data(store.active, self.as_dict)

    def response(self, store, avl_index, metrics, identifier=None):
        """Construye la respuesta comun con evento opcional, arbol y metricas."""
        event = store.get(identifier) if identifier is not None else None
        return {
            "event": self.as_dict(event) if event else None,
            "tree": self.tree_data(store, avl_index),
            "values": avl_index.values(),
            "metrics": metrics,
        }
