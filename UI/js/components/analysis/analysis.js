import { treeService } from "../../services/treeService.js";

export function initAnalysis() {
  const output = document.querySelector("#analysis-result");
  const forms = document.querySelectorAll("[data-analysis]");
  const toQuery = (values) => new URLSearchParams(values).toString();

  forms.forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form));

      try {
        let result;
        switch (form.dataset.analysis) {
          case "pending":
            result = await treeService.queryAnalysis(`pending?${toQuery(values)}`);
            break;
          case "magnitude":
            result = await treeService.queryAnalysis(`magnitude?${toQuery(values)}`);
            break;
          case "depth":
            values.start = `${values.start}:00Z`;
            values.end = `${values.end}:00Z`;
            result = await treeService.queryAnalysis(`depth?${toQuery(values)}`);
            break;
          case "associations":
            result = await treeService.queryAnalysis(
              `associations/${encodeURIComponent(values.identifier)}`,
            );
            break;
          case "costly":
            result = await treeService.queryAnalysis(
              `costly-high-priority?${toQuery({ depth_limit: values.depth_limit })}`,
            );
            break;
          case "compare":
            result = await treeService.compareStructures();
            break;
          default:
            return;
        }
        output.textContent = JSON.stringify(result, null, 2);
      } catch (error) {
        output.textContent = `[${error.status || 500}] ${error.message}`;
      }
    });
  });
}
