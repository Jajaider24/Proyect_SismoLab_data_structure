const API_BASE_URL = "http://localhost:8000/events";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(
      payload.detail || payload.message || "La solicitud fallo.",
    );
    error.status = response.status;
    throw error;
  }
  return payload;
}

export const avlApi = {
  getTree: () => request("/tree"),
  get: (identifier) => request(`/${encodeURIComponent(identifier)}`),
  insert: (event) =>
    request("", { method: "POST", body: JSON.stringify(event) }),
  create: (event) =>
    request("", { method: "POST", body: JSON.stringify(event) }),
  update: (identifier, event) =>
    request(`/${encodeURIComponent(identifier)}`, {
      method: "PUT",
      body: JSON.stringify(event),
    }),
  review: (identifier) =>
    request(`/${encodeURIComponent(identifier)}/review`, {
      method: "POST",
    }),
  delete: (identifier) =>
    request(`/${encodeURIComponent(identifier)}`, { method: "DELETE" }),
  archive: (identifier) =>
    request(`/${encodeURIComponent(identifier)}/archive`, {
      method: "POST",
    }),
  undo: () => request("/undo", { method: "POST" }),
  enqueueReport: (report) =>
    request("/reports", { method: "POST", body: JSON.stringify(report) }),
  processReports: () => request("/reports/process", { method: "POST" }),
};
