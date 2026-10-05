"""Casos de uso y estado del catalogo de eventos."""

from src.core.AvlTree.metodos.balance import balance_factor
from src.core.AvlTree.tree import AVL_tree
from src.core.node.node import Node
from src.models.event import AttentionState, Event, EventState
from src.models.event_key import EventKey
from src.models.zone import ZoneClassifier
from src.services.event_policies import AssociationPolicy, PriorityPolicy
from src.services.event_presenter import EventPresenter


class EventValidationError(ValueError):
    """Error de datos de dominio antes de mutar el catalogo."""


class EventNotFound(LookupError):
    """El identificador no existe en el estado solicitado."""


class EventCatalog:
    """Orquesta eventos sin mezclar su estado con la estructura AVL."""

    def __init__(self, zone_classifier=None):
        self.tree = AVL_tree()
        self._active = {}
        self._archived = {}
        self._deleted = {}
        self._nodes_by_id = {}
        self._history = []
        self._zone_classifier = zone_classifier or ZoneClassifier()
        self._association_policy = AssociationPolicy()

    def _validate(self, event):
        if not isinstance(event.identifier, int) or not 1 <= event.identifier <= 999999:
            raise EventValidationError("identificador debe ser un entero entre 1 y 999999.")
        if not isinstance(event.station, str) or not event.station.strip():
            raise EventValidationError("station es obligatorio.")
        if not -2.0 <= event.magnitude <= 10.0:
            raise EventValidationError("magnitud fuera de rango.")
        if not 0.0 <= event.depth_km <= 700.0:
            raise EventValidationError("profundidad fuera de rango.")
        if not -90.0 <= event.latitude <= 90.0:
            raise EventValidationError("latitud fuera de rango.")
        if not -180.0 <= event.longitude <= 180.0:
            raise EventValidationError("longitud fuera de rango.")
        if event.revision < 1:
            raise EventValidationError("revision debe ser positiva.")

    def _prepare(self, event):
        self._validate(event)
        prepared = event.copy()
        prepared.populated_zone = self._zone_classifier.is_populated(
            prepared.latitude, prepared.longitude
        )
        prepared.priority = PriorityPolicy.calculate(
            prepared.magnitude, prepared.depth_km, prepared.populated_zone
        )
        prepared.state = EventState.ACTIVE
        return prepared

    @staticmethod
    def _node(event):
        return Node(
            event.identifier,
            magnitud=event.magnitude,
            profundidad_h=event.depth_km,
            fecha_hora=event.occurred_at.isoformat(),
            revision=str(event.revision),
            procedencia=event.station,
            estado_atencion=event.attention == AttentionState.REVIEWED,
            zona_poblada=event.populated_zone,
        )

    def _snapshot(self):
        return {
            "active": {key: event.copy() for key, event in self._active.items()},
            "archived": {key: event.copy() for key, event in self._archived.items()},
            "deleted": {key: event.copy() for key, event in self._deleted.items()},
        }

    def _restore(self, snapshot):
        self._active = {key: event.copy() for key, event in snapshot["active"].items()}
        self._archived = {key: event.copy() for key, event in snapshot["archived"].items()}
        self._deleted = {key: event.copy() for key, event in snapshot["deleted"].items()}
        self._rebuild_tree()

    def _record(self, action):
        self._history.append((action, self._snapshot()))

    def _rebuild_tree(self):
        self.tree = AVL_tree()
        self._nodes_by_id = {}
        for identifier, event in self._active.items():
            node = self._node(event)
            self.tree.insert(node)
            self._nodes_by_id[identifier] = node
        self._sync_associations()

    def _sync_associations(self):
        self._association_policy.refresh(self._active.values())

    def create(self, event):
        prepared = self._prepare(event)
        identifier = prepared.identifier
        if identifier in self._active or identifier in self._archived or identifier in self._deleted:
            raise EventValidationError("el identificador ya existe en el catalogo.")
        self._record("create")
        prepared.accepted_stations.add(prepared.station)
        self._active[identifier] = prepared
        self._rebuild_tree()
        return self.get(identifier)

    def get(self, identifier):
        if identifier in self._active:
            return self._active[identifier].copy()
        if identifier in self._archived:
            return self._archived[identifier].copy()
        if identifier in self._deleted:
            return self._deleted[identifier].copy()
        raise EventNotFound(identifier)

    def update(self, identifier, event):
        current = self._active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        if event.identifier != identifier:
            raise EventValidationError("el identificador es inmutable.")
        prepared = self._prepare(event)
        self._record("update")
        prepared.revision = current.revision + 1
        prepared.attention = AttentionState.PENDING
        prepared.accepted_stations = set(current.accepted_stations)
        self._active[identifier] = prepared
        self._rebuild_tree()
        return self.get(identifier)

    def review(self, identifier):
        current = self._active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        self._record("review")
        current.attention = AttentionState.REVIEWED
        self._rebuild_tree()
        return self.get(identifier)

    def delete(self, identifier):
        current = self._active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        self._record("delete")
        self._active.pop(identifier)
        current.state = EventState.DELETED
        self._deleted[identifier] = current
        self._rebuild_tree()
        return current.copy()

    def archive_branch(self, identifier):
        root = self._nodes_by_id.get(identifier)
        if root is None:
            raise EventNotFound(identifier)
        identifiers = []

        def collect(node):
            if node is None:
                return
            identifiers.append(node.getIdentifier())
            collect(node.getLeftChild())
            collect(node.getRightChild())

        collect(root)
        self._record("archive")
        for event_id in identifiers:
            event = self._active.pop(event_id)
            event.state = EventState.ARCHIVED
            self._archived[event_id] = event
        self._rebuild_tree()
        return [self.get(event_id) for event_id in identifiers]

    def process_report(self, report):
        if report.identifier in self._deleted:
            return {"status": "rejected_deleted", "event": self.get(report.identifier)}
        current = self._active.get(report.identifier) or self._archived.get(report.identifier)
        if current is None:
            return {"status": "created", "event": self.create(report)}
        if report.revision < current.revision:
            return {"status": "stale", "event": self.get(report.identifier)}
        if report.revision == current.revision:
            if not current.same_report_data(report):
                return {"status": "conflict", "event": self.get(report.identifier)}
            self._record("confirm")
            current.accepted_stations.add(report.station)
            if current.state == EventState.ACTIVE:
                self._rebuild_tree()
            return {"status": "confirmed", "event": self.get(report.identifier)}
        self._record("report_update")
        updated = self._prepare(report)
        updated.accepted_stations = set(current.accepted_stations)
        updated.accepted_stations.add(report.station)
        updated.attention = AttentionState.PENDING
        if current.state == EventState.ARCHIVED:
            self._archived.pop(report.identifier)
        self._active[report.identifier] = updated
        self._rebuild_tree()
        return {"status": "updated", "event": self.get(report.identifier)}

    def undo(self):
        if not self._history:
            raise EventNotFound("no hay acciones para deshacer")
        _action, snapshot = self._history.pop()
        self._restore(snapshot)
        return self.metrics()

    def metrics(self):
        events = list(self._active.values())
        return {
            "active": len(events),
            "archived": len(self._archived),
            "deleted": len(self._deleted),
            "priority_3": sum(event.priority == 3 for event in events),
            "pending": sum(event.attention == AttentionState.PENDING for event in events),
        }

    def tree_data(self):
        def serialize(node):
            if node is None:
                return None
            event = self._active[node.getIdentifier()]
            children = [child for child in (
                serialize(node.getLeftChild()), serialize(node.getRightChild())
            ) if child is not None]
            return {
                "id": str(event.identifier),
                "value": event.identifier,
                "priority": event.priority,
                "height": node.getHeight(),
                "balance_factor": balance_factor(node),
                "children": children,
                "event": self.as_dict(event),
                "attributes": self.as_dict(event),
            }

        return serialize(self.tree.getRoot())

    @staticmethod
    def as_dict(event):
        return EventPresenter.as_dict(event)

    def response(self, identifier=None):
        event = self.get(identifier) if identifier is not None else None
        values = []

        def collect(node):
            if node is None:
                return
            collect(node.getLeftChild())
            values.append(node.getIdentifier())
            collect(node.getRightChild())

        collect(self.tree.getRoot())
        return {
            "event": self.as_dict(event) if event else None,
            "tree": self.tree_data(),
            "values": values,
            "metrics": self.metrics(),
        }