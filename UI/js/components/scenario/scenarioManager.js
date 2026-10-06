import { treeService } from "../../services/treeService.js";
import { setBusy } from "../../utils/dom.js";
import { store } from "../state/store.js";

export function initScenarioManager({ onRequestRefresh } = {}) {
  const parametersForm = document.querySelector("#scenario-parameters-form");
  const thresholdInput = document.querySelector("#scenario-archive-threshold");
  const clockForm = document.querySelector("#scenario-clock-form");
  const clockLabel = document.querySelector("#scenario-clock");
  const message = document.querySelector("#scenario-message");

  function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.toggle("error", isError);
  }

  function renderScenario(scenario) {
    thresholdInput.value = scenario.parameters.archive_threshold_hours;
    clockLabel.textContent = new Date(scenario.clock).toLocaleString("es-CO", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    }) + (scenario.clock_is_fixed ? " UTC · fijo" : " UTC · en vivo");
    const archiveThreshold = document.querySelector("#old-archive-threshold");
    if (archiveThreshold && !archiveThreshold.matches(":focus")) {
      archiveThreshold.value = scenario.parameters.archive_threshold_hours;
    }
  }

  async function refresh() {
    renderScenario(await treeService.getScenario());
  }

  parametersForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!parametersForm.reportValidity()) return;
    setBusy(parametersForm, true);
    try {
      await treeService.updateScenarioParameters({
        archive_threshold_hours: Number(thresholdInput.value),
      });
      if (onRequestRefresh) await onRequestRefresh();
      else await refresh();
      showMessage("Parámetros guardados. Esta acción se puede deshacer.");
      store.addActivity("Parámetros actualizados", "Umbral de archivo guardado");
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(parametersForm, false);
    }
  });

  clockForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!clockForm.reportValidity()) return;
    const seconds = Number(new FormData(clockForm).get("minutes")) * 60;
    setBusy(clockForm, true);
    try {
      await treeService.advanceClock(seconds);
      await refresh();
      showMessage("Reloj avanzado. Esta acción se puede deshacer.");
      store.addActivity("Reloj avanzado", `${seconds / 60} minuto(s)`);
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(clockForm, false);
    }
  });

  refresh().catch((error) => showMessage(`[${error.status || 500}] ${error.message}`, true));
  return { refresh };
}
