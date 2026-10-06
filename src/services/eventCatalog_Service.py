"""Fachada principal del catalogo de eventos sismicos."""

import math

from src.models.event import AttentionState, EventState
from src.models.simulation_clock import SimulationClock
from src.models.zone import ZoneClassifier
from src.services.eventCatalog.avl_index import EventAvlIndex
from src.services.eventCatalog.exceptions import EventValidationError
from src.services.eventCatalog.history import EventHistory
from src.services.eventCatalog.replica import EventReplicaService
from src.services.eventCatalog.reports import EventReportService
from src.services.eventCatalog.response_builder import EventResponseBuilder
from src.services.eventCatalog.state_store import EventStateStore
from src.services.eventCatalog.validator import EventValidator
from src.core.AvlTree.rotation_tracker import RotationTracker
from src.services.event_policies import AssociationPolicy, PriorityPolicy


class EventCatalog:
    """Orquesta el catalogo delegando la logica en servicios especializados.

    La clase conserva la API publica que usan controladores y pruebas, pero su
    trabajo principal es coordinar validacion, estado, indice AVL, historial,
    reportes y presentacion.
    """

    def __init__(self, zone_classifier=None, clock=None, avl_service=None):
        """Inicializa todos los servicios internos del catalogo."""
        self._store = EventStateStore()
        self._clock = clock or SimulationClock()
        self._validator = EventValidator(self._clock)
        self._zone_classifier = zone_classifier or ZoneClassifier()
        self._association_policy = AssociationPolicy()
        self._avl_index = EventAvlIndex(avl_service)
        self._history = EventHistory()
        self._reports = EventReportService()
        self._replicas = EventReplicaService()
        self._responses = EventResponseBuilder()
        self._rotation_tracker = None
        self._stress_mode = False
        self._recovering = False

    @property
    def tree(self):
        """Expone el arbol AVL interno para compatibilidad de bajo nivel."""
        return self._avl_index.tree

    def _prepare(self, event):
        """Copia, valida y completa datos derivados para guardar un evento."""
        self._validator.validate(event)
        prepared = event.copy()
        prepared.populated_zone = self._zone_classifier.is_populated(prepared.x, prepared.y)
        prepared.priority = PriorityPolicy.calculate(
            prepared.magnitude, prepared.depth_km, prepared.populated_zone
        )
        prepared.state = EventState.ACTIVE
        return prepared

    def _snapshot(self):
        """Toma una copia profunda del estado de eventos para poder deshacer."""
        return self._store.snapshot()

    def _restore(self, snapshot):
        """Restaura un snapshot y reconstruye estructuras derivadas."""
        self._store.restore(snapshot)
        self._rebuild_tree()

    def _record(self, action):
        """Guarda la accion y el estado previo en el historial."""
        self._history.record(action, self._snapshot())

    def _rebuild_tree(self):
        """Reconstruye el indice AVL desde eventos activos."""
        self._avl_index.rebuild(
            self._store.active,
            rebalance=not self._stress_mode,
        )
        self._sync_associations()

    def _sync_associations(self):
        """Actualiza asociaciones calculadas para todos los eventos activos."""
        self._association_policy.refresh(self._store.active.values())

    def _insert_active(self, event, tracker=None):
        """Inserta en el AVL el nodo derivado de un evento activo."""
        self._avl_index.insert(
            event,
            tracker or self._rotation_tracker,
            rebalance=not self._stress_mode,
        )

    def _remove_active(self, identifier, tracker=None):
        """Elimina del AVL el nodo de un evento activo por identificador."""
        self._avl_index.remove(
            identifier,
            tracker or self._rotation_tracker,
            rebalance=not self._stress_mode,
        )

    def set_stress_mode(self, enabled):
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        if not enabled and not self._avl_index.audit()["balanced"]:
            raise EventValidationError("recupere el AVL antes de volver a modo normal")
        self._stress_mode = bool(enabled)
        return self.status()

    def status(self):
        audit = self._avl_index.audit()
        return {
            "mode": "stress" if self._stress_mode else "normal",
            "recovering": self._recovering,
            "audit": audit,
        }

    def recover(self):
        if self._recovering:
            raise EventValidationError("la recuperacion ya esta en curso")
        self._recovering = True
        try:
            before = self._avl_index.audit()
            result = self._avl_index.recover()
            after = result["audit"]
            if (not after["valid_bst"] or not after["balanced"]
                    or not after["valid_heights"] or not after["valid_depths"]):
                raise EventValidationError("la auditoria no confirma un AVL valido")
            self._stress_mode = False
            return {
                "mode": "normal",
                "before": before,
                "after": after,
                "rotations": result["rotations"],
                "visited": result["visited"],
                "cost": result["visited"] + len(result["rotations"]),
            }
        finally:
            self._recovering = False

    def create(self, event, initial_revision=True):
        """Crea un evento activo, lo inserta en AVL y devuelve una copia."""
        prepared = self._prepare(event)
        if initial_revision:
            prepared.revision = 1
        self._store.ensure_identifier_available(prepared.identifier)
        self._record("create")
        prepared.accepted_stations.add(prepared.station)
        self._store.add_active(prepared)
        self._insert_active(prepared)
        self._sync_associations()
        return self.get(prepared.identifier)

    def get(self, identifier):
        """Obtiene una copia de un evento activo, archivado o eliminado."""
        return self._store.get(identifier)

    def update(self, identifier, event):
        """Actualiza un evento activo conservando su identificador original."""
        current = self._store.active_event(identifier)
        if event.identifier != identifier:
            raise EventValidationError("el identificador es inmutable.")
        prepared = self._prepare(event)
        self._record("update")
        prepared.revision = current.revision + 1
        prepared.attention = AttentionState.PENDING
        prepared.accepted_stations = set(current.accepted_stations)
        self._store.remove_active(identifier)
        self._remove_active(identifier)
        self._store.add_active(prepared)
        self._insert_active(prepared)
        self._sync_associations()
        return self.get(identifier)

    def review(self, identifier):
        """Marca un evento activo como revisado por atencion humana."""
        current = self._store.active_event(identifier)
        self._record("review")
        current.attention = AttentionState.REVIEWED
        self._rebuild_tree()
        return self.get(identifier)

    def delete(self, identifier):
        """Mueve un evento activo a eliminados y lo retira del AVL."""
        self._store.active_event(identifier)
        self._record("delete")
        event = self._store.move_active_to_deleted(identifier)
        self._remove_active(identifier)
        self._sync_associations()
        return event.copy()

    def archive_branch(self, identifier):
        """Archiva el subarbol AVL que nace en el identificador indicado."""
        identifiers = self._avl_index.branch_identifiers(identifier)
        self._record("archive")
        for event_id in identifiers:
            self._store.move_active_to_archived(event_id)
            self._remove_active(event_id)
        self._sync_associations()
        return [self.get(event_id) for event_id in identifiers]

    @staticmethod
    def _validate_archive_threshold(threshold_hours):
        """Exige un umbral numerico, finito y estrictamente positivo."""
        if (
            isinstance(threshold_hours, bool)
            or not isinstance(threshold_hours, (int, float))
        ):
            raise EventValidationError("threshold_hours debe ser un numero positivo y finito.")
        try:
            threshold = float(threshold_hours)
        except OverflowError as error:
            raise EventValidationError(
                "threshold_hours debe ser un numero positivo y finito."
            ) from error
        if not math.isfinite(threshold) or threshold <= 0:
            raise EventValidationError("threshold_hours debe ser un numero positivo y finito.")
        return threshold

    def preview_old_branch_archive(self, threshold_hours=72):
        """Previsualiza la rama que cumple los criterios de archivo antiguo."""
        threshold = self._validate_archive_threshold(threshold_hours)
        selection = self._avl_index.select_old_branch(
            self._store.active,
            self._clock.now(),
            threshold,
        )
        return {**selection, "threshold_hours": threshold}

    def archive_old_branch(self, threshold_hours=72, expected_identifiers=None):
        """Archiva la rama previsualizada como una unica accion deshacible.

        Los identificadores esperados evitan ejecutar una previsualizacion
        obsoleta. La lista se fija antes de mover eventos, pues cada borrado
        puede rotar el AVL y cambiar la topologia restante.
        """
        if expected_identifiers is None:
            raise EventValidationError("se requiere confirmar la lista previsualizada.")
        preview = self.preview_old_branch_archive(threshold_hours)
        if preview["identifiers"] != expected_identifiers:
            raise EventValidationError(
                "el arbol cambio desde la previsualizacion; vuelva a seleccionar la rama."
            )
        if not preview["eligible"]:
            return {**preview, "archived": False}

        fixed_identifiers = list(preview["identifiers"])
        self._record("archive_old_branch")
        for event_id in fixed_identifiers:
            self._store.move_active_to_archived(event_id)
            self._remove_active(event_id)
        self._sync_associations()
        return {
            **preview,
            "archived": True,
            "archived_identifiers": fixed_identifiers,
        }

    def process_report(self, report):
        """Procesa un reporte individual segun reglas de revision."""
        tracker = RotationTracker()
        self._rotation_tracker = tracker
        try:
            with tracker:
                result = self._reports.process_report(report, self, tracker)
        finally:
            self._rotation_tracker = None
        result["rotations"] = tracker.events
        result["report"] = self.as_dict(report)
        result["mode"] = "stress" if self._stress_mode else "normal"
        result["deferred"] = self._stress_mode
        return result

    def enqueue_report(self, report):
        """Agrega un reporte a la cola pendiente de procesamiento."""
        self._reports.enqueue(report)

    def process_pending_reports(self):
        """Procesa todos los reportes pendientes en orden FIFO."""
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        return self._reports.process_pending(self)

    def process_next_report(self):
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        result = self._reports.process_next(self)
        if result is None:
            return None
        return result

    def pending_reports(self):
        return [self.as_dict(report) for report in self._reports.pending()]

    def find_replicas(self, identifier, radius_km, window_hours):
        """Busca eventos activos/archivados cercanos a un evento base."""
        base_event = self.get(identifier)
        return {
            "base_event": self.as_dict(base_event),
            "radius_km": radius_km,
            "window_hours": window_hours,
            "replicas": self._replicas.find_replicas(
                base_event,
                radius_km,
                window_hours,
                self._store.active,
                self._store.archived,
            ),
        }

    def undo(self):
        """Restaura la ultima accion registrada y devuelve metricas actuales."""
        self._restore(self._history.pop_snapshot())
        return self.metrics()

    def history_count(self):
        """Devuelve cuantas acciones pueden deshacerse actualmente."""
        return self._history.count()

    def pending_reports_count(self):
        """Devuelve cuantos reportes quedan en la cola de procesamiento."""
        return self._reports.pending_count()

    def metrics(self):
        """Calcula conteos de estado, prioridad critica y atencion pendiente."""
        events = list(self._store.active.values())
        return {
            "active": len(events),
            "archived": len(self._store.archived),
            "deleted": len(self._store.deleted),
            "priority_3": sum(event.priority == 3 for event in events),
            "pending": sum(event.attention == AttentionState.PENDING for event in events),
        }

    def tree_data(self):
        """Serializa el AVL de eventos activos con datos de dominio completos."""
        return self._responses.tree_data(self._store, self._avl_index)

    @staticmethod
    def as_dict(event):
        """Convierte un evento de dominio en el contrato JSON de la API."""
        return EventResponseBuilder.as_dict(event)

    def response(self, identifier=None):
        """Construye la respuesta comun con evento opcional, arbol y metricas."""
        return self._responses.response(
            self._store,
            self._avl_index,
            self.metrics(),
            identifier,
        )
