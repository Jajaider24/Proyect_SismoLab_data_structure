import { store } from "../state/store.js";
import { treeService } from "../../services/treeService.js";
import { setBusy, wait } from "../../utils/dom.js";

export function initReportConsole({ onRequestRefresh } = {}) {
  const reportForm = document.querySelector("#report-form");
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
  const stressStatus = document.querySelector("#stress-status");
  const stressAudit = document.querySelector("#stress-audit");

  let stressRunning = false;
  let stressMode = false;

  function showReportMessage(text, isError = false) {
    if (!reportMessage) return;
    reportMessage.textContent = text;
    reportMessage.classList.toggle("error", isError);
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
        !statusData.audit?.balanced,
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

  return {
    refreshStressStatus,
    paintStressStatus,
    showReportMessage,
    processOneReport,
  };
}

