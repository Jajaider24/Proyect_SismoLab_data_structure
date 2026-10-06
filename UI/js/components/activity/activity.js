import { store } from "../state/store.js";
import { treeService } from "../../services/treeService.js";
import { flattenTree, findNode } from "../../utils/treeUtils.js";

export function initActivity({ onRequestRefresh } = {}) {
  const eventList = document.querySelector("#event-list");
  const listCount = document.querySelector("#list-count");
  const activityList = document.querySelector("#activity-list");
  const clearActivityButton = document.querySelector("#clear-activity");
  const undoButton = document.querySelector("#undo-button");
  const editMessage = document.querySelector("#edit-message");

  function renderActivity(activity = store.getState().activity) {
    if (!activityList) return;
    activityList.innerHTML = activity.length
      ? activity
          .map(
            (item) =>
              `<div class="activity-row"><i class="activity-marker ${item.isError ? "error" : ""}"></i><div class="activity-main"><strong>${item.label}</strong><span class="activity-meta">${item.detail} · ${item.at}</span></div></div>`,
          )
          .join("")
      : '<p class="muted">Todavía no hay acciones.</p>';
  }

  function renderEventList(data) {
    if (!eventList || !data) return;
    const attributes = flattenTree(data.tree).map((node) => node.attributes);

    if (listCount) {
      listCount.textContent = `${attributes.length} registro${attributes.length === 1 ? "" : "s"}`;
    }

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

  eventList?.addEventListener("click", (event) => {
    const row = event.target.closest("[data-identifier]");
    if (!row) return;
    const { currentData } = store.getState();
    const node = findNode(currentData.tree, Number(row.dataset.identifier));
    if (node) {
      store.selectNode(node);
    }
  });

  clearActivityButton?.addEventListener("click", () => {
    store.clearActivity();
  });

  undoButton?.addEventListener("click", async () => {
    try {
      await treeService.undo();
      if (onRequestRefresh) {
        await onRequestRefresh();
      }
      store.addActivity("Acción deshecha", "Catálogo restaurado");
      if (editMessage) editMessage.textContent = "Última acción deshecha.";
    } catch (error) {
      if (editMessage) {
        editMessage.textContent = `[${error.status || 500}] ${error.message}`;
      }
    }
  });

  store.on("data", renderEventList);
  store.on("activity", renderActivity);

  // Initial activity rendering
  renderActivity();

  return { renderActivity, renderEventList };
}

