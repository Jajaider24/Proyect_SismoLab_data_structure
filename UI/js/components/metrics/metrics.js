import { store } from "../state/store.js";
import { flattenTree } from "../../utils/treeUtils.js";

export function initMetrics() {
  const metricTotal = document.querySelector("#metric-total");
  const metricPriority = document.querySelector("#metric-priority");
  const metricPending = document.querySelector("#metric-pending");
  const metricHeight = document.querySelector("#metric-height");

  function renderMetrics(data) {
    if (!data) return;
    const attributes = flattenTree(data.tree).map((node) => node.attributes);

    if (metricTotal) {
      metricTotal.textContent = data.metrics?.active ?? attributes.length;
    }
    if (metricPriority) {
      metricPriority.textContent = attributes.filter(
        (item) => item.priority === 3,
      ).length;
    }
    if (metricPending) {
      metricPending.textContent =
        data.metrics?.pending ??
        attributes.filter((item) => item.attention === "pending").length;
    }
    if (metricHeight) {
      metricHeight.textContent = data.tree?.height || 0;
    }
  }

  store.on("data", renderMetrics);

  return { renderMetrics };
}

