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
const activityList = document.querySelector("#activity-list");
const eventList = document.querySelector("#event-list");
const metadataKey = "sismolab-event-context";
let selectedIdentifier = null;
let currentData = { values: [], tree: null };
let activity = JSON.parse(localStorage.getItem("sismolab-activity") || "[]");
let localMetadata = JSON.parse(localStorage.getItem(metadataKey) || "{}");

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
  document.querySelector("#metric-total").textContent = attributes.length;
  document.querySelector("#metric-priority").textContent = attributes.filter(
    (item) => item.prioridad === 3,
  ).length;
  document.querySelector("#metric-pending").textContent = attributes.filter(
    (item) => item.revision !== "Revisado",
  ).length;
  document.querySelector("#metric-height").textContent = data.tree?.height || 0;
  document.querySelector("#list-count").textContent =
    `${attributes.length} registro${attributes.length === 1 ? "" : "s"}`;
  eventList.innerHTML = attributes.length
    ? attributes
        .map(
          (item) =>
            `<div class="event-row"><div class="event-main"><strong class="event-id">#${item.identificador}</strong><span class="event-meta">M ${item.magnitud.toFixed(1)} · ${item.procedencia || "Sin procedencia"} · ${item.revision || "Pendiente"}</span></div><span class="event-priority priority-${item.prioridad}">P${item.prioridad}</span></div>`,
        )
        .join("")
    : '<p class="muted">No hay eventos activos.</p>';
}

function flattenTree(tree, result = []) {
  if (!tree) return result;
  result.push(tree);
  tree.children?.forEach((child) => flattenTree(child, result));
  return result;
}

function saveMetadata(identifier, source) {
  localMetadata[identifier] = {
    estacion: source.estacion || "",
    latitud: source.latitud || "",
    longitud: source.longitud || "",
  };
  localStorage.setItem(metadataKey, JSON.stringify(localMetadata));
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
  const metadata = localMetadata[attributes.identificador] || {};
  selectionHint.hidden = true;
  editForm.hidden = false;
  document.querySelector("#edit-priority-badge").hidden = false;
  document.querySelector("#edit-priority-badge").textContent =
    `P${attributes.prioridad}`;
  document.querySelector("#selected-id-label").textContent =
    `#${attributes.identificador}`;
  document.querySelector("#edit-identificador").value =
    attributes.identificador;
  document.querySelector("#edit-prioridad").value = attributes.prioridad;
  document.querySelector("#edit-magnitud").value = attributes.magnitud;
  document.querySelector("#edit-profundidad").value = attributes.profundidad_h;
  document.querySelector("#edit-fecha").value =
    attributes.fecha_hora?.slice(0, 16) || "";
  document.querySelector("#edit-revision").value = attributes.revision;
  document.querySelector("#edit-procedencia").value = attributes.procedencia;
  document.querySelector("#edit-atencion").checked = attributes.estado_atencion;
  document.querySelector("#edit-zona").checked = attributes.zona_poblada;
  document.querySelector("#edit-estacion").value = metadata.estacion;
  document.querySelector("#edit-latitud").value = metadata.latitud;
  document.querySelector("#edit-longitud").value = metadata.longitud;
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
    zona_poblada: document.querySelector("#edit-zona").checked,
  };
}

function readCreateForm() {
  return {
    identificador: Number(input.value),
    magnitud: Number(createMagnitud.value),
    profundidad_h: Number(createProfundidad.value),
    fecha_hora: createFecha.value || null,
    revision: createRevision.value,
    procedencia: createProcedencia.value,
    estado_atencion: createAtencion.checked,
    zona_poblada: createZona.checked,
    estacion: createEstacion.value,
    latitud: createLatitud.value,
    longitud: createLongitud.value,
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = Number(input.value);
  if (!Number.isInteger(value))
    return showMessage("Ingresa un identificador entero valido.", true);
  try {
    const data = await treeService.create(readCreateForm());
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    saveMetadata(value, readCreateForm());
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
  }
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (selectedIdentifier === null) return;
  try {
    const data = await treeService.update(selectedIdentifier, readEditForm());
    renderTree(data.tree, selectNode);
    currentData = data;
    renderMetrics(data);
    saveMetadata(readEditForm().identificador, {
      estacion: document.querySelector("#edit-estacion").value,
      latitud: document.querySelector("#edit-latitud").value,
      longitud: document.querySelector("#edit-longitud").value,
    });
    setConnection(true);
    addActivity("Evento actualizado", `#${selectedIdentifier} corregido`);
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
    currentData = data;
    renderMetrics(data);
    setConnection(true);
    delete localMetadata[selectedIdentifier];
    localStorage.setItem(metadataKey, JSON.stringify(localMetadata));
    addActivity("Evento eliminado", `#${selectedIdentifier} retirado del AVL`);
    editForm.hidden = true;
    document.querySelector("#edit-priority-badge").hidden = true;
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
    localMetadata = {};
    localStorage.removeItem(metadataKey);
    addActivity("Índice reiniciado", "Todos los eventos fueron eliminados");
    showMessage("Arbol reiniciado.");
  } catch (error) {
    console.error(`[${error.status || 500}] ${error.message}`);
    showMessage(`[${error.status || 500}] ${error.message}`, true);
  }
});

reviewButton.addEventListener("click", async () => {
  if (selectedIdentifier === null) return;
  document.querySelector("#edit-revision").value = "Revisado";
  editForm.dispatchEvent(
    new Event("submit", { bubbles: true, cancelable: true }),
  );
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
