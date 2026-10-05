import { renderTree } from "./components/treeRenderer.js";
import { treeService } from "./services/treeService.js";

const form = document.querySelector("#insert-form");
const input = document.querySelector("#value-input");
const createMagnitud = document.querySelector("#create-magnitud");
const createProfundidad = document.querySelector("#create-profundidad");
const createFecha = document.querySelector("#create-fecha");
const createRevision = document.querySelector("#create-revision");
const createProcedencia = document.querySelector("#create-procedencia");
const createZona = document.querySelector("#create-zona");
const createAtencion = document.querySelector("#create-atencion");
const createEstacion = document.querySelector("#create-estacion");
const createLatitud = document.querySelector("#create-latitud");
const createLongitud = document.querySelector("#create-longitud");
const clearButton = document.querySelector("#clear-button");
const message = document.querySelector("#message");
const status = document.querySelector("#tree-status");
const editForm = document.querySelector("#edit-form");
const selectionHint = document.querySelector("#selection-hint");
const editMessage = document.querySelector("#edit-message");
const deleteButton = document.querySelector("#delete-button");
const reviewButton = document.querySelector("#review-button");
const archiveButton = document.querySelector("#archive-button");
const undoButton = document.querySelector("#undo-button");
const lookupForm = document.querySelector("#lookup-form");
const lookupId = document.querySelector("#lookup-id");
const activityList = document.querySelector("#activity-list");
const eventList = document.querySelector("#event-list");
let selectedIdentifier = null;
let currentData = { values: [], tree: null };
let activity = JSON.parse(localStorage.getItem("sismolab-activity") || "[]");

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
}

function setConnection(online) {
  document
    .querySelector("#connection-dot")
    .classList.toggle("offline", !online);
  status.textContent = online
    ? `${currentData.values.length} eventos activos`
    : "Backend no disponible";
}

function setBusy(element, busy) {
  element?.querySelectorAll("button, input").forEach((control) => {
    control.disabled = busy;
  });
  element?.classList.toggle("is-busy", busy);
}

function addActivity(label, detail, isError = false) {
  activity.unshift({
    label,
    detail,
    isError,
    at: new Date().toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    }),
  });
  activity = activity.slice(0, 8);
  localStorage.setItem("sismolab-activity", JSON.stringify(activity));
  renderActivity();
}

function renderActivity() {
  activityList.innerHTML = activity.length
    ? activity
        .map(
          (item) =>
            `<div class="activity-row"><i class="activity-marker ${item.isError ? "error" : ""}"></i><div class="activity-main"><strong>${item.label}</strong><span class="activity-meta">${item.detail} · ${item.at}</span></div></div>`,
        )
        .join("")
    : '<p class="muted">Todavía no hay acciones.</p>';
}

function renderMetrics(data) {
  const attributes = flattenTree(data.tree).map((node) => node.attributes);
  document.querySelector("#metric-total").textContent =
    data.metrics?.active ?? attributes.length;
  document.querySelector("#metric-priority").textContent = attributes.filter(
    (item) => item.priority === 3,
  ).length;
  document.querySelector("#metric-pending").textContent =
    data.metrics?.pending ??
    attributes.filter((item) => item.attention === "pending").length;
  document.querySelector("#metric-height").textContent = data.tree?.height || 0;
  document.querySelector("#list-count").textContent =
    `${attributes.length} registro${attributes.length === 1 ? "" : "s"}`;
  eventList.replaceChildren();
  if (!attributes.length) {
    eventList.innerHTML = '<p class="muted">No hay eventos activos.</p>';
    return;
  }
  attributes.forEach((item) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "event-row";
    row.dataset.identifier = item.identificador;
    row.innerHTML = `<span class="event-main"><strong class="event-id"></strong><span class="event-meta"></span></span><span class="event-priority priority-${item.priority}">P${item.priority}</span>`;
    row.querySelector(".event-id").textContent = `#${item.identificador}`;
    row.querySelector(".event-meta").textContent =
      `M ${Number(item.magnitude).toFixed(1)} · ${item.station || "Sin estación"} · ${item.attention === "reviewed" ? "Revisado" : "Pendiente"}`;
    eventList.append(row);
  });
}

function flattenTree(tree, result = []) {
  if (!tree) return result;
  result.push(tree);
  tree.children?.forEach((child) => flattenTree(child, result));
  return result;
}

async function refresh() {
  const data = await treeService.load();
  currentData = data;
  renderTree(data.tree, selectNode);
  renderMetrics(data);
  setConnection(true);
}

function selectNode(nodeData) {
  selectedIdentifier = nodeData.attributes.identificador;
  const attributes = nodeData.attributes;
  selectionHint.hidden = true;
  editForm.hidden = false;
  document.querySelector("#edit-priority-badge").hidden = false;
  document.querySelector("#edit-priority-badge").textContent =
    `P${attributes.priority}`;
  document.querySelector("#selected-id-label").textContent =
    `#${attributes.identificador}`;
  document.querySelector("#edit-identificador").value =
    attributes.identificador;
  document.querySelector("#edit-prioridad").value = attributes.priority;
  document.querySelector("#edit-magnitud").value = attributes.magnitude;
  document.querySelector("#edit-profundidad").value = attributes.depth_km;
  document.querySelector("#edit-fecha").value =
    attributes.occurred_at?.slice(0, 16) || "";
  document.querySelector("#edit-revision").value = attributes.revision;
  document.querySelector("#edit-procedencia").value = attributes.station;
  document.querySelector("#edit-atencion").checked =
    attributes.attention === "pending";
  document.querySelector("#edit-zona").checked = attributes.populated_zone;
  document.querySelector("#edit-estacion").value = attributes.station || "";
  document.querySelector("#edit-latitud").value = attributes.latitude ?? "";
  document.querySelector("#edit-longitud").value = attributes.longitude ?? "";
  editMessage.textContent = `Nodo ${selectedIdentifier} seleccionado.`;
}

function findNode(tree, identifier) {
  if (!tree) return null;
  if (tree.attributes.identificador === identifier) return tree;
  for (const child of tree.children || []) {
    const found = findNode(child, identifier);
    if (found) return found;
  }
  return null;
}

function readEditForm() {
  return {
    identifier: Number(document.querySelector("#edit-identificador").value),
    magnitude: Number(document.querySelector("#edit-magnitud").value),
    depth_km: Number(document.querySelector("#edit-profundidad").value),
    latitude: Number(document.querySelector("#edit-latitud").value),
    longitude: Number(document.querySelector("#edit-longitud").value),
    occurred_at: document.querySelector("#edit-fecha").value,
    station: document.querySelector("#edit-estacion").value,
  };
}

function readCreateForm() {
  return {
    identifier: Number(input.value),
    magnitude: Number(createMagnitud.value),
    depth_km: Number(createProfundidad.value),
    latitude: Number(createLatitud.value),
    longitude: Number(createLongitud.value),
    occurred_at: createFecha.value,
    station: createEstacion.value || createProcedencia.value,
    revision: Number(createRevision.value || 1),
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = Number(input.value);
  if (!Number.isInteger(value))
    return showMessage("Ingresa un identificador entero valido.", true);
  setBusy(form, true);
  try {
    const data = await treeService.create(readCreateForm());
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    addActivity("Evento registrado", `#${value} añadido al AVL`);
    showMessage(`Evento #${value} registrado correctamente.`);
    input.value = "";
    createMagnitud.value = "";
    createProfundidad.value = "";
    createFecha.value = "";
    createRevision.value = "1";
    createProcedencia.value = "";
    createZona.checked = false;
    createAtencion.checked = false;
    createEstacion.value = "";
    createLatitud.value = "";
    createLongitud.value = "";
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    showMessage(`[${error.status || 500}] ${error.message}`, true);
  } finally {
    setBusy(form, false);
  }
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (selectedIdentifier === null) return;
  setBusy(editForm, true);
  try {
    const data = await treeService.update(selectedIdentifier, readEditForm());
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    addActivity("Evento actualizado", `#${selectedIdentifier} corregido`);
    editMessage.textContent = "Cambios guardados.";
    selectedIdentifier = readEditForm().identifier;
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  } finally {
    setBusy(editForm, false);
  }
});

deleteButton.addEventListener("click", async () => {
  if (selectedIdentifier === null) return;
  if (!window.confirm(`¿Eliminar el evento #${selectedIdentifier}?`)) return;
  setBusy(editForm, true);
  try {
    const data = await treeService.delete(selectedIdentifier);
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    addActivity("Evento eliminado", `#${selectedIdentifier} retirado del AVL`);
    editForm.hidden = true;
    document.querySelector("#edit-priority-badge").hidden = true;
    selectionHint.hidden = false;
    selectedIdentifier = null;
    editMessage.textContent = "Nodo eliminado.";
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  } finally {
    setBusy(editForm, false);
  }
});

clearButton.addEventListener("click", () => {
  form.reset();
  createRevision.value = "1";
  showMessage("Formulario limpio.");
});

reviewButton.addEventListener("click", async () => {
  if (selectedIdentifier === null) return;
  setBusy(editForm, true);
  try {
    const data = await treeService.review(selectedIdentifier);
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    addActivity(
      "Evento revisado",
      `#${selectedIdentifier} marcado como revisado`,
    );
    editMessage.textContent = "Evento marcado como revisado.";
  } catch (error) {
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  } finally {
    setBusy(editForm, false);
  }
});

archiveButton.addEventListener("click", async () => {
  if (selectedIdentifier === null) return;
  if (!window.confirm(`¿Archivar la rama desde #${selectedIdentifier}?`))
    return;
  setBusy(editForm, true);
  try {
    const data = await treeService.archive(selectedIdentifier);
    currentData = data;
    renderTree(data.tree, selectNode);
    renderMetrics(data);
    setConnection(true);
    addActivity("Rama archivada", `Desde #${selectedIdentifier}`);
    editForm.hidden = true;
    selectionHint.hidden = false;
    selectedIdentifier = null;
  } catch (error) {
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  } finally {
    setBusy(editForm, false);
  }
});

eventList.addEventListener("click", (event) => {
  const row = event.target.closest("[data-identifier]");
  if (!row) return;
  const node = findNode(currentData.tree, Number(row.dataset.identifier));
  if (node) selectNode(node);
});

lookupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const identifier = Number(lookupId.value);
  try {
    const data = await treeService.get(identifier);
    const node = findNode(data.tree, identifier);
    if (node) selectNode(node);
    else
      editMessage.textContent = `Evento #${identifier} está ${data.event.state}.`;
  } catch (error) {
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  }
});

undoButton.addEventListener("click", async () => {
  try {
    const data = await treeService.undo();
    await refresh();
    addActivity("Acción deshecha", "Catálogo restaurado");
    editMessage.textContent = "Última acción deshecha.";
  } catch (error) {
    editMessage.textContent = `[${error.status || 500}] ${error.message}`;
  }
});

document.querySelector("#clear-activity").addEventListener("click", () => {
  activity = [];
  localStorage.removeItem("sismolab-activity");
  renderActivity();
});

renderActivity();

refresh().catch((error) => {
  console.error(`[${error.status || 500}] ${error.message}`);
  status.textContent = "Backend no disponible";
  document.querySelector("#connection-dot").classList.add("offline");
  renderMetrics(currentData);
  addActivity("Error de conexión", "No fue posible cargar el AVL", true);
  showMessage("No fue posible conectar con el backend.", true);
});
