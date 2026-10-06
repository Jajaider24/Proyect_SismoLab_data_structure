"""Fachada principal del catalogo de eventos sismicos."""

import math
from contextlib import contextmanager
from datetime import timedelta

from src.models.event import AttentionState, EventState
from src.models.simulation_clock import SimulationClock
from src.models.zone import Zone, ZoneClassifier
from src.services.eventCatalog.avl_index import EventAvlIndex
from src.services.eventCatalog.performance_queries import EventPerformanceQueries
from src.services.eventCatalog.exceptions import EventValidationError
from src.services.eventCatalog.history import EventHistory
from src.services.eventCatalog.replica import EventReplicaService
from src.services.eventCatalog.reports import EventReportService
from src.services.eventCatalog.response_builder import EventResponseBuilder
from src.services.eventCatalog.state_store import EventStateStore
from src.services.eventCatalog.validator import EventValidator
from src.core.AvlTree.rotation_tracker import RotationTracker
from src.services.event_policies import AssociationPolicy, PriorityPolicy
from src.services.eventCatalog.state_codec import decode_snapshot, encode_snapshot
from src.services.eventCatalog.metrics import EventMetrics


class EventCatalog:
    """Orquesta el catalogo delegando la logica en servicios especializados.

    La clase conserva la API publica que usan controladores y pruebas, pero su
    trabajo principal es coordinar validacion, estado, indice AVL, historial,
    reportes y presentacion.
    """

    def __init__(self, zone_classifier=None, clock=None, avl_service=None, repository=None):
        """Inicializa todos los servicios internos del catalogo."""
        self._store = EventStateStore()
        self._clock = clock or SimulationClock()
        self._validator = EventValidator(self._clock)
        self._zone_classifier = zone_classifier or ZoneClassifier()
        self._association_policy = AssociationPolicy()
        self._avl_index = EventAvlIndex(avl_service)
        self._performance_queries = EventPerformanceQueries(self._store, self._avl_index)
        self._metrics = EventMetrics()
        self._history = EventHistory()
        self._reports = EventReportService()
        self._replicas = EventReplicaService()
        self._responses = EventResponseBuilder()
        self._rotation_tracker = None
        self._indicators = {
            "accepted_corrections": 0,
            "discarded_reports": 0,
            "conflicts": 0,
            "bulk_archives": 0,
            "rotation_cases": {case: 0 for case in ("LL", "RR", "LR", "RL")},
            "simple_rotations": {direction: 0 for direction in ("left", "right")},
        }
        self._stress_mode = False
        self._recovering = False
        self._repository = repository
        self._versions = []
        self._history_suspended = 0
        self._persistence_suspended = 0
        self._parameters = {
            "archive_threshold_hours": 72.0,
            "zones": list(getattr(self._zone_classifier, "zones", ())),
        }
        if self._repository is not None:
            self._load_persisted_document(self._repository.load())

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
        """Copia el estado operativo completo y la topologia AVL exacta."""
        return {
            "store": self._store.snapshot(),
            "pending_reports": [report.copy() for report in self._reports.pending()],
            "clock": self._clock.snapshot(),
            "parameters": {
                "archive_threshold_hours": self._parameters["archive_threshold_hours"],
                "zones": list(self._parameters["zones"]),
            },
            "stress_mode": self._stress_mode,
            "topology": self._avl_index.snapshot_topology(),
            "metrics": self.metrics(),
            "indicators": self._copy_indicators(),
        }

    def _restore(self, snapshot):
        """Restaura los datos operativos sin compartir objetos mutables."""
        self._store.restore(snapshot["store"])
        self._reports.restore_pending(snapshot["pending_reports"])
        self._clock.restore(snapshot["clock"])
        self._parameters = {
            "archive_threshold_hours": snapshot["parameters"]["archive_threshold_hours"],
            "zones": list(snapshot["parameters"]["zones"]),
        }
        if hasattr(self._zone_classifier, "replace_zones"):
            self._zone_classifier.replace_zones(self._parameters["zones"])
        self._stress_mode = snapshot["stress_mode"]
        self._indicators = self._copy_indicators(snapshot.get("indicators"))
        self._avl_index.restore_topology(self._store.active, snapshot["topology"])

    def _copy_indicators(self, indicators=None):
        source = self._indicators if indicators is None else indicators
        rotation_cases = {case: 0 for case in ("LL", "RR", "LR", "RL")}
        rotation_cases.update(source.get("rotation_cases", {}))
        simple_rotations = {direction: 0 for direction in ("left", "right")}
        simple_rotations.update(source.get("simple_rotations", {}))
        return {
            "accepted_corrections": source.get("accepted_corrections", 0),
            "discarded_reports": source.get("discarded_reports", 0),
            "conflicts": source.get("conflicts", 0),
            "bulk_archives": source.get("bulk_archives", 0),
            "rotation_cases": rotation_cases,
            "simple_rotations": simple_rotations,
        }

    def _accumulate_rotations(self, tracker):
        for case in tracker.cases:
            self._indicators["rotation_cases"][case] += 1
        for direction in tracker.events:
            self._indicators["simple_rotations"][direction] += 1

    def _track_avl_mutation(self, operation):
        if self._rotation_tracker is not None:
            return operation(self._rotation_tracker)
        tracker = RotationTracker()
        with tracker:
            result = operation(tracker)
        self._accumulate_rotations(tracker)
        return result

    def _record(self, action):
        """Guarda una copia aislada antes de una accion de dominio."""
        if self._history_suspended:
            return None
        snapshot = self._snapshot()
        self._history.record(action, snapshot)
        return snapshot

    @contextmanager
    def _suspend_nested_commits(self):
        """Agrupa mutaciones internas de un paso de cola en una accion."""
        self._history_suspended += 1
        self._persistence_suspended += 1
        try:
            yield
        finally:
            self._history_suspended -= 1
            self._persistence_suspended -= 1

    @staticmethod
    def _encode_history(entries):
        return [
            {"action": action, "snapshot": encode_snapshot(snapshot)}
            for action, snapshot in entries
        ]

    @staticmethod
    def _decode_history(entries):
        return [
            (entry["action"], decode_snapshot(entry["snapshot"]))
            for entry in entries
        ]

    def _load_persisted_document(self, document):
        self._versions = document.get("versions", [])
        if document.get("state") is None:
            return
        self._restore(decode_snapshot(document["state"]))
        self._history.restore(self._decode_history(document.get("history", [])))

    def _persist(self):
        if self._repository is None or self._persistence_suspended:
            return
        self._repository.save({
            "schema_version": 1,
            "state": encode_snapshot(self._snapshot()),
            "history": self._encode_history(self._history.export()),
            "versions": self._versions,
        })

    def _rebuild_tree(self):
        """Reconstruye el indice AVL desde eventos activos."""
        tracker = RotationTracker()
        with tracker:
            self._avl_index.rebuild(self._store.active, rebalance=not self._stress_mode)
        self._accumulate_rotations(tracker)
        self._sync_associations()

    def _sync_associations(self):
        """Actualiza asociaciones calculadas para todos los eventos activos."""
        self._association_policy.refresh(self._store.active.values())

    def _insert_active(self, event, tracker=None):
        """Inserta en el AVL el nodo derivado de un evento activo."""
        self._track_avl_mutation(lambda active_tracker: self._avl_index.insert(
            event, tracker or self._rotation_tracker or active_tracker,
            rebalance=not self._stress_mode
        ))

    def _remove_active(self, identifier, tracker=None):
        """Elimina del AVL el nodo de un evento activo por identificador."""
        self._track_avl_mutation(lambda active_tracker: self._avl_index.remove(
            identifier, tracker or self._rotation_tracker or active_tracker,
            rebalance=not self._stress_mode
        ))

    def _update_active(self, event, reinsert, tracker=None):
        """Actualiza un evento en el índice conservando el nodo si su clave no cambia."""
        self._track_avl_mutation(lambda active_tracker: self._avl_index.update(
            event, reinsert=reinsert,
            tracker=tracker or self._rotation_tracker or active_tracker,
            rebalance=not self._stress_mode
        ))

    def set_stress_mode(self, enabled):
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        if not enabled and not self._avl_index.audit()["balanced"]:
            raise EventValidationError("recupere el AVL antes de volver a modo normal")
        enabled = bool(enabled)
        if enabled != self._stress_mode:
            self._record("set_mode")
            self._stress_mode = enabled
            self._persist()
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
        previous_state = self._record("recover")
        self._recovering = True
        try:
            audit_before = self._avl_index.audit()
            result = self._avl_index.recover()
            after = result["audit"]
            if (not after["valid_bst"] or not after["balanced"]
                    or not after["valid_heights"] or not after["valid_depths"]):
                raise EventValidationError("la auditoria no confirma un AVL valido")
            self._stress_mode = False
            tracker_result = RotationTracker()
            tracker_result.events = result.get("rotations", [])
            tracker_result.cases = result.get("cases", [])
            self._accumulate_rotations(tracker_result)
            self._persist()
            return {
                "mode": "normal",
                "before": audit_before,
                "after": after,
                "rotations": result["rotations"],
                "visited": result["visited"],
                "cost": result["visited"] + len(result["rotations"]),
            }
        except Exception:
            self._history.pop_snapshot()
            self._restore(previous_state)
            raise
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
        self._persist()
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
        # Magnitud, profundidad_h y zona poblada son los datos que determinan
        # la prioridad/clave; los demás cambios no alteran la posición AVL.
        reinsert = (
            prepared.magnitude != current.magnitude
            or prepared.depth_km != current.depth_km
            or prepared.populated_zone != current.populated_zone
        )
        self._record("update")
        self._indicators["accepted_corrections"] += 1
        prepared.revision = current.revision + 1
        prepared.attention = AttentionState.PENDING
        prepared.accepted_stations = set(current.accepted_stations)
        self._store.remove_active(identifier)
        self._store.add_active(prepared)
        self._update_active(prepared, reinsert=reinsert)
        self._sync_associations()
        self._persist()
        return self.get(identifier)

    def review(self, identifier):
        """Marca un evento activo como revisado por atencion humana."""
        current = self._store.active_event(identifier)
        self._record("review")
        current.attention = AttentionState.REVIEWED
        self._update_active(current, reinsert=False)
        self._persist()
        return self.get(identifier)

    def delete(self, identifier):
        """Mueve un evento activo a eliminados y lo retira del AVL."""
        self._store.active_event(identifier)
        self._record("delete")
        event = self._store.move_active_to_deleted(identifier)
        self._remove_active(identifier)
        self._sync_associations()
        self._persist()
        return event.copy()

    def archive_branch(self, identifier):
        """Archiva el subarbol AVL que nace en el identificador indicado."""
        identifiers = self._avl_index.branch_identifiers(identifier)
        self._record("archive")
        self._indicators["bulk_archives"] += 1
        for event_id in identifiers:
            self._store.move_active_to_archived(event_id)
            self._remove_active(event_id)
        self._sync_associations()
        self._persist()
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

    def preview_old_branch_archive(self, threshold_hours=None):
        """Previsualiza la rama que cumple los criterios de archivo antiguo."""
        if threshold_hours is None:
            threshold_hours = self._parameters["archive_threshold_hours"]
        threshold = self._validate_archive_threshold(threshold_hours)
        selection = self._avl_index.select_old_branch(
            self._store.active,
            self._clock.now(),
            threshold,
        )
        return {**selection, "threshold_hours": threshold}

    def archive_old_branch(self, threshold_hours=None, expected_identifiers=None):
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
        self._indicators["bulk_archives"] += 1
        for event_id in fixed_identifiers:
            self._store.move_active_to_archived(event_id)
            self._remove_active(event_id)
        self._sync_associations()
        self._persist()
        return {
            **preview,
            "archived": True,
            "archived_identifiers": fixed_identifiers,
        }

    def scenario(self):
        """Devuelve reloj, parametros, modo e indicadores vigentes."""
        return {
            "clock": self._clock.now().isoformat(),
            "clock_is_fixed": self._clock.snapshot() is not None,
            "parameters": {
                "archive_threshold_hours": self._parameters["archive_threshold_hours"],
                "zones": [
                    {
                        "name": zone.name,
                        "min_x": zone.min_x,
                        "max_x": zone.max_x,
                        "min_y": zone.min_y,
                        "max_y": zone.max_y,
                        "populated": zone.populated,
                    }
                    for zone in self._parameters["zones"]
                ],
            },
            "mode": "stress" if self._stress_mode else "normal",
            "metrics": self.metrics(),
            "pending_reports": self.pending_reports_count(),
            "undo_actions": self.history_count(),
        }

    def update_parameters(self, archive_threshold_hours=None, zones=None):
        """Cambia parametros del escenario como una unica accion reversible."""
        threshold = self._parameters["archive_threshold_hours"]
        if archive_threshold_hours is not None:
            threshold = self._validate_archive_threshold(archive_threshold_hours)
        next_zones = self._parameters["zones"] if zones is None else list(zones)
        if any(not isinstance(zone, Zone) for zone in next_zones):
            raise EventValidationError("cada zona debe cumplir el contrato de escenario.")
        if threshold == self._parameters["archive_threshold_hours"] and next_zones == self._parameters["zones"]:
            return self.scenario()["parameters"]

        self._record("update_parameters")
        self._parameters = {"archive_threshold_hours": threshold, "zones": next_zones}
        if hasattr(self._zone_classifier, "replace_zones"):
            self._zone_classifier.replace_zones(next_zones)
        for event in self._store.active.values():
            event.populated_zone = self._zone_classifier.is_populated(event.x, event.y)
            event.priority = PriorityPolicy.calculate(
                event.magnitude, event.depth_km, event.populated_zone
            )
        self._rebuild_tree()
        self._persist()
        return self.scenario()["parameters"]

    def advance_clock(self, seconds):
        """Avanza el reloj UTC y registra el avance como una accion separada."""
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise EventValidationError("seconds debe ser un numero finito no negativo.")
        if not math.isfinite(seconds) or seconds < 0:
            raise EventValidationError("seconds debe ser un numero finito no negativo.")
        if seconds == 0:
            return self.scenario()["clock"]
        before = self._record("advance_clock")
        try:
            self._clock.advance(timedelta(seconds=seconds))
        except (OverflowError, ValueError) as error:
            self._history.pop_snapshot()
            self._restore(before)
            raise EventValidationError(str(error)) from error
        self._persist()
        return self.scenario()["clock"]

    def export_state(self):
        """Exporta el estado operativo sin pila de retroceso ni otras versiones."""
        return {"schema_version": 1, **encode_snapshot(self._snapshot())}

    def load_state(self, data):
        """Carga un estado exportado como una sola accion deshacible."""
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise EventValidationError("el archivo no tiene un formato SismoLab compatible.")
        try:
            snapshot = decode_snapshot(data)
            before = self._record("load_state")
            self._restore(snapshot)
            audit = self._avl_index.audit()
            valid = audit["valid_bst"] and audit["valid_heights"] and audit["valid_depths"]
            if self._stress_mode is False:
                valid = valid and audit["balanced"]
            current_metrics = self.metrics()
            metrics_match = all(
                current_metrics.get(key) == value
                for key, value in snapshot["metrics"].items()
            )
            if not valid or not metrics_match:
                raise EventValidationError("el estado importado no conserva sus invariantes.")
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            if "before" in locals():
                self._history.pop_snapshot()
                self._restore(before)
            if isinstance(error, EventValidationError):
                raise
            raise EventValidationError("el archivo de estado esta incompleto o invalido.") from error
        self._persist()
        return self.response()

    def save_version(self, name):
        """Guarda una copia operativa nombrada y persistente."""
        name = name.strip() if isinstance(name, str) else ""
        if not name or len(name) > 60:
            raise EventValidationError("el nombre debe contener entre 1 y 60 caracteres.")
        if any(version["name"].casefold() == name.casefold() for version in self._versions):
            raise EventValidationError("ya existe una version con ese nombre.")
        self._versions.append({
            "name": name,
            "created_at": self._clock.now().isoformat(),
            "state": encode_snapshot(self._snapshot()),
        })
        self._persist()
        return self.list_versions()

    def list_versions(self):
        """Lista versiones nombradas sin exponer su estado operativo completo."""
        return [
            {
                "name": version["name"],
                "created_at": version["created_at"],
                "metrics": version["state"]["metrics"],
            }
            for version in self._versions
        ]

    def restore_version(self, name):
        """Restaura una version y conserva el estado previo en la pila undo."""
        version = next(
            (item for item in self._versions if item["name"] == name),
            None,
        )
        if version is None:
            raise EventValidationError("la version solicitada no existe.")
        before = self._record("restore_version")
        try:
            self._restore(decode_snapshot(version["state"]))
        except (KeyError, TypeError, ValueError) as error:
            self._history.pop_snapshot()
            self._restore(before)
            raise EventValidationError("la version guardada no es valida.") from error
        self._persist()
        return self.response()

    def delete_version(self, name):
        """Elimina una version nombrada sin alterar el estado operativo."""
        versions = [version for version in self._versions if version["name"] != name]
        if len(versions) == len(self._versions):
            raise EventValidationError("la version solicitada no existe.")
        self._versions = versions
        self._persist()
        return self.list_versions()

    def process_report(self, report):
        """Procesa un reporte individual segun reglas de revision."""
        tracker = RotationTracker()
        self._rotation_tracker = tracker
        try:
            with tracker:
                result = self._reports.process_report(report, self, tracker)
            self._accumulate_rotations(tracker)
        finally:
            self._rotation_tracker = None
        result["rotations"] = tracker.events
        result["rotation_cases"] = tracker.cases
        result["report"] = self.as_dict(report)
        result["mode"] = "stress" if self._stress_mode else "normal"
        result["deferred"] = self._stress_mode
        return result

    def enqueue_report(self, report):
        """Agrega un reporte a la cola pendiente de procesamiento."""
        self._validator.validate(report)
        self._record("enqueue_report")
        self._reports.enqueue(report)
        self._persist()

    def process_pending_reports(self):
        """Procesa todos los reportes pendientes en orden FIFO."""
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        results = []
        while self._reports.pending_count():
            results.append(self.process_next_report())
        return results

    def process_next_report(self):
        if self._recovering:
            raise EventValidationError("la recuperacion esta en curso")
        if not self._reports.pending_count():
            return None
        before = self._record("process_report_step")
        try:
            with self._suspend_nested_commits():
                result = self._reports.process_next(self)
                if result is not None:
                    if result["status"] == "updated":
                        self._indicators["accepted_corrections"] += 1
                    elif result["status"] == "conflict":
                        self._indicators["conflicts"] += 1
                    elif result["status"] in {"stale", "rejected_deleted"}:
                        self._indicators["discarded_reports"] += 1
        except Exception:
            self._history.pop_snapshot()
            self._restore(before)
            raise
        if result is None:
            return None
        self._persist()
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

    def query_pending_top(self, k):
        return self._performance_queries.pending_top(k)

    def query_magnitude_range(self, minimum, maximum):
        return self._performance_queries.magnitude_range(minimum, maximum)

    def query_shallow_depth(self, maximum_depth, start, end):
        return self._performance_queries.shallow_depth_range(maximum_depth, start, end)

    def query_associations(self, identifier):
        return self._performance_queries.associations(identifier)

    def query_costly_high_priority(self, depth_limit):
        return self._performance_queries.costly_high_priority(depth_limit)

    def verify_structure(self):
        """Audita el AVL y referencias de dominio y reporta cada evento afectado."""
        audit = self._avl_index.audit()
        reports = {
            item["identifier"]: dict(item, issues=list(item["issues"]))
            for item in audit.get("events", [])
        }
        all_events = {
            **self._store.active,
            **self._store.archived,
            **self._store.deleted,
        }
        locations = {}
        for state, events in (
            ("active", self._store.active),
            ("archived", self._store.archived),
            ("deleted", self._store.deleted),
        ):
            for identifier in events:
                locations.setdefault(identifier, []).append(state)
        for identifier, states in locations.items():
            if len(states) > 1:
                report = reports.setdefault(identifier, {"identifier": identifier, "issues": []})
                report["issues"].append("duplicate_catalog_identifier")
        known_identifiers = set(locations)
        for event in all_events.values():
            for reference in event.associations:
                if reference not in known_identifiers:
                    report = reports.setdefault(
                        event.identifier, {"identifier": event.identifier, "issues": []}
                    )
                    report["issues"].append(f"missing_reference:{reference}")
                if reference == event.identifier:
                    report = reports.setdefault(
                        event.identifier, {"identifier": event.identifier, "issues": []}
                    )
                    report["issues"].append("self_reference")

        mode = "stress" if self._stress_mode else "normal"
        expected_unbalance = []
        errors = []
        for report in reports.values():
            report["issues"] = sorted(set(report["issues"]))
            if "balance" in report["issues"] and mode == "stress":
                report["expected_imbalance"] = True
                expected_unbalance.append(report["identifier"])
            blocking_issues = [issue for issue in report["issues"] if issue != "balance"]
            if mode == "normal" and "balance" in report["issues"]:
                blocking_issues.append("balance")
            if blocking_issues:
                errors.append({**report, "issues": blocking_issues})

        valid = not errors and (mode == "stress" or audit["balanced"])
        return {
            "valid": valid,
            "mode": mode,
            "nodes_checked": audit["nodes"],
            "tree": audit,
            "event_reports": sorted(reports.values(), key=lambda item: item["identifier"]),
            "inconsistent_events": errors,
            "expected_unbalance_events": sorted(expected_unbalance),
            "references_valid": not any(
                issue.startswith("missing_reference:")
                or issue in {"self_reference", "duplicate_catalog_identifier"}
                for report in reports.values() for issue in report["issues"]
            ),
        }

    def compare_structures(self):
        return self._performance_queries.compare_structures(self._store.active.values())

    def undo(self):
        """Restaura la ultima accion registrada y devuelve metricas actuales."""
        self._restore(self._history.pop_snapshot())
        self._persist()
        return self.metrics()

    def history_count(self):
        """Devuelve cuantas acciones pueden deshacerse actualmente."""
        return self._history.count()

    def history_report(self, limit=20):
        """Explica los cambios de métricas de las acciones aún deshacibles."""
        entries = self._history.export()
        recent = entries[-limit:]
        start = len(entries) - len(recent)
        actions = []
        for offset, (name, before_snapshot) in enumerate(recent, start=start):
            after_metrics = (
                entries[offset + 1][1]["metrics"]
                if offset + 1 < len(entries)
                else self.metrics()
            )
            before_metrics = before_snapshot["metrics"]
            def flatten_metrics(metrics):
                values = {
                    key: metrics.get(key, 0)
                    for key in (
                        "active", "historical", "archived", "deleted", "height", "leaves",
                        "pending", "accepted_corrections", "discarded_reports", "conflicts",
                        "bulk_archives", "archived_events", "costly_access_events",
                    )
                }
                values.update({
                    f"priority_{priority}": count
                    for priority, count in metrics.get("priority_counts", {}).items()
                })
                values.update({
                    f"case_{case}": count
                    for case, count in metrics.get("rotation_cases", {}).items()
                })
                values.update({
                    f"rotation_{direction}": count
                    for direction, count in metrics.get("simple_rotations", {}).items()
                })
                return values

            before_values = flatten_metrics(before_metrics)
            after_values = flatten_metrics(after_metrics)
            actions.append({
                "action": name,
                "metrics_before": before_values,
                "metrics_after": after_values,
                "traversals_before": before_metrics.get("traversals", {}),
                "traversals_after": after_metrics.get("traversals", {}),
                "changes": {
                    key: after_values.get(key, 0) - before_values.get(key, 0)
                    for key in before_values.keys() | after_values.keys()
                    if isinstance(before_values.get(key, 0), (int, float))
                    and isinstance(after_values.get(key, 0), (int, float))
                },
            })
        return {"actions_available_to_undo": len(entries), "actions": actions}

    def pending_reports_count(self):
        """Devuelve cuantos reportes quedan en la cola de procesamiento."""
        return self._reports.pending_count()

    def metrics(self):
        """Delega el calculo puro de indicadores al servicio de métricas."""
        return self._metrics.calculate(
            self._store.active,
            self._store.archived,
            self._store.deleted,
            self._avl_index.tree.getRoot(),
            self._indicators,
        )

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
