import { store } from "../state/store.js";
import { renderTree } from "./treeRenderer.js";

export function initWorkspace() {
  function render(data) {
    if (!data) return;
    renderTree(data.tree, (nodeData) => {
      store.selectNode(nodeData);
    });
  }

  store.on("data", render);

  return { render };
}

