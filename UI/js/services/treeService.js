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
  getHistory: async () => avlApi.getHistory(),
  enqueueReport: async (report) => avlApi.enqueueReport(report),
  processReports: async () => avlApi.processReports(),
  processReportStep: async () => avlApi.processReportStep(),
  getMode: async () => avlApi.getMode(),
  verifyStructure: async () => avlApi.verifyStructure(),
  setMode: async (stress) => avlApi.setMode(stress),
  recover: async () => avlApi.recover(),
  queryAnalysis: async (path) => avlApi.queryAnalysis(path),
  compareStructures: async () => avlApi.compareStructures(),
  getScenario: async () => avlApi.getScenario(),
  updateScenarioParameters: async (parameters) =>
    avlApi.updateScenarioParameters(parameters),
  advanceClock: async (seconds) => avlApi.advanceClock(seconds),
  listVersions: async () => avlApi.listVersions(),
  saveVersion: async (name) => avlApi.saveVersion(name),
  restoreVersion: async (name) => avlApi.restoreVersion(name),
  deleteVersion: async (name) => avlApi.deleteVersion(name),
  exportState: async () => avlApi.exportState(),
  importState: async (state) => avlApi.importState(state),
};
