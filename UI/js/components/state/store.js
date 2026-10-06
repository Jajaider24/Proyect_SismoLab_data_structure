class Store {
  constructor() {
    this.state = {
      currentData: { values: [], tree: null },
      selectedIdentifier: null,
      selectedNode: null,
      activity: JSON.parse(localStorage.getItem("sismolab-activity") || "[]"),
      stressMode: false,
      stressRunning: false,
      stressAudit: null,
      isOnline: false,
    };
    this.listeners = new Map();
  }

  getState() {
    return this.state;
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((cb) => {
        try {
          cb(data);
        } catch (error) {
          console.error(`Error en listener de evento '${event}':`, error);
        }
      });
    }
  }

  setData(data) {
    this.state.currentData = data || { values: [], tree: null };
    this.setConnection(true);
    this.emit("data", this.state.currentData);
  }

  selectNode(nodeData) {
    this.state.selectedNode = nodeData;
    this.state.selectedIdentifier = nodeData?.attributes?.identificador ?? null;
    this.emit("nodeSelected", nodeData);
  }

  clearSelection() {
    this.state.selectedNode = null;
    this.state.selectedIdentifier = null;
    this.emit("nodeDeselected");
  }

  addActivity(label, detail, isError = false) {
    const item = {
      label,
      detail,
      isError,
      at: new Date().toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    this.state.activity.unshift(item);
    this.state.activity = this.state.activity.slice(0, 8);
    localStorage.setItem("sismolab-activity", JSON.stringify(this.state.activity));
    this.emit("activity", this.state.activity);
  }

  clearActivity() {
    this.state.activity = [];
    localStorage.removeItem("sismolab-activity");
    this.emit("activity", this.state.activity);
  }

  setStress(statusData) {
    if (!statusData) return;
    this.state.stressMode = statusData.mode === "stress";
    this.state.stressAudit = statusData.audit || null;
    this.emit("stress", {
      mode: this.state.stressMode,
      audit: this.state.stressAudit,
      running: this.state.stressRunning,
      raw: statusData,
    });
  }

  setStressRunning(running) {
    this.state.stressRunning = running;
    this.emit("stressRunning", running);
  }

  setConnection(online) {
    this.state.isOnline = online;
    this.emit("connection", {
      online,
      count: this.state.currentData.values?.length || 0,
    });
  }
}

export const store = new Store();

