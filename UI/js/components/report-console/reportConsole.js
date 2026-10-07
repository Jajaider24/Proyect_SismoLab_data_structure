import { store } from "../state/store.js";
import { treeService } from "../../services/treeService.js";
import { setBusy, wait } from "../../utils/dom.js";

export function initReportConsole({ onRequestRefresh } = {}) {
  const reportForm = document.querySelector("#report-form");
  const catalogImportForm = document.querySelector("#report-catalog-import-form");
  const catalogFileInput = document.querySelector("#report-catalog-file");
  const catalogImportMessage = document.querySelector("#report-catalog-message");
  const processReportsButton = document.querySelector("#process-reports");
  const reportMessage = document.querySelector("#report-message");
  const reportQueueCount = document.querySelector("#report-queue-count");
  const reportQueue = document.querySelector("#report-queue");
  const reportResults = document.querySelector("#report-results");
  const processOneReportButton = document.querySelector("#process-one-report");
  const stressStartButton = document.querySelector("#stress-start");
  const stressDelay = document.querySelector("#stress-delay");
  const stressModeButton = document.querySelector("#stress-mode");
  const recoverTreeButton = document.querySelector("#recover-tree");
  const verifyTreeButton = document.querySelector("#verify-tree");
  const auditSummary = document.querySelector("#structure-audit-summary");
  const auditEvents = document.querySelector("#structure-audit-events");
  const stressStatus = document.querySelector("#stress-status");
  const stressAudit = document.querySelector("#stress-audit");

  let stressRunning = false;
  let stressMode = false;

  function showReportMessage(text, isError = false) {
    if (!reportMessage) return;
    reportMessage.textContent = text;
    reportMessage.classList.toggle("error", isError);
  }

  function showCatalogImportMessage(text, isError = false) {
    if (!catalogImportMessage) return;
    catalogImportMessage.textContent = text;
    catalogImportMessage.classList.toggle("error", isError);
  }

  function readReportForm() {
    return {
      identifier: Number(document.querySelector("#report-id").value),
      magnitude: Number(document.querySelector("#report-magnitude").value),
      depth_km: Number(document.querySelector("#report-depth").value),
      x: Number(document.querySelector("#report-x").value),
      y: Number(document.querySelector("#report-y").value),
      occurred_at: document.querySelector("#report-time").value,
      station: document.querySelector("#report-station").value,
      revision: Number(document.querySelector("#report-revision").value),
    };
  }

  function renderReportQueue(queue) {
    if (reportQueueCount) {
      reportQueueCount.textContent = `${queue.length} en cola`;
    }
    if (!reportQueue) return;
    reportQueue.replaceChildren();
    queue.forEach((report, index) => {
      const row = document.createElement("div");
      row.className = "queue-row";
      row.innerHTML =
        '<span class="queue-order"></span><span class="report-detail"><strong></strong><span></span></span>';
      row.querySelector(".queue-order").textContent = `#${index + 1}`;
      row.querySelector("strong").textContent =
        `Estación ${report.station} · Evento ${report.identifier}`;
      row.querySelector(".report-detail span").textContent =
        `Revisión ${report.revision} · M ${report.magnitude}`;
      reportQueue.append(row);
    });
  }

  function renderReportResult(result) {
    if (!result || !reportResults) return;
    const report = result.report || {};
    const row = document.createElement("div");
    row.className = "report-result";
    const detail = document.createElement("span");
    detail.className = "report-detail";
    const title = document.createElement("strong");
    title.textContent = `Estación ${report.station} · Evento ${report.identifier}`;
    const metadata = document.createElement("span");
    metadata.textContent = `Revisión ${report.revision} · Rotaciones: ${(result.rotations || []).join(", ") || "ninguna"}`;
    detail.append(title, metadata);
    const decision = document.createElement("span");
    decision.className = "report-decision";
    decision.textContent = result.status;
    row.append(detail, decision);
    reportResults.prepend(row);
    while (reportResults.children.length > 12) {
      reportResults.lastElementChild.remove();
    }
  }

  function paintStressStatus(statusData) {
    if (!statusData) return;
    stressMode = statusData.mode === "stress";
    store.setStress(statusData);

    if (stressStatus) {
      stressStatus.textContent = stressMode ? "Modo estrés" : "Modo normal";
      stressStatus.parentElement?.classList.toggle("is-stress", stressMode);
      stressStatus.parentElement?.classList.toggle(
        "is-unbalanced",
        !stressMode && !statusData.audit?.balanced,
      );
    }
    if (stressModeButton) {
      stressModeButton.textContent = stressMode
        ? "Volver a normal"
        : "Activar estrés";
    }
    if (stressAudit) {
      stressAudit.textContent = statusData.audit?.balanced
        ? "AVL equilibrado"
        : stressMode
          ? "Desbalance esperado · verificar orden y metadatos"
          : "AVL desequilibrado · requiere recuperación";
    }
  }

  async function refreshStressStatus() {
    try {
      const data = await treeService.getMode();
      paintStressStatus(data);
    } catch {
      if (stressAudit) {
        stressAudit.textContent = "No se pudo auditar el AVL";
      }
    }
  }

  function applyReportResponse(response) {
    if (response.data) {
      store.setData(response.data);
    }
    renderReportQueue(response.queue || []);
    refreshStressStatus();
  }

  async function processOneReport() {
    const result = await treeService.processReportStep();
    applyReportResponse(result);
    if (result.result) {
      renderReportResult(result.result);
      store.addActivity(
        "Paso de estrés",
        `${result.result.status} · #${result.result.report.identifier}`,
      );
      return true;
    }
    return false;
  }

  reportForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    setBusy(reportForm, true);
    try {
      const result = await treeService.enqueueReport(readReportForm());
      renderReportQueue(result.queue || []);
      showReportMessage("Reporte encolado. Procésalo cuando termine la ráfaga.");
      store.addActivity(
        "Reporte recibido",
        `#${result.pending_reports} pendiente de procesamiento`,
      );
      reportForm.reset();
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(reportForm, false);
    }
  });

  catalogImportForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!catalogImportForm.reportValidity()) return;
    const file = catalogFileInput?.files?.[0];
    if (!file) {
      showCatalogImportMessage("Selecciona un archivo JSON.", true);
      return;
    }

    setBusy(catalogImportForm, true);
    try {
      let reports;
      try {
        reports = JSON.parse(await file.text());
      } catch {
        throw new Error("El archivo seleccionado no contiene JSON válido.");
      }
      if (!Array.isArray(reports)) {
        throw new Error("El JSON debe contener una lista de reportes.");
      }

      const result = await treeService.importReportCatalog(reports);
      renderReportQueue(result.queue || []);
      catalogImportForm.reset();
      showCatalogImportMessage(
        `${result.imported_reports} reporte(s) encolado(s) en orden de llegada.`,
      );
      store.addActivity(
        "Catálogo de reportes importado",
        `${result.imported_reports} reporte(s) añadidos a la cola`,
      );
    } catch (error) {
      const message = error.status
        ? `[${error.status}] ${error.message}`
        : error.message;
      showCatalogImportMessage(message, true);
    } finally {
      setBusy(catalogImportForm, false);
    }
  });

  processReportsButton?.addEventListener("click", async () => {
    processReportsButton.disabled = true;
    try {
      const result = await treeService.processReports();
      applyReportResponse(result);
      result.results?.forEach(renderReportResult);
      showReportMessage(`${result.results?.length || 0} reporte(s) procesado(s).`);
      store.addActivity(
        "Reportes procesados",
        `${result.results?.length || 0} resultado(s) aplicado(s)`,
      );
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      processReportsButton.disabled = false;
    }
  });

  processOneReportButton?.addEventListener("click", async () => {
    processOneReportButton.disabled = true;
    try {
      const processed = await processOneReport();
      showReportMessage(
        processed ? "Reporte procesado." : "La cola está vacía.",
      );
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      processOneReportButton.disabled = false;
    }
  });

  stressStartButton?.addEventListener("click", async () => {
    if (stressRunning) {
      stressRunning = false;
      store.setStressRunning(false);
      stressStartButton.textContent = "Iniciar continuo";
      return;
    }
    stressRunning = true;
    store.setStressRunning(true);
    stressStartButton.textContent = "Detener continuo";
    try {
      if (!stressMode) {
        paintStressStatus(await treeService.setMode(true));
      }
      while (stressRunning) {
        const processed = await processOneReport();
        if (!processed) break;
        await wait(Number(stressDelay?.value) || 800);
      }
      showReportMessage(
        stressRunning
          ? "La cola está vacía."
          : "Procesamiento continuo detenido.",
      );
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      stressRunning = false;
      store.setStressRunning(false);
      if (stressStartButton) {
        stressStartButton.textContent = "Iniciar continuo";
      }
    }
  });

  stressModeButton?.addEventListener("click", async () => {
    try {
      const next = await treeService.setMode(!stressMode);
      paintStressStatus(next);
      showReportMessage(
        next.mode === "stress"
          ? "Modo estrés activado."
          : "Modo normal activado.",
      );
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    }
  });

  recoverTreeButton?.addEventListener("click", async () => {
    stressRunning = false;
    store.setStressRunning(false);
    recoverTreeButton.disabled = true;
    try {
      const result = await treeService.recover();
      if (onRequestRefresh) {
        await onRequestRefresh();
      }
      showReportMessage(
        `AVL recuperado: ${result.rotations.length} rotación(es), costo ${result.cost}.`,
      );
      store.addActivity(
        "AVL recuperado",
        `${result.rotations.length} rotación(es) · costo ${result.cost}`,
      );
    } catch (error) {
      showReportMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      recoverTreeButton.disabled = false;
    }
  });

  verifyTreeButton?.addEventListener("click", async () => {
    verifyTreeButton.disabled = true;
    if (auditSummary) auditSummary.textContent = "Verificando estructura y referencias…";
    if (auditEvents) auditEvents.replaceChildren();
    try {
      const audit = await treeService.verifyStructure();
      const summary = audit.valid
        ? `Estructura válida en modo ${audit.mode}. ${audit.nodes_checked} nodos revisados.`
        : `Se encontraron ${audit.inconsistent_events.length} evento(s) inconsistente(s) en modo ${audit.mode}.`;
      if (auditSummary) {
        auditSummary.textContent = summary;
        auditSummary.classList.toggle("structure-audit-summary-error", !audit.valid);
        auditSummary.classList.toggle("structure-audit-summary-ok", audit.valid);
      }
      const rows = audit.inconsistent_events.map((item) => ({
        ...item,
        expected_imbalance: false,
      }));
      audit.expected_unbalance_events.forEach((identifier) => {
        const item = audit.event_reports.find((entry) => entry.identifier === identifier);
        if (item) rows.push({ ...item, expected_imbalance: true });
      });
      rows.forEach((item) => {
        const row = document.createElement("li");
        const issues = item.expected_imbalance
          ? `desbalance esperado en estrés (BF ${item.balance_factor})`
          : item.issues.join(", ");
        const details = [];
        if (item.issues.includes("height")) {
          details.push(`altura guardada ${item.stored_height}, recalculada ${item.expected_height}`);
        }
        if (item.issues.includes("depth")) {
          details.push(`profundidad guardada ${item.depth}, esperada ${item.expected_depth}`);
        }
        if (item.issues.includes("balance") && !item.expected_imbalance) {
          details.push(`factor de balance ${item.balance_factor}`);
        }
        row.textContent = `Evento #${item.identifier}: ${issues}${details.length ? ` · ${details.join(" · ")}` : ""}`;
        auditEvents?.append(row);
      });
      if (auditSummary && audit.valid && audit.expected_unbalance_events.length) {
        auditSummary.textContent += ` Desbalance esperado en ${audit.expected_unbalance_events.length} evento(s); orden y metadatos válidos.`;
      }
    } catch (error) {
      if (auditSummary) {
        auditSummary.textContent = `[${error.status || 500}] ${error.message}`;
        auditSummary.classList.add("structure-audit-summary-error");
      }
    } finally {
      verifyTreeButton.disabled = false;
    }
  });

  return {
    refreshStressStatus,
    paintStressStatus,
    showReportMessage,
    processOneReport,
  };
}
