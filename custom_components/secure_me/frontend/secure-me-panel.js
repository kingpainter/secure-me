// Secure Me Panel
// Version: 0.3.3 (F2 Health Sync Fix merged pixel-perfect)

const DOMAIN = "secure_me";
const VERSION = "0.3.3";

class SecureMePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });

    this._activeTab = "sensors";
    this._alarmState = "disarmed";
    this._data = {
      sensors: [],
      zones: {},
      users: {},
      modules: {},
      notifications: {},
      automations: {},
    };

    this._expandedModule = null;
    this._showDialog = null;
    this._tempConfig = null;
    this._availableEntities = {};
    this._autoSection = "notifications";
    this._renderTimeout = null;
    this._testRunning = false;

    // ==============================
    // F2 FIX: Health sync properties
    // ==============================
    this._healthUpdateUnsubscribe = null;
    this._lastHealthUpdate = null;
    this._healthStatus = null;
    this._healthScore = 100;
  }

  // ==============================
  // Lifecycle
  // ==============================
  connectedCallback() {
    if (this._hass && this._hass.connection) {
      this._subscribeToHealthUpdates();
    }
  }

  disconnectedCallback() {
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
      this._renderTimeout = null;
    }

    if (this._healthUpdateUnsubscribe) {
      this._healthUpdateUnsubscribe();
      this._healthUpdateUnsubscribe = null;
    }
  }

  set hass(hass) {
    this._hass = hass;

    if (hass && hass.connection && !this._healthUpdateUnsubscribe) {
      this._subscribeToHealthUpdates();
    }

    if (!this._initialized) {
      this._initialized = true;
      this._loadData();
    }

    this._queueRender();
  }

  // ==============================
  // F2 FIX: Health event subscription
  // ==============================
  _subscribeToHealthUpdates() {
    if (!this._hass || !this._hass.connection) return;
    if (this._healthUpdateUnsubscribe) return;

    this._healthUpdateUnsubscribe = this._hass.connection.subscribeEvents(
      (event) => {
        if (!event?.data?.modules) return;

        const newData = event.data;
        const shouldUpdate = this._shouldUpdateDisplay(newData);

        this._healthStatus = newData.modules;
        this._healthScore = newData.health_score || 100;
        this._lastHealthUpdate = newData.timestamp;

        if (shouldUpdate || this._activeTab === "testing") {
          this._queueRender();
        }

        console.log("[Secure Me F2] Health updated", {
          score: this._healthScore,
          modules: Object.keys(this._healthStatus).length,
        });
      },
      "secure_me_health_updated"
    );

    console.log("[Secure Me F2] Subscribed to health updates");
  }

  _shouldUpdateDisplay(newHealthData) {
    if (!this._healthStatus) return true;

    const oldModules = this._healthStatus || {};
    const newModules = newHealthData.modules || {};

    for (const id in newModules) {
      if (oldModules[id]?.status !== newModules[id]?.status) {
        return true;
      }
    }

    const oldScore = this._healthScore || 100;
    const newScore = newHealthData.health_score || 100;

    return Math.abs(oldScore - newScore) >= 5;
  }

  async _getHealthStatus() {
    if (this._healthStatus && this._lastHealthUpdate) {
      const age = Date.now() - new Date(this._lastHealthUpdate).getTime();
      if (age < 60000) {
        return this._healthStatus;
      }
    }

    try {
      const result = await this._callWS("get_health_summary", {});
      if (result?.modules) {
        this._healthStatus = result.modules;
        this._healthScore = result.health_score || 100;
        this._lastHealthUpdate = new Date().toISOString();
      }
      return result?.modules || {};
    } catch (err) {
      console.error("[Secure Me F2] Failed to fetch health:", err);
      return {};
    }
  }

  // ==============================
  // Original logic (unchanged from v0.3.0)
  // ==============================

  async _loadData() {
    const data = await this._callWS("get_full_config", {});
    if (data) {
      this._data = data;
      this._queueRender();
    }
  }

  async _callWS(type, data = {}) {
    if (!this._hass) return null;
    try {
      return await this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
    } catch (err) {
      console.error(`Secure Me WS error (${type}):`, err);
      return null;
    }
  }

  _queueRender() {
    if (this._renderTimeout) clearTimeout(this._renderTimeout);
    this._renderTimeout = setTimeout(() => {
      this._render();
      this._renderTimeout = null;
    }, 50);
  }

  _render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          font-family: var(--primary-font-family);
        }
      </style>
      <div>
        <h2>Secure Me Panel v${VERSION}</h2>
        <p>Active tab: ${this._activeTab}</p>
        <p>Health score: ${this._healthScore}</p>
      </div>
    `;
  }
}

customElements.define("secure-me-panel", SecureMePanel);
