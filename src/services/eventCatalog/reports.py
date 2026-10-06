"""Cola y reglas de version para reportes de eventos."""

from src.core.structures.queue import Queue
from src.models.event import AttentionState, EventState


class EventReportService:
    """Administra reportes pendientes y aplica reglas de revision."""

    def __init__(self):
        """Inicializa la cola FIFO de reportes pendientes."""
        self._pending_reports = Queue()

    def enqueue(self, report):
        """Agrega un reporte a la cola pendiente de procesamiento."""
        self._pending_reports.enqueue(report)

    def pending_count(self):
        """Devuelve cuantos reportes quedan pendientes."""
        return len(self._pending_reports)

    def process_pending(self, catalog):
        """Procesa todos los reportes pendientes usando la fachada recibida."""
        results = []
        while self._pending_reports:
            results.append(self.process_next(catalog))
        return results

    def process_next(self, catalog):
        """Consume exactamente un reporte y devuelve su decision."""
        if not self._pending_reports:
            return None
        return catalog.process_report(self._pending_reports.dequeue())

    def pending(self):
        return self._pending_reports.items()

    def process_report(self, report, catalog, tracker=None):
        """Aplica reglas de version para crear, confirmar o actualizar reportes."""
        catalog._validator.validate(report)
        if report.identifier in catalog._store.deleted:
            return {"status": "rejected_deleted", "event": catalog.get(report.identifier)}
        current = catalog._store.current_report_target(report.identifier)
        if current is None:
            return {
                "status": "created",
                "event": catalog.create(report, initial_revision=False),
            }
        if report.revision < current.revision:
            return {"status": "stale", "event": catalog.get(report.identifier)}
        if report.revision == current.revision:
            if not current.same_report_data(report):
                return {"status": "conflict", "event": catalog.get(report.identifier)}
            catalog._record("confirm")
            current.accepted_stations.add(report.station)
            if current.state == EventState.ACTIVE:
                catalog._sync_associations()
            return {"status": "confirmed", "event": catalog.get(report.identifier)}
        catalog._record("report_update")
        updated = catalog._prepare(report)
        updated.accepted_stations = set(current.accepted_stations)
        updated.accepted_stations.add(report.station)
        updated.attention = AttentionState.PENDING
        if current.state != EventState.ARCHIVED:
            catalog._remove_active(report.identifier, tracker)
        catalog._store.reactivate(updated)
        catalog._insert_active(updated, tracker)
        catalog._sync_associations()
        return {"status": "updated", "event": catalog.get(report.identifier)}

