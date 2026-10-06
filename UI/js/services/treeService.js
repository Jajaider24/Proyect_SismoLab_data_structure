import { avlApi } from "../api/avlApi.js";

export const treeService = {
  load: async () => avlApi.getTree(),
  get: async (identifier) => avlApi.get(identifier),
  create: async (event) => avlApi.create(event),
  update: async (identifier, event) => avlApi.update(identifier, event),
  review: async (identifier) => avlApi.review(identifier),
  delete: async (identifier) => avlApi.delete(identifier),
  archive: async (identifier) => avlApi.archive(identifier),
  previewOldArchive: async (thresholdHours) =>
    avlApi.previewOldArchive(thresholdHours),
  archiveOld: async (thresholdHours, expectedIdentifiers) =>
    avlApi.archiveOld(thresholdHours, expectedIdentifiers),
  replicas: async (identifier, params) => avlApi.replicas(identifier, params),
  undo: async () => avlApi.undo(),
  enqueueReport: async (report) => avlApi.enqueueReport(report),
  processReports: async () => avlApi.processReports(),
  processReportStep: async () => avlApi.processReportStep(),
  getMode: async () => avlApi.getMode(),
  setMode: async (stress) => avlApi.setMode(stress),
  recover: async () => avlApi.recover(),
  queryAnalysis: async (path) => avlApi.queryAnalysis(path),
  compareStructures: async () => avlApi.compareStructures(),
};
