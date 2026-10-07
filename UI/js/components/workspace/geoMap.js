import { store } from "../state/store.js";
import { localMapImageStorage } from "./localMapImageStorage.js";

const WIDTH = 680;
const HEIGHT = 580;
const MARGIN = { top: 30, right: 100, bottom: 70, left: 100 };
const PLOT_SIZE = Math.min(
  WIDTH - MARGIN.left - MARGIN.right,
  HEIGHT - MARGIN.top - MARGIN.bottom,
);
const PLOT = {
  left: (WIDTH - PLOT_SIZE) / 2,
  top: MARGIN.top,
  right: (WIDTH + PLOT_SIZE) / 2,
  bottom: MARGIN.top + PLOT_SIZE,
};
const DOMAIN = [0, 1000];

function collectEvents(tree, events = []) {
  if (!tree) return events;
  const event = tree.attributes;
  if (event && Number.isFinite(Number(event.x)) && Number.isFinite(Number(event.y))) {
    events.push(event);
  }
  (tree.children || []).forEach((child) => collectEvents(child, events));
  return events;
}

function eventSelection(event) {
  return { attributes: event };
}

export function initGeoMap() {
  const canvas = d3.select("#geo-map-canvas");
  const summary = document.querySelector("#geo-map-summary");
  const eventList = document.querySelector("#geo-map-event-list");
  const imageFile = document.querySelector("#geo-map-image-file");
  const imageOpacity = document.querySelector("#geo-map-image-opacity");
  const clearImageButton = document.querySelector("#geo-map-image-clear");
  const imageMessage = document.querySelector("#geo-map-image-message");
  let events = [];
  let imageUrl = null;
  let imageOpacityValue = Number(imageOpacity?.value || 0.68);
  let imageChangeVersion = 0;

  function setImage(blob) {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    imageUrl = blob ? URL.createObjectURL(blob) : null;
    if (clearImageButton) clearImageButton.disabled = !imageUrl;
  }

  function selectEvent(event) {
    store.selectNode(eventSelection(event));
    canvas.selectAll(".geo-event-point").classed(
      "is-selected",
      (item) => item.identificador === event.identificador,
    );
  }

  function render(data = store.getState().currentData) {
    const selectedId = store.getState().selectedIdentifier;
    events = collectEvents(data?.tree).filter(
      (event) => Number(event.x) >= 0 && Number(event.x) <= 1000
        && Number(event.y) >= 0 && Number(event.y) <= 1000,
    );

    canvas.selectAll("*").remove();
    canvas
      .attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const x = d3.scaleLinear().domain(DOMAIN).range([PLOT.left, PLOT.right]);
    const y = d3.scaleLinear().domain(DOMAIN).range([PLOT.bottom, PLOT.top]);
    const ticks = d3.range(0, 1001, 200);

    canvas.append("g")
      .attr("class", "geo-grid geo-grid-x")
      .attr("transform", `translate(0,${PLOT.bottom})`)
      .call(d3.axisBottom(x).tickValues(ticks).tickSize(-PLOT_SIZE).tickFormat(() => ""));
    canvas.append("g")
      .attr("class", "geo-grid geo-grid-y")
      .attr("transform", `translate(${PLOT.left},0)`)
      .call(d3.axisLeft(y).tickValues(ticks).tickSize(-PLOT_SIZE).tickFormat(() => ""));

    if (imageUrl) {
      canvas.insert("image", ".geo-grid")
        .attr("class", "geo-background-image")
        .attr("href", imageUrl)
        .attr("x", PLOT.left)
        .attr("y", PLOT.top)
        .attr("width", PLOT_SIZE)
        .attr("height", PLOT_SIZE)
        .attr("preserveAspectRatio", "xMidYMid slice")
        .attr("opacity", imageOpacityValue)
        .attr("pointer-events", "none");
    }

    canvas.append("g")
      .attr("class", "geo-axis")
      .attr("transform", `translate(0,${PLOT.bottom})`)
      .call(d3.axisBottom(x).tickValues(ticks).tickFormat((value) => `${value}`));
    canvas.append("g")
      .attr("class", "geo-axis")
      .attr("transform", `translate(${PLOT.left},0)`)
      .call(d3.axisLeft(y).tickValues(ticks).tickFormat((value) => `${value}`));

    canvas.append("text")
      .attr("class", "geo-axis-label")
      .attr("x", WIDTH / 2)
      .attr("y", HEIGHT - 18)
      .attr("text-anchor", "middle")
      .text("X · kilómetros");
    canvas.append("text")
      .attr("class", "geo-axis-label")
      .attr("transform", `translate(24,${(PLOT.top + PLOT.bottom) / 2}) rotate(-90)`)
      .attr("text-anchor", "middle")
      .text("Y · kilómetros");

    const points = canvas.append("g").attr("class", "geo-event-points")
      .selectAll("g")
      .data(events, (event) => event.identificador)
      .join("g")
      .attr("class", (event) => `geo-event-point priority-${event.priority || 1}${event.identificador === selectedId ? " is-selected" : ""}`)
      .attr("transform", (event) => `translate(${x(Number(event.x))},${y(Number(event.y))})`)
      .attr("tabindex", 0)
      .attr("role", "button")
      .attr("aria-label", (event) => `Evento ${event.identificador}, X ${event.x}, Y ${event.y} kilómetros, prioridad ${event.priority}`)
      .on("click", (_pointer, event) => selectEvent(event))
      .on("keydown", (keyboard, event) => {
        if (keyboard.key === "Enter" || keyboard.key === " ") {
          keyboard.preventDefault();
          selectEvent(event);
        }
      });

    points.append("title")
      .text((event) => `Evento #${event.identificador} · X ${event.x} km · Y ${event.y} km · Magnitud ${event.magnitude}`);
    points.append("circle").attr("class", "geo-point-halo").attr("r", 8);
    points.append("circle").attr("class", "geo-point-core").attr("r", 4);
    points.append("text")
      .attr("class", "geo-point-label")
      .attr("x", 10)
      .attr("y", -10)
      .text((event) => `#${event.identificador}`);

    if (summary) {
      summary.textContent = events.length
        ? `${events.length} evento(s) activo(s) en el plano. Selecciona un punto para abrir su ficha.`
        : "No hay eventos activos para representar en el plano.";
    }
    if (eventList) {
      eventList.replaceChildren();
      events.forEach((event) => {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = `geo-event-chip priority-${event.priority || 1}`;
        button.textContent = `#${event.identificador} · X ${event.x}, Y ${event.y} km`;
        button.setAttribute("aria-label", `Seleccionar evento ${event.identificador} en X ${event.x}, Y ${event.y} kilómetros`);
        button.addEventListener("click", () => selectEvent(event));
        item.append(button);
        eventList.append(item);
      });
    }
  }

  imageFile?.addEventListener("change", async () => {
    const file = imageFile.files?.[0];
    if (!file) return;
    imageChangeVersion += 1;
    if (!new Set(["image/png", "image/jpeg", "image/webp"]).has(file.type)) {
      imageMessage.textContent = "Usa una imagen PNG, JPG o WebP.";
      imageFile.value = "";
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      imageMessage.textContent = "La imagen debe pesar menos de 15 MB.";
      imageFile.value = "";
      return;
    }

    setImage(file);
    render();
    try {
      await localMapImageStorage.save(file);
      imageMessage.textContent = `Imagen “${file.name}” guardada en este navegador y ajustada al plano 0–1000.`;
    } catch {
      imageMessage.textContent = `Imagen “${file.name}” visible durante esta sesión; el navegador no permitió guardarla localmente.`;
    }
    imageFile.value = "";
  });

  imageOpacity?.addEventListener("input", () => {
    imageOpacityValue = Number(imageOpacity.value);
    canvas.select(".geo-background-image").attr("opacity", imageOpacityValue);
  });

  clearImageButton?.addEventListener("click", async () => {
    imageChangeVersion += 1;
    setImage(null);
    render();
    imageMessage.textContent = "Imagen local retirada del plano.";
    try {
      await localMapImageStorage.clear();
    } catch {
      imageMessage.textContent = "Se quitó la imagen de esta vista, pero el navegador no pudo borrar su copia local.";
    }
  });

  store.on("data", render);
  store.on("nodeSelected", ({ attributes } = {}) => {
    canvas.selectAll(".geo-event-point").classed(
      "is-selected",
      (event) => event.identificador === attributes?.identificador,
    );
  });
  store.on("nodeDeselected", () => canvas.selectAll(".geo-event-point").classed("is-selected", false));
  window.addEventListener("sismolab:viewchange", ({ detail }) => {
    if (detail?.activeView === "eventos") window.requestAnimationFrame(() => render());
  });

  render();
  const initialImageVersion = imageChangeVersion;
  localMapImageStorage.load().then((savedImage) => {
    if (imageChangeVersion !== initialImageVersion) return;
    if (!savedImage) return;
    setImage(savedImage);
    render();
    if (imageMessage) imageMessage.textContent = "Imagen local restaurada desde este navegador.";
  }).catch(() => {
    if (imageMessage) imageMessage.textContent = "Puedes elegir una imagen local; el almacenamiento persistente no está disponible en este navegador.";
  });
  return { render };
}
