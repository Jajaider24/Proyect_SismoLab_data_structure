const API_BASE_URL = "http://localhost:8000/avl";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || payload.message || "La solicitud fallo.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

export const avlApi = {
  getTree: () => request("/tree"),
  insert: (value) => request(`/insert/${encodeURIComponent(value)}`, { method: "POST" }),
  create: (node) => request("/nodes", { method: "POST", body: JSON.stringify(node) }),
  update: (identifier, node) => request(`/nodes/${encodeURIComponent(identifier)}`, {
    method: "PUT", body: JSON.stringify(node),
  }),
  delete: (identifier) => request(`/nodes/${encodeURIComponent(identifier)}`, { method: "DELETE" }),
  clear: () => request("/tree", { method: "DELETE" }),
};
