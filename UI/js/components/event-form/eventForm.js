import { store } from "../state/store.js";
import { treeService } from "../../services/treeService.js";
import { setBusy } from "../../utils/dom.js";

export function initEventForm() {
  const form = document.querySelector("#insert-form");
  const input = document.querySelector("#value-input");
  const createMagnitud = document.querySelector("#create-magnitud");
  const createProfundidad = document.querySelector("#create-profundidad");
  const createFecha = document.querySelector("#create-fecha");
  const createRevision = document.querySelector("#create-revision");
  const createProcedencia = document.querySelector("#create-procedencia");
  const createEstacion = document.querySelector("#create-estacion");
  const createLatitud = document.querySelector("#create-latitud");
  const createLongitud = document.querySelector("#create-longitud");
  const clearButton = document.querySelector("#clear-button");
  const message = document.querySelector("#message");
  const importForm = document.querySelector("#nodes-import-form");
  const importFile = document.querySelector("#nodes-json-file");
  const importMessage = document.querySelector("#nodes-import-message");

  function showMessage(text, isError = false) {
    if (!message) return;
    message.textContent = text;
    message.classList.toggle("error", isError);
  }

  function showImportMessage(text, isError = false) {
    if (!importMessage) return;
    importMessage.textContent = text;
    importMessage.classList.toggle("error", isError);
  }

  function readCreateForm() {
    return {
      identifier: Number(input.value),
      magnitude: Number(createMagnitud.value),
      depth_km: Number(createProfundidad.value),
      x: Number(createLatitud.value),
      y: Number(createLongitud.value),
      occurred_at: createFecha.value,
      station: createEstacion.value || createProcedencia.value,
      revision: Number(createRevision.value || 1),
    };
  }

  function resetFormFields() {
    input.value = "";
    createMagnitud.value = "";
    createProfundidad.value = "";
    createFecha.value = "";
    createRevision.value = "1";
    createProcedencia.value = "";
    createEstacion.value = "";
    createLatitud.value = "";
    createLongitud.value = "";
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const value = Number(input.value);
    if (!Number.isInteger(value)) {
      return showMessage("Ingresa un identificador entero valido.", true);
    }
    setBusy(form, true);
    try {
      const data = await treeService.create(readCreateForm());
      store.setData(data);
      store.addActivity("Evento registrado", `#${value} añadido al AVL`);
      showMessage(`Evento #${value} registrado correctamente.`);
      resetFormFields();
    } catch (error) {
      console.error(`[${error.status || 500}] ${error.message}`);
      showMessage(`[${error.status || 500}] ${error.message}`, true);
    } finally {
      setBusy(form, false);
    }
  });

  importForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = importFile?.files?.[0];
    if (!file) {
      return showImportMessage("Selecciona un archivo JSON.", true);
    }

    setBusy(importForm, true);
    try {
      const contents = await file.text();
      let nodes;
      try {
        nodes = JSON.parse(contents);
      } catch {
        throw new Error("El archivo seleccionado no contiene JSON válido.");
      }
      if (!Array.isArray(nodes)) {
        throw new Error("El JSON debe contener una lista de nodos.");
      }

      const data = await treeService.importNodes(nodes);
      store.setData(data);
      store.addActivity("Nodos importados", `${nodes.length} nodos añadidos al AVL`);
      showImportMessage(`${nodes.length} nodos importados correctamente.`);
      importForm.reset();
    } catch (error) {
      const message = error.status
        ? `[${error.status}] ${error.message}`
        : error.message;
      console.error(message);
      showImportMessage(message, true);
    } finally {
      setBusy(importForm, false);
    }
  });

  clearButton?.addEventListener("click", () => {
    form?.reset();
    if (createRevision) createRevision.value = "1";
    showMessage("Formulario limpio.");
  });

  return { showMessage, readCreateForm };
}
