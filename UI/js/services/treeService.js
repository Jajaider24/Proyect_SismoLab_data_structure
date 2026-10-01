import { avlApi } from "../api/avlApi.js";

export const treeService = {
  load: async () => (await avlApi.getTree()).data,
  insert: async (value) => (await avlApi.insert(value)).data,
  update: async (identifier, node) => (await avlApi.update(identifier, node)).data,
  delete: async (identifier) => (await avlApi.delete(identifier)).data,
  clear: async () => (await avlApi.clear()).data,
};
