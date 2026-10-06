import { store } from "../state/store.js";
import { flattenTree } from "../../utils/treeUtils.js";
import { treeService } from "../../services/treeService.js";

export function initMetrics() {
  const metricTotal = document.querySelector("#metric-total");
  const metricPriority = document.querySelector("#metric-priority");
  const metricPending = document.querySelector("#metric-pending");
  const metricHeight = document.querySelector("#metric-height");
  const metricHistorical = document.querySelector("#metric-historical");
  const metricLeaves = document.querySelector("#metric-leaves");
  const historyButton = document.querySelector("#show-metric-history");
  const historyList = document.querySelector("#metric-history");

  function setText(id, value) {
    const element = document.querySelector(id);
    if (element) element.textContent = value;
  }

  function renderDetails(metrics) {
    setText("#metric-priority-1", metrics.priority_counts?.["1"] ?? 0);
    setText("#metric-priority-2", metrics.priority_counts?.["2"] ?? 0);
    setText("#metric-priority-3", metrics.priority_counts?.["3"] ?? 0);
    setText("#metric-corrections", metrics.accepted_corrections ?? 0);
    setText("#metric-discarded", metrics.discarded_reports ?? 0);
    setText("#metric-conflicts", metrics.conflicts ?? 0);
    setText("#metric-bulk-archives", metrics.bulk_archives ?? 0);
    setText("#metric-archived", metrics.archived_events ?? metrics.archived ?? 0);
    setText("#metric-cases-ll-rr", `${metrics.rotation_cases?.LL ?? 0} / ${metrics.rotation_cases?.RR ?? 0}`);
    setText("#metric-cases-lr-rl", `${metrics.rotation_cases?.LR ?? 0} / ${metrics.rotation_cases?.RL ?? 0}`);
    setText("#metric-rotations", `${metrics.simple_rotations?.left ?? 0} / ${metrics.simple_rotations?.right ?? 0}`);
    setText("#metric-costly", metrics.costly_access_events ?? 0);
    for (const [name, values] of Object.entries(metrics.traversals || {})) {
      setText(`#traversal-${name.replaceAll("_", "-")}`, values.join(" → ") || "Árbol vacío");
    }
  }

  function renderMetrics(data) {
    if (!data) return;
    const attributes = flattenTree(data.tree).map((node) => node.attributes);

    if (metricTotal) {
      metricTotal.textContent = data.metrics?.active ?? attributes.length;
    }
    if (metricPriority) {
      metricPriority.textContent = data.metrics?.priority_3 ?? attributes.filter(
        (item) => item.priority === 3,
      ).length;
    }
    if (metricPending) {
      metricPending.textContent =
        data.metrics?.pending ??
        attributes.filter((item) => item.attention === "pending").length;
    }
    if (metricHeight) {
      metricHeight.textContent = data.metrics?.height ?? data.tree?.height ?? -1;
    }
    if (metricHistorical) metricHistorical.textContent = data.metrics?.historical ?? 0;
    if (metricLeaves) metricLeaves.textContent = data.metrics?.leaves ?? 0;
    renderDetails(data.metrics || {});
  }

  historyButton?.addEventListener("click", async () => {
    historyButton.disabled = true;
    historyList?.replaceChildren();
    try {
      const report = await treeService.getHistory();
      (report.explanations?.actions || []).slice().reverse().forEach((item) => {
        const row = document.createElement("li");
        const changes = Object.entries(item.changes || {})
          .filter(([, change]) => change !== 0)
          .map(([name, change]) => `${name}: ${change > 0 ? "+" : ""}${change}`);
        row.textContent = `${item.action}: ${changes.join(" · ") || "sin cambio en contadores"}`;
        historyList?.append(row);
      });
      if (!historyList?.children.length) {
        const row = document.createElement("li");
        row.textContent = "No hay acciones pendientes de deshacer.";
        historyList?.append(row);
      }
    } catch (error) {
      const row = document.createElement("li");
      row.textContent = `No se pudo cargar la trazabilidad: ${error.message}`;
      historyList?.append(row);
    } finally {
      historyButton.disabled = false;
    }
  });

  store.on("data", renderMetrics);

  return { renderMetrics };
}

