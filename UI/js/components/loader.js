const components = [
  ["header", "../../components/header/header.html"],
  ["metrics", "../../components/metrics/metrics.html"],
  ["event-form", "../../components/event-form/event-form.html"],
  ["report-console", "../../components/report-console/report-console.html"],
  ["analysis", "../../components/analysis/analysis.html"],
  ["workspace", "../../components/workspace/workspace.html"],
  ["activity", "../../components/activity/activity.html"],
  ["scenario", "../../components/scenario/scenario.html"],
  ["versions", "../../components/versions/versions.html"],
];

async function loadComponent([name, path]) {
  const response = await fetch(`${path}?v=4`);
  if (!response.ok) throw new Error(`No se pudo cargar el componente ${name}.`);
  const host = document.querySelector(`[data-component="${name}"]`);
  host.innerHTML = await response.text();
}

await Promise.all(components.map(loadComponent));
await import("../app.js?v=4");
