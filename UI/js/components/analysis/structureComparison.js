import { buildComparisonTrees } from "./treeBuilder.js";
import { renderComparisonTree } from "./comparisonTreeRenderer.js";

const ORDER_LABELS = {
  catalog_order: "orden del catálogo",
  ascending: "orden ascendente por prioridad, magnitud e identificador",
  descending: "orden descendente por prioridad, magnitud e identificador",
};

function appendMetric(container, label, value) {
  const card = document.createElement("div");
  card.className = "comparison-metric";
  const caption = document.createElement("span");
  caption.textContent = label;
  const number = document.createElement("strong");
  number.textContent = value;
  card.append(caption, number);
  container.append(card);
}

export function initStructureComparison() {
  const panel = document.querySelector("#structure-comparison");
  const orderSelect = document.querySelector("#comparison-order");
  const orderDescription = document.querySelector("#comparison-order-description");
  const metrics = document.querySelector("#comparison-metrics");
  const avlTree = document.querySelector("#comparison-avl-tree");
  const bstTree = document.querySelector("#comparison-bst-tree");
  const avlSummary = document.querySelector("#avl-tree-summary");
  const bstSummary = document.querySelector("#bst-tree-summary");
  const searches = document.querySelector("#comparison-searches");
  const closeButton = document.querySelector("#close-comparison");
  let comparisonData = null;

  function renderOrder() {
    if (!comparisonData) return;
    const comparison = buildComparisonTrees(comparisonData, orderSelect.value);
    const { order, avl, bst } = comparison;

    orderDescription.textContent =
      `${ORDER_LABELS[order.order] || order.order}. ` +
      `${order.insertion_order.length} eventos insertados en cada estructura.`;
    metrics.replaceChildren();
    appendMetric(metrics, "Nodos", String(avl.metrics.nodes));
    appendMetric(metrics, "Altura AVL", String(avl.metrics.height));
    appendMetric(metrics, "Altura BST", String(bst.metrics.height));
    appendMetric(metrics, "Hojas AVL / BST", `${avl.metrics.leaves} / ${bst.metrics.leaves}`);

    avlSummary.textContent =
      `${avl.metrics.nodes} nodos · altura ${avl.metrics.height} · ${avl.metrics.leaves} hojas`;
    bstSummary.textContent =
      `${bst.metrics.nodes} nodos · altura ${bst.metrics.height} · ${bst.metrics.leaves} hojas`;
    renderComparisonTree(avlTree, avl.root, "avl");
    renderComparisonTree(bstTree, bst.root, "bst");
    renderSearches(order.searches || []);
  }

  function renderSearches(rows) {
    searches.replaceChildren();
    const heading = document.createElement("h4");
    heading.textContent = "Costo de búsqueda por evento";
    const description = document.createElement("p");
    description.textContent =
      "Cantidad de nodos examinados al buscar cada clave en ambos árboles.";
    const table = document.createElement("table");
    table.className = "comparison-search-table";
    table.innerHTML =
      "<thead><tr><th>Evento</th><th>Clave (P, M, ID)</th><th>AVL</th><th>BST</th></tr></thead>";
    const body = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      [
        `#${row.key[2]}`,
        `P${row.key[0]} · M ${row.key[1]} · #${row.key[2]}`,
        String(row.avl_nodes_examined),
        String(row.bst_comparisons),
      ].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        tr.append(cell);
      });
      body.append(tr);
    });
    table.append(body);
    if (!rows.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No hay eventos para comparar.";
      searches.append(heading, empty);
      return;
    }
    searches.append(heading, description, table);
  }

  orderSelect.addEventListener("change", renderOrder);
  closeButton.addEventListener("click", () => {
    panel.hidden = true;
    document.querySelector("#analysis-result").hidden = false;
    document.querySelector("#analysis-result").textContent =
      "Ejecuta una consulta para ver los resultados y nodos AVL examinados.";
  });

  function render(data) {
    comparisonData = data;
    orderSelect.value = "catalog_order";
    renderOrder();
    panel.hidden = false;
    document.querySelector("#analysis-result").hidden = true;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function hide() {
    panel.hidden = true;
    document.querySelector("#analysis-result").hidden = false;
  }

  return { render, hide };
}
