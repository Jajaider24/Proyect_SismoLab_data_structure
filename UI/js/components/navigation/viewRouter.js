const DEFAULT_VIEW = "inicio";

export function initViewRouter() {
  const views = [...document.querySelectorAll("[data-view]")];
  const links = [...document.querySelectorAll("[data-view-link]")];
  const availableViews = new Set(views.map((view) => view.dataset.view));

  function renderView({ reveal = false, smooth = true } = {}) {
    const requestedView = window.location.hash.slice(1);
    const activeView = availableViews.has(requestedView)
      ? requestedView
      : DEFAULT_VIEW;

    views.forEach((view) => {
      view.hidden = view.dataset.view !== activeView;
    });
    links.forEach((link) => {
      const selected = link.dataset.viewLink === activeView;
      link.classList.toggle("active", selected);
      if (selected) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });

    if (window.location.hash !== `#${activeView}`) {
      window.history.replaceState(null, "", `#${activeView}`);
    }
    window.dispatchEvent(
      new CustomEvent("sismolab:viewchange", { detail: { activeView } }),
    );

    if (reveal) {
      const activeSection = views.find((view) => view.dataset.view === activeView);
      activeSection?.scrollIntoView({
        behavior: smooth ? "smooth" : "auto",
        block: "start",
      });
      activeSection?.querySelector(".view-title")?.focus({ preventScroll: true });
    }
  }

  window.addEventListener("hashchange", () => renderView({ reveal: true }));
  renderView({ reveal: Boolean(window.location.hash), smooth: false });
  return { renderView };
}
