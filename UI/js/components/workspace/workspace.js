import { store } from "../state/store.js";
import { renderTree } from "./treeRenderer.js";

export function initWorkspace() {
  const costForm = document.querySelector("#cost-to-reach-form");
  const costDepthInput = document.querySelector("#cost-to-reach-depth");
  let currentTree;
  let costDepth = null;

  function renderCurrentTree() {
    renderTree(currentTree, (nodeData) => {
      store.selectNode(nodeData);
    }, costDepth);
  }

  function render(data) {
    if (!data) return;
    currentTree = data.tree;
    renderCurrentTree();
  }

  costForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!costForm.reportValidity()) return;
    costDepth = costDepthInput.valueAsNumber;
    if (currentTree) renderCurrentTree();
  });

  store.on("data", render);

  return { render };
}
