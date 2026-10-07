import { treeService } from "../../services/treeService.js";
import { setBusy } from "../../utils/dom.js";
import { store } from "../state/store.js";

export function initVersionManager({ onRequestRefresh } = {}) {
  const saveForm = document.querySelector("#save-version-form");
  const nameInput = document.querySelector("#version-name");
  const versionSelect = document.querySelector("#version-select");
  const restoreButton = document.querySelector("#restore-version");
  const exportButton = document.querySelector("#export-state");
  const importForm = document.querySelector("#import-state-form");
  const stateFile = document.querySelector("#state-file");
  const countLabel = document.querySelector("#versions-count");
  const message = document.querySelector("#versions-message");

  function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.toggle("error", isError);
  }

  async function refreshVersions(selectedName = "") {
    const versions = await treeService.listVersions();
    versionSelect.replaceChildren(new Option("Selecciona una versión", ""));
    versions.forEach((version) => {
      const option = new Option(
        `${version.name} · ${new Date(version.created_at).toLocaleString("es-CO")}`,
        version.name,
      );
      versionSelect.append(option);
    });
    countLabel.textContent = `${versions.length} versión${versions.length === 1 ? "" : "es"}`;
    versionSelect.value = selectedName;
    restoreButton.disabled = !versionSelect.value;
  }

  versionSelect.addEventListener("change", () => {
    restoreButton.disabled = !versionSelect.value;
  });

  saveForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!saveForm.reportValidity()) return;
    const name = nameInput.value.trim();
    setBusy(saveForm, true);
    try {
      await treeService.saveVersion(name);
      await refreshVersions(name);
      saveForm.reset();
      showMessage("Versión guardada en esta sesión. Exporta el estado completo para conservarla.");
      store.addActivity("Versión guardada", name);
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(saveForm, false);
    }
  });

  restoreButton.addEventListener("click", async () => {
    const name = versionSelect.value;
    if (!name) return;
    restoreButton.disabled = true;
    try {
      await treeService.restoreVersion(name);
      await onRequestRefresh?.();
      showMessage(`Versión «${name}» restaurada. Puedes deshacer esta restauración.`);
      store.addActivity("Versión restaurada", name);
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      restoreButton.disabled = !versionSelect.value;
    }
  });

  exportButton.addEventListener("click", async () => {
    exportButton.disabled = true;
    try {
      const state = await treeService.exportState();
      const file = new Blob([JSON.stringify(state, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = url;
      link.download = `sismolab-estado-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      showMessage("Estado completo exportado, incluidas las versiones guardadas.");
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      exportButton.disabled = false;
    }
  });

  importForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!importForm.reportValidity()) return;
    setBusy(importForm, true);
    try {
      const state = JSON.parse(await stateFile.files[0].text());
      await treeService.importState(state);
      await onRequestRefresh?.();
      await refreshVersions();
      importForm.reset();
      showMessage("Estado y versiones cargados. La carga se puede deshacer.");
      store.addActivity("Estado cargado", "Archivo operativo restaurado");
    } catch (error) {
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(importForm, false);
    }
  });

  refreshVersions().catch((error) =>
    showMessage(`[${error.status || 500}] ${error.message}`, true),
  );
  return { refreshVersions };
}
