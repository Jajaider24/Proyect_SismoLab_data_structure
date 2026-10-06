import { store } from "../state/store.js";
import { treeService } from "../../services/treeService.js";
import { setBusy } from "../../utils/dom.js";
import { findNode } from "../../utils/treeUtils.js";

export function initInspector() {
  const editForm = document.querySelector("#edit-form");
  const selectionHint = document.querySelector("#selection-hint");
  const editMessage = document.querySelector("#edit-message");
  const editPriorityBadge = document.querySelector("#edit-priority-badge");
  const selectedIdLabel = document.querySelector("#selected-id-label");

  const editIdentificador = document.querySelector("#edit-identificador");
  const editPrioridad = document.querySelector("#edit-prioridad");
  const editMagnitud = document.querySelector("#edit-magnitud");
  const editProfundidad = document.querySelector("#edit-profundidad");
  const editFecha = document.querySelector("#edit-fecha");
  const editRevision = document.querySelector("#edit-revision");
  const editProcedencia = document.querySelector("#edit-procedencia");
  const editEstacion = document.querySelector("#edit-estacion");
  const editLatitud = document.querySelector("#edit-latitud");
  const editLongitud = document.querySelector("#edit-longitud");
  const editAtencion = document.querySelector("#edit-atencion");
  const editZona = document.querySelector("#edit-zona");

  const deleteButton = document.querySelector("#delete-button");
  const reviewButton = document.querySelector("#review-button");
  const archiveButton = document.querySelector("#archive-button");

  const lookupForm = document.querySelector("#lookup-form");
  const lookupId = document.querySelector("#lookup-id");

  const replicaForm = document.querySelector("#replica-form");
  const replicaResults = document.querySelector("#replica-results");
  const replicaR = document.querySelector("#replica-r");
  const replicaW = document.querySelector("#replica-w");

  function readEditForm() {
    return {
      identifier: Number(editIdentificador.value),
      magnitude: Number(editMagnitud.value),
      depth_km: Number(editProfundidad.value),
      x: Number(editLatitud.value),
      y: Number(editLongitud.value),
      occurred_at: editFecha.value,
      station: editEstacion.value,
    };
  }

  function readReplicaForm() {
    return {
      r: Number(replicaR.value),
      w: Number(replicaW.value),
    };
  }

  function renderReplicaResults(result) {
    const replicas = result.replicas || [];
    if (!replicas.length) {
      replicaResults.innerHTML =
        '<p class="muted">No hay eventos activos o archivados dentro de R y W.</p>';
      return;
    }
    replicaResults.innerHTML = replicas
      .map(
        (item) =>
          `<div class="replica-row"><div><strong>#${item.identifier} · ${item.state}</strong><span class="replica-meta">Δt ${Number(item.time_delta_hours).toFixed(2)} h · M ${Number(item.event.magnitude).toFixed(1)}</span></div><span class="replica-distance">${Number(item.distance_km).toFixed(2)} km</span></div>`,
      )
      .join("");
  }

  function handleNodeSelected(nodeData) {
    if (!nodeData?.attributes) return;
    const attributes = nodeData.attributes;

    if (selectionHint) selectionHint.hidden = true;
    if (editForm) editForm.hidden = false;

    if (editPriorityBadge) {
      editPriorityBadge.hidden = false;
      editPriorityBadge.textContent = `P${attributes.priority}`;
    }
    if (selectedIdLabel) {
      selectedIdLabel.textContent = `#${attributes.identificador}`;
    }

    if (editIdentificador) editIdentificador.value = attributes.identificador;
    if (editPrioridad) editPrioridad.value = attributes.priority;
    if (editMagnitud) editMagnitud.value = attributes.magnitude;
    if (editProfundidad) editProfundidad.value = attributes.depth_km;
    if (editFecha) editFecha.value = attributes.occurred_at?.slice(0, 16) || "";
    if (editRevision) editRevision.value = attributes.revision;
    if (editProcedencia) editProcedencia.value = attributes.station;
    if (editAtencion) editAtencion.checked = attributes.attention === "pending";
    if (editZona) editZona.checked = attributes.populated_zone;
    if (editEstacion) editEstacion.value = attributes.station || "";
    if (editLatitud) editLatitud.value = attributes.x ?? "";
    if (editLongitud) editLongitud.value = attributes.y ?? "";

    if (replicaForm) replicaForm.hidden = false;
    if (replicaResults) {
      replicaResults.innerHTML =
        '<p class="muted">Define R y W para comparar activos y archivados.</p>';
    }
    if (editMessage) {
      editMessage.textContent = `Nodo ${attributes.identificador} seleccionado.`;
    }
  }

  function handleNodeDeselected() {
    if (editForm) editForm.hidden = true;
    if (replicaForm) replicaForm.hidden = true;
    if (editPriorityBadge) editPriorityBadge.hidden = true;
    if (selectionHint) selectionHint.hidden = false;
  }

  store.on("nodeSelected", handleNodeSelected);
  store.on("nodeDeselected", handleNodeDeselected);

  editForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const { selectedIdentifier } = store.getState();
    if (selectedIdentifier === null) return;
    setBusy(editForm, true);
    try {
      const data = await treeService.update(selectedIdentifier, readEditForm());
      store.setData(data);
      store.addActivity("Evento actualizado", `#${selectedIdentifier} corregido`);
      if (editMessage) editMessage.textContent = "Cambios guardados.";
    } catch (error) {
      console.error(`[${error.status || 500}] ${error.message}`);
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    } finally {
      setBusy(editForm, false);
    }
  });

  deleteButton?.addEventListener("click", async () => {
    const { selectedIdentifier } = store.getState();
    if (selectedIdentifier === null) return;
    if (!window.confirm(`¿Eliminar el evento #${selectedIdentifier}?`)) return;
    setBusy(editForm, true);
    try {
      const data = await treeService.delete(selectedIdentifier);
      store.setData(data);
      store.clearSelection();
      store.addActivity("Evento eliminado", `#${selectedIdentifier} retirado del AVL`);
      if (editMessage) editMessage.textContent = "Nodo eliminado.";
    } catch (error) {
      console.error(`[${error.status || 500}] ${error.message}`);
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    } finally {
      setBusy(editForm, false);
    }
  });

  reviewButton?.addEventListener("click", async () => {
    const { selectedIdentifier } = store.getState();
    if (selectedIdentifier === null) return;
    setBusy(editForm, true);
    try {
      const data = await treeService.review(selectedIdentifier);
      store.setData(data);
      store.addActivity(
        "Evento revisado",
        `#${selectedIdentifier} marcado como revisado`,
      );
      if (editMessage) editMessage.textContent = "Evento marcado como revisado.";
    } catch (error) {
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    } finally {
      setBusy(editForm, false);
    }
  });

  archiveButton?.addEventListener("click", async () => {
    const { selectedIdentifier } = store.getState();
    if (selectedIdentifier === null) return;
    if (!window.confirm(`¿Archivar la rama desde #${selectedIdentifier}?`)) return;
    setBusy(editForm, true);
    try {
      const data = await treeService.archive(selectedIdentifier);
      store.setData(data);
      store.clearSelection();
      store.addActivity("Rama archivada", `Desde #${selectedIdentifier}`);
    } catch (error) {
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    } finally {
      setBusy(editForm, false);
    }
  });

  lookupForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const identifier = Number(lookupId.value);
    try {
      const data = await treeService.get(identifier);
      const node = findNode(data.tree, identifier);
      if (node) {
        store.selectNode(node);
      } else if (editMessage) {
        editMessage.textContent = `Evento #${identifier} está ${data.event.state}.`;
      }
    } catch (error) {
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    }
  });

  replicaForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const { selectedIdentifier } = store.getState();
    if (selectedIdentifier === null) return;
    setBusy(replicaForm, true);
    try {
      const result = await treeService.replicas(
        selectedIdentifier,
        readReplicaForm(),
      );
      renderReplicaResults(result);
      store.addActivity(
        "Replica consultada",
        `#${selectedIdentifier} con ${result.replicas.length} cercano(s)`,
      );
    } catch (error) {
      if (replicaResults) {
        replicaResults.innerHTML = `<p class="muted">[${error.status || 500}] ${error.message}</p>`;
      }
    } finally {
      setBusy(replicaForm, false);
    }
  });

  return { handleNodeSelected, handleNodeDeselected, readEditForm };
}

