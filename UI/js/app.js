import { store } from "./components/state/store.js";
import { treeService } from "./services/treeService.js";
import { initHeader } from "./components/header/header.js";
import { initMetrics } from "./components/metrics/metrics.js";
import { initEventForm } from "./components/event-form/eventForm.js";
import { initWorkspace } from "./components/workspace/workspace.js";
import { initInspector } from "./components/workspace/inspector.js";
import { initReportConsole } from "./components/report-console/reportConsole.js";
import { initActivity } from "./components/activity/activity.js";

// Initialize UI components
initHeader();
const metrics = initMetrics();
const eventForm = initEventForm();
initWorkspace();
initInspector();

export async function refresh() {
  const data = await treeService.load();
  store.setData(data);
  await reportConsole.refreshStressStatus();
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
