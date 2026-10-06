import { store } from "../state/store.js";
import { renderTree } from "./treeRenderer.js";
import { treeService } from "../../services/treeService.js";

export function initWorkspace() {
  const costForm = document.querySelector("#cost-to-reach-form");
  const costDepthInput = document.querySelector("#cost-to-reach-depth");
  const refreshButton = document.querySelector("#refresh-tree-button");
  const refreshMessage = document.querySelector("#tree-refresh-message");
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

  refreshButton.addEventListener("click", async () => {
    refreshButton.disabled = true;
    refreshMessage.textContent = "";
    try {
      const data = await treeService.load();
      store.setData(data);
      refreshMessage.textContent = "Árbol actualizado.";
    } catch (error) {
      console.error(`[${error.status || 500}] ${error.message}`);
      refreshMessage.textContent = `[${error.status || 500}] ${error.message}`;
    } finally {
      refreshButton.disabled = false;
    }
  });

  store.on("data", render);

  return { render };
}
