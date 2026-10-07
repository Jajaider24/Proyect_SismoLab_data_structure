import { store } from "./components/state/store.js";
import { treeService } from "./services/treeService.js";
import { initHeader } from "./components/header/header.js";
import { initMetrics } from "./components/metrics/metrics.js";
import { initEventForm } from "./components/event-form/eventForm.js";
import { initWorkspace } from "./components/workspace/workspace.js";
import { initGeoMap } from "./components/workspace/geoMap.js";
import { initInspector } from "./components/workspace/inspector.js";
import { initReportConsole } from "./components/report-console/reportConsole.js";
import { initActivity } from "./components/activity/activity.js";
import { initAnalysis } from "./components/analysis/analysis.js?v=3";
import { initViewRouter } from "./components/navigation/viewRouter.js";
import { initScenarioManager } from "./components/scenario/scenarioManager.js";
import { initVersionManager } from "./components/versions/versionManager.js";

// Initialize UI components
initViewRouter();
initHeader();
const metrics = initMetrics();
const eventForm = initEventForm();
initWorkspace();
initGeoMap();
initInspector();
initAnalysis();
const scenarioManager = initScenarioManager({ onRequestRefresh: refresh });
initVersionManager({ onRequestRefresh: refresh });

export async function refresh() {
  const data = await treeService.load();
  store.setData(data);
  await reportConsole.refreshStressStatus();
  await scenarioManager.refresh().catch((error) => {
    console.warn(`No se pudo actualizar el escenario: ${error.message}`);
  });
}

const reportConsole = initReportConsole({ onRequestRefresh: refresh });
initActivity({ onRequestRefresh: refresh });

// Initial load
refresh().catch((error) => {
  console.error(`[${error.status || 500}] ${error.message}`);
  store.setConnection(false);
  metrics.renderMetrics(store.getState().currentData);
  store.addActivity("Error de conexión", "No fue posible cargar el AVL", true);
  eventForm.showMessage("No fue posible conectar con el backend.", true);
});
