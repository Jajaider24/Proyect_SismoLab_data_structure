import { avlApi } from "../api/avlApi.js";

export const treeService = {
  load: async () => avlApi.getTree(),
  get: async (identifier) => avlApi.get(identifier),
  insert: async (event) => avlApi.insert(event),
  create: async (event) => avlApi.create(event),
  update: async (identifier, event) => avlApi.update(identifier, event),
  review: async (identifier) => avlApi.review(identifier),
  delete: async (identifier) => avlApi.delete(identifier),
  archive: async (identifier) => avlApi.archive(identifier),
  replicas: async (identifier, params) => avlApi.replicas(identifier, params),
  undo: async () => avlApi.undo(),
  enqueueReport: async (report) => avlApi.enqueueReport(report),
  processReports: async () => avlApi.processReports(),
};
