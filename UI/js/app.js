import { treeService } from "./services/treeService.js";
import { renderTree } from "./components/treeRenderer.js";

const form = document.querySelector("#insert-form");
const input = document.querySelector("#value-input");
const clearButton = document.querySelector("#clear-button");
const message = document.querySelector("#message");
const status = document.querySelector("#tree-status");
const editForm = document.querySelector("#edit-form");
const selectionHint = document.querySelector("#selection-hint");
const editMessage = document.querySelector("#edit-message");
const deleteButton = document.querySelector("#delete-button");
let selectedIdentifier = null;

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
}

async function refresh() {
  const data = await treeService.load();
  renderTree(data.tree, selectNode);
  status.textContent = `${data.values.length} nodo${data.values.length === 1 ? "" : "s"}`;
}

function selectNode(nodeData) {
  selectedIdentifier = nodeData.attributes.identificador;
  const attributes = nodeData.attributes;
  selectionHint.hidden = true;
  editForm.hidden = false;
  document.querySelector("#edit-identificador").value = attributes.identificador;
  document.querySelector("#edit-magnitud").value = attributes.magnitud;
  document.querySelector("#edit-profundidad").value = attributes.profundidad_h;
  document.querySelector("#edit-fecha").value = attributes.fecha_hora;
  document.querySelector("#edit-revision").value = attributes.revision;
  document.querySelector("#edit-procedencia").value = attributes.procedencia;
  document.querySelector("#edit-atencion").checked = attributes.estado_atencion;
  editMessage.textContent = `Nodo ${selectedIdentifier} seleccionado.`;
}

function readEditForm() {
  return {
    identificador: Number(document.querySelector("#edit-identificador").value),
    magnitud: Number(document.querySelector("#edit-magnitud").value),
    profundidad_h: Number(document.querySelector("#edit-profundidad").value),
    fecha_hora: document.querySelector("#edit-fecha").value,
    revision: document.querySelector("#edit-revision").value,
    procedencia: document.querySelector("#edit-procedencia").value,
    estado_atencion: document.querySelector("#edit-atencion").checked,
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = Number(input.value);
  if (!Number.isInteger(value)) return showMessage("Ingresa un entero valido.", true);
  try {
    const data = await treeService.insert(value);
    renderTree(data.tree, selectNode);
    status.textContent = `${data.values.length} nodos`;
    showMessage(`Valor ${value} insertado correctamente.`);
    input.value = "";
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    showMessage(`[${error.status || 500}] ${error.message}`, true);
  }
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (selectedIdentifier === null) return;
  try {
    const data = await treeService.update(selectedIdentifier, readEditForm());
    renderTree(data.tree, selectNode);
    status.textContent = `${data.values.length} nodos`;
    editMessage.textContent = "Cambios guardados.";
    selectedIdentifier = readEditForm().identificador;
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  }
});

deleteButton.addEventListener("click", async () => {
  if (selectedIdentifier === null) return;
  try {
    const data = await treeService.delete(selectedIdentifier);
    renderTree(data.tree, selectNode);
    status.textContent = `${data.values.length} nodos`;
    editForm.hidden = true;
    selectionHint.hidden = false;
    selectedIdentifier = null;
    editMessage.textContent = "Nodo eliminado.";
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  }
});

clearButton.addEventListener("click", async () => {
  try {
    await treeService.clear();
    await refresh();
    showMessage("Arbol reiniciado.");
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    showMessage(`[${error.status || 500}] ${error.message}`, true);
  }
});

refresh().catch((error) => {
  console.error(`[${error.status || 500}] ${error.message}`);
  status.textContent = "Backend no disponible";
  showMessage("No fue posible conectar con el backend.", true);
});
