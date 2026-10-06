import { store } from "../state/store.js";

export function initHeader() {
  const dot = document.querySelector("#connection-dot");
  const status = document.querySelector("#tree-status");

  function updateStatus({ online, count }) {
    if (dot) {
      dot.classList.toggle("offline", !online);
    }
    if (status) {
      status.textContent = online
        ? `${count} eventos activos`
        : "Backend no disponible";
    }
  }

  store.on("connection", updateStatus);
  store.on("data", (data) => {
    updateStatus({
      online: true,
      count: data.values?.length || 0,
    });
  });

  return { updateStatus };
}

