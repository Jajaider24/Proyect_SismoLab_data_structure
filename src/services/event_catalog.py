"""Casos de uso y estado del catalogo de eventos."""

from src.core.node.node import Node
from src.core.structures.queue import Queue
from src.core.structures.stack import Stack
from src.models.event import AttentionState, EventState
from src.models.simulation_clock import SimulationClock
from src.models.zone import ZoneClassifier
from src.services.Avlservice import AVLTreeService
from src.services.event_policies import AssociationPolicy, PriorityPolicy
from src.services.event_presenter import EventPresenter


class EventValidationError(ValueError):
    """Error de datos de dominio detectado antes de mutar el catalogo."""


class EventNotFound(LookupError):
    """Error usado cuando un identificador no existe en el estado solicitado."""


class EventCatalog:
    """Orquesta eventos y reutiliza un servicio AVL propio para ordenarlos.

    El catalogo conserva el ciclo de vida de eventos en diccionarios de dominio
    y delega la estructura balanceada a ``AVLTreeService``. Esta instancia AVL
    es privada del catalogo y no comparte estado con la API manual ``/avl``.
    """

    def __init__(self, zone_classifier=None, clock=None, avl_service=None):
        """Inicializa dependencias, colecciones de estado e infraestructura."""
        self._avl = avl_service or AVLTreeService()
        self._active = {}
        self._archived = {}
        self._deleted = {}
        self._nodes_by_id = {}
        self._history = Stack()
        self._pending_reports = Queue()
        self._zone_classifier = zone_classifier or ZoneClassifier()
        self._clock = clock or SimulationClock()
        self._association_policy = AssociationPolicy()

    @property
    def tree(self):
        """Expone el arbol AVL interno para compatibilidad de bajo nivel."""
        return self._avl.tree

    def _validate(self, event):
        """Valida rangos, finitud, estacion, tiempo y revision del evento."""
        if not isinstance(event.identifier, int) or not 1 <= event.identifier <= 999999:
            raise EventValidationError("identificador debe ser un entero entre 1 y 999999.")
        if not isinstance(event.station, str) or not event.station.strip():
            raise EventValidationError("station es obligatorio.")
        if not -2.0 <= event.magnitude <= 10.0:
            raise EventValidationError("magnitud fuera de rango.")
        if not 0.0 <= event.depth_km <= 700.0:
            raise EventValidationError("profundidad fuera de rango.")
        if not 0.0 <= event.x <= 1000.0:
            raise EventValidationError("x debe estar entre 0 y 1000 km.")
        if not 0.0 <= event.y <= 1000.0:
            raise EventValidationError("y debe estar entre 0 y 1000 km.")
        for name, value in (
            ("magnitud", event.magnitude),
            ("profundidad", event.depth_km),
            ("x", event.x),
            ("y", event.y),
        ):
            text = str(value).lower()
            if "nan" in text or "inf" in text:
                raise EventValidationError(f"{name} debe ser finito.")
            if "." in text and len(text.split(".", 1)[1]) > 1:
                raise EventValidationError(f"{name} solo puede tener un decimal.")
        event.normalize_time()
        try:
            self._clock.validate_occurrence(event.occurred_at)
        except ValueError as error:
            raise EventValidationError(str(error)) from error
        if event.revision < 1:
            raise EventValidationError("revision debe ser positiva.")

    def _prepare(self, event):
        """Copia y completa datos derivados antes de guardar un evento activo."""
        self._validate(event)
        prepared = event.copy()
        prepared.populated_zone = self._zone_classifier.is_populated(prepared.x, prepared.y)
        prepared.priority = PriorityPolicy.calculate(
            prepared.magnitude, prepared.depth_km, prepared.populated_zone
        )
        prepared.state = EventState.ACTIVE
        return prepared

    @staticmethod
    def _node(event):
        """Convierte un evento activo en el ``Node`` que entiende el AVL."""
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
        """Toma una copia profunda del estado de eventos para poder deshacer."""
        return {
            "active": {key: event.copy() for key, event in self._active.items()},
            "archived": {key: event.copy() for key, event in self._archived.items()},
            "deleted": {key: event.copy() for key, event in self._deleted.items()},
        }

    def _restore(self, snapshot):
        """Restaura un snapshot y reconstruye el AVL desde eventos activos."""
        self._active = {key: event.copy() for key, event in snapshot["active"].items()}
        self._archived = {key: event.copy() for key, event in snapshot["archived"].items()}
        self._deleted = {key: event.copy() for key, event in snapshot["deleted"].items()}
        self._rebuild_tree()

    def _record(self, action):
        """Guarda la accion y el estado previo en la pila de historial."""
        self._history.push((action, self._snapshot()))

    def _rebuild_tree(self):
        """Reconstruye el AVL interno a partir de los eventos activos."""
        self._nodes_by_id = {}
        nodes = []
        for identifier, event in self._active.items():
            node = self._node(event)
            nodes.append(node)
            self._nodes_by_id[identifier] = node
        self._avl.rebuild(nodes)
        self._sync_associations()

    def _sync_associations(self):
        """Actualiza asociaciones calculadas para todos los eventos activos."""
        self._association_policy.refresh(self._active.values())

    def _insert_active(self, event):
        """Inserta en el AVL el nodo derivado de un evento activo."""
        node = self._node(event)
        if not self._avl.insert_node(node):
            raise EventValidationError("no se pudo insertar la clave del evento.")
        self._nodes_by_id[event.identifier] = node

    def _remove_active(self, identifier):
        """Elimina del AVL el nodo de un evento activo por identificador."""
        if not self._avl.delete_node(identifier):
            raise EventNotFound(identifier)
        self._nodes_by_id.pop(identifier, None)

    def create(self, event, initial_revision=True):
        """Crea un evento activo, lo inserta en AVL y devuelve una copia."""
        prepared = self._prepare(event)
        if initial_revision:
            prepared.revision = 1
        identifier = prepared.identifier
        if identifier in self._active or identifier in self._archived or identifier in self._deleted:
            raise EventValidationError("el identificador ya existe en el catalogo.")
        self._record("create")
        prepared.accepted_stations.add(prepared.station)
        self._active[identifier] = prepared
        self._insert_active(prepared)
        self._sync_associations()
        return self.get(identifier)

    def get(self, identifier):
        """Obtiene una copia de un evento activo, archivado o eliminado."""
        if identifier in self._active:
            return self._active[identifier].copy()
        if identifier in self._archived:
            return self._archived[identifier].copy()
        if identifier in self._deleted:
            return self._deleted[identifier].copy()
        raise EventNotFound(identifier)

    def update(self, identifier, event):
        """Actualiza un evento activo conservando su identificador original."""
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
        self._remove_active(identifier)
        self._active[identifier] = prepared
        self._insert_active(prepared)
        self._sync_associations()
        return self.get(identifier)

    def review(self, identifier):
        """Marca un evento activo como revisado por atencion humana."""
        current = self._active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        self._record("review")
        current.attention = AttentionState.REVIEWED
        self._rebuild_tree()
        return self.get(identifier)

    def delete(self, identifier):
        """Mueve un evento activo a eliminados y lo retira del AVL."""
        current = self._active.get(identifier)
        if current is None:
            raise EventNotFound(identifier)
        self._record("delete")
        self._active.pop(identifier)
        self._remove_active(identifier)
        current.state = EventState.DELETED
        self._deleted[identifier] = current
        self._sync_associations()
        return current.copy()

    def archive_branch(self, identifier):
        """Archiva el subarbol AVL que nace en el identificador indicado."""
        root = self._nodes_by_id.get(identifier)
        if root is None:
            raise EventNotFound(identifier)
        identifiers = []

        def collect(node):
            """Acumula identificadores de un subarbol por recorrido pre-order."""
            if node is None:
                return
            identifiers.append(node.getIdentifier())
            collect(node.getLeftChild())
            collect(node.getRightChild())

        collect(root)
        self._record("archive")
        for event_id in identifiers:
            event = self._active.pop(event_id)
            self._remove_active(event_id)
            event.state = EventState.ARCHIVED
            self._archived[event_id] = event
        self._sync_associations()
        return [self.get(event_id) for event_id in identifiers]

    def process_report(self, report):
        """Aplica reglas de version para crear, confirmar o actualizar reportes."""
        self._validate(report)
        if report.identifier in self._deleted:
            return {"status": "rejected_deleted", "event": self.get(report.identifier)}
        current = self._active.get(report.identifier) or self._archived.get(report.identifier)
        if current is None:
            return {
                "status": "created",
                "event": self.create(report, initial_revision=False),
            }
        if report.revision < current.revision:
            return {"status": "stale", "event": self.get(report.identifier)}
        if report.revision == current.revision:
            if not current.same_report_data(report):
                return {"status": "conflict", "event": self.get(report.identifier)}
            self._record("confirm")
            current.accepted_stations.add(report.station)
            if current.state == EventState.ACTIVE:
                self._sync_associations()
            return {"status": "confirmed", "event": self.get(report.identifier)}
        self._record("report_update")
        updated = self._prepare(report)
        updated.accepted_stations = set(current.accepted_stations)
        updated.accepted_stations.add(report.station)
        updated.attention = AttentionState.PENDING
        if current.state == EventState.ARCHIVED:
            self._archived.pop(report.identifier)
        else:
            self._remove_active(report.identifier)
        self._active[report.identifier] = updated
        self._insert_active(updated)
        self._sync_associations()
        return {"status": "updated", "event": self.get(report.identifier)}

    def enqueue_report(self, report):
        """Agrega un reporte a la cola pendiente de procesamiento."""
        self._pending_reports.enqueue(report)

    def process_pending_reports(self):
        """Procesa todos los reportes pendientes en orden FIFO."""
        results = []
        while self._pending_reports:
            results.append(self.process_report(self._pending_reports.dequeue()))
        return results

    def undo(self):
        """Restaura la ultima accion registrada y devuelve metricas actuales."""
        if not self._history:
            raise EventNotFound("no hay acciones para deshacer")
        _action, snapshot = self._history.pop()
        self._restore(snapshot)
        return self.metrics()

    def history_count(self):
        """Devuelve cuantas acciones pueden deshacerse actualmente."""
        return len(self._history)

    def pending_reports_count(self):
        """Devuelve cuantos reportes quedan en la cola de procesamiento."""
        return len(self._pending_reports)

    def metrics(self):
        """Calcula conteos de estado, prioridad critica y atencion pendiente."""
        events = list(self._active.values())
        return {
            "active": len(events),
            "archived": len(self._archived),
            "deleted": len(self._deleted),
            "priority_3": sum(event.priority == 3 for event in events),
            "pending": sum(event.attention == AttentionState.PENDING for event in events),
        }

    def tree_data(self):
        """Serializa el AVL de eventos activos con datos de dominio completos."""
        def event_dict_for(node):
            """Obtiene la representacion JSON del evento asociado a un nodo."""
            event = self._active[node.getIdentifier()]
            return self.as_dict(event)

        def event_extra_for(node):
            """Agrega el alias ``event`` esperado por la respuesta de eventos."""
            return {"event": event_dict_for(node)}

        return self._avl.serialize_tree(
            attributes_factory=event_dict_for,
            extra_factory=event_extra_for,
        )

    @staticmethod
    def as_dict(event):
        """Convierte un evento de dominio en el contrato JSON de la API."""
        return EventPresenter.as_dict(event)

    def response(self, identifier=None):
        """Construye la respuesta comun con evento opcional, arbol y metricas."""
        event = self.get(identifier) if identifier is not None else None
        return {
            "event": self.as_dict(event) if event else None,
            "tree": self.tree_data(),
            "values": self._avl.get_values(),
            "metrics": self.metrics(),
        }
