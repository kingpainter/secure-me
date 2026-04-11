// secure-me-info-card.js
// Secure Me - Info card: persons, weather, alarm status, lock
// type: custom:secure-me-info-card
// VERSION = "1.3.0"

function _esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

class SecureMeInfoCard extends HTMLElement {
  static getStubConfig() {
    return {
      persons: [
        { entity: "person.flemming", name: "Flemming" },
        { entity: "person.sebastian", name: "Sebastian" }
      ],
      weather_entity: "weather.hjem",
      alarm_entity: "alarm_control_panel.secure_me",
      lock_entity: "lock.frontdoor",
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = {};
    this._shellBuilt = false;
  }

  setConfig(config) {
    this._config = config || {};
  }

  set hass(h) {
    this._hass = h;
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
    } else {
      this._update();
    }
  }

  _state(e)   { return this._hass?.states?.[e]?.state ?? "unknown"; }
  _attr(e, a) { return this._hass?.states?.[e]?.attributes?.[a]; }

  _buildShell() {
    this.shadowRoot.innerHTML = `
      <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
        :host {
          display: block;
          --bg:      var(--primary-background-color,   #0f1923);
          --bg2:     var(--secondary-background-color, #1a2535);
          --bg3:     #243044;
          --text:    var(--primary-text-color,   #e2e8f0);
          --sub:     var(--secondary-text-color, #94a3b8);
          --div:     var(--divider-color, rgba(148,163,184,0.12));
          --accent:  #ef4444;
          --accent2: #64748b;
          --green:   #10b981;
          --orange:  #f59e0b;
          --red:     #ef4444;
          --card-radius: 18px;
          font-family: 'DM Sans', var(--paper-font-body1_-_font-family, sans-serif);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        .card {
          background: var(--bg2);
          border-radius: var(--card-radius);
          border: 1px solid var(--div);
          padding: 16px;
          box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,.2));
          overflow: hidden;
        }
        .section-label {
          font-size: 10px;
          font-weight: 700;
          color: var(--sub);
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin: 0 0 8px 2px;
        }
        .divider {
          height: 1px;
          background: var(--div);
          margin: 12px 0;
        }
        .row {
          display: flex;
          align-items: center;
          gap: 12px;
          background: var(--bg3);
          border-radius: 12px;
          border-left: 3px solid var(--div);
          padding: 10px 12px;
          margin-bottom: 6px;
          cursor: pointer;
          transition: opacity .15s;
          user-select: none;
        }
        .row:last-child { margin-bottom: 0; }
        .row:active { opacity: .7; }
        .row.no-tap { cursor: default; }
        .row-icon {
          width: 36px; height: 36px;
          border-radius: 10px;
          background: var(--bg2);
          display: flex; align-items: center; justify-content: center;
          font-size: 18px;
          flex-shrink: 0;
        }
        .avatar {
          width: 36px; height: 36px;
          border-radius: 50%;
          object-fit: cover;
          flex-shrink: 0;
        }
        .row-info { flex: 1; min-width: 0; }
        .row-title {
          font-size: 13px; font-weight: 600;
          color: var(--text);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .row-sub {
          font-size: 11px; margin-top: 2px;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .row-right { text-align: right; flex-shrink: 0; }
        .dot {
          width: 8px; height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
      </style>
      <div class="card">
        <div id="persons-section"></div>
        <div class="divider"></div>
        <div id="weather-section"></div>
        <div class="divider"></div>
        <div id="alarm-section"></div>
        <div id="lock-section"></div>
      </div>`;

    this.shadowRoot.querySelector(".card").addEventListener("click", (e) => {
      const row = e.target.closest("[data-tap]");
      if (!row) return;
      this._moreInfo(row.dataset.tap);
    });

    this._update();
  }

  _update() {
    const root = this.shadowRoot;
    if (!root || !this._hass) return;

    const persons = this._config.persons || [];
    const weatherEntity = this._config.weather_entity || "weather.hjem";
    const alarmEntity   = this._config.alarm_entity   || "alarm_control_panel.secure_me";
    const lockEntity    = this._config.lock_entity    || "lock.frontdoor";

    // Persons
    const ps = root.getElementById("persons-section");
    if (ps) {
      ps.innerHTML = persons.length
        ? `<div class="section-label">Hjemme</div>` +
          persons.map(p => this._personRow(p.entity, p.name)).join("")
        : "";
    }

    // Weather
    const wr = root.getElementById("weather-section");
    if (wr) wr.innerHTML = this._weatherRow(weatherEntity);

    // Alarm
    const ar = root.getElementById("alarm-section");
    if (ar) ar.innerHTML = this._alarmRow(alarmEntity);

    // Lock
    const lr = root.getElementById("lock-section");
    if (lr) lr.innerHTML = this._lockRow(lockEntity);
  }

  _personRow(entity, name) {
    const state = this._state(entity);
    const home  = state === "home";
    const color = home ? "#10b981" : "#64748b";
    const label = home ? "Hjemme" : _esc(state === "unknown" ? "Ukendt" : state);
    const pic   = this._attr(entity, "entity_picture");
    const avatar = pic
      ? `<img src="${pic}" class="avatar">`
      : `<div class="row-icon" style="background:${color}22">
           <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2">
             <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
             <circle cx="12" cy="7" r="4"/>
           </svg>
         </div>`;
    return `
      <div class="row no-tap" style="border-left-color:${color}">
        ${avatar}
        <div class="row-info">
          <div class="row-title">${_esc(name)}</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="dot" style="background:${color}"></div>
      </div>`;
  }

  _weatherRow(entity) {
    const state   = this._state(entity);
    const temp    = this._attr(entity, "temperature");
    const hum     = this._attr(entity, "humidity");
    const name    = this._attr(entity, "friendly_name") || "Vejr";
    const color   = "#0ea5e9";
    const iconMap = {
      "sunny":"\u2600\uFE0F","clear-night":"\uD83C\uDF19","partlycloudy":"\u26C5",
      "cloudy":"\u2601\uFE0F","rainy":"\uD83C\uDF27\uFE0F","snowy":"\u2744\uFE0F",
      "lightning":"\u26A1","windy":"\uD83C\uDF2C\uFE0F","fog":"\uD83C\uDF2B\uFE0F",
      "hail":"\uD83C\uDF27\uFE0F","pouring":"\uD83C\uDF27\uFE0F",
    };
    const icon    = iconMap[state] || "\uD83C\uDF24\uFE0F";
    const tempStr = temp != null ? `${parseFloat(temp).toFixed(1)}\u00b0C` : "--";
    const humStr  = hum  != null ? `${Math.round(hum)}%` : "";
    return `
      <div class="row no-tap" style="border-left-color:${color}">
        <div class="row-icon" style="font-size:20px;background:${color}18">${icon}</div>
        <div class="row-info">
          <div class="row-title">${_esc(name)}</div>
          <div class="row-sub" style="color:var(--sub)">${_esc(state)}</div>
        </div>
        <div class="row-right">
          <div class="row-title" style="color:${color}">${tempStr}</div>
          ${humStr ? `<div class="row-sub" style="color:var(--sub)">${humStr}</div>` : ""}
        </div>
      </div>`;
  }

  _alarmRow(entity) {
    const state = this._state(entity);
    const COLOR = {
      armed_away:       "#ef4444", armed_home:       "#f59e0b",
      armed_night:      "#6366f1", armed_vacation:   "#8b5cf6",
      armed_home_alone: "#10b981", arming:           "#f59e0b",
      pending:          "#f59e0b", triggered:        "#ef4444",
      disarmed:         "#10b981",
    };
    const LABEL = {
      armed_away:       "Aktiveret - vaek",    armed_home:       "Aktiveret - hjemme",
      armed_night:      "Aktiveret - nat",     armed_vacation:   "Aktiveret - ferie",
      armed_home_alone: "Hjemme alene",        arming:           "Aktiverer...",
      pending:          "Indgang registreret", triggered:        "ALARM!",
      disarmed:         "Deaktiveret",
    };
    const color = COLOR[state] || "#64748b";
    const label = LABEL[state] || _esc(state);
    const pulse = ["arming","pending","triggered"].includes(state)
      ? "animation:pulse 1s infinite;" : "";
    return `
      <div class="row" data-tap="${entity}" style="border-left-color:${color}">
        <div class="row-icon" style="background:${color}22;${pulse}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <div class="row-info">
          <div class="row-title">Alarm</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="dot" style="background:${color}"></div>
      </div>`;
  }

  _lockRow(entity) {
    const state  = this._state(entity);
    const locked = state === "locked";
    const color  = locked ? "#10b981" : "#ef4444";
    const label  = locked ? "Laast" : "Ulaast";
    const name   = this._attr(entity, "friendly_name") || "Laasen";
    const pulse  = locked ? "" : "animation:pulse 2s infinite;";
    return `
      <div class="row" data-tap="${entity}" style="border-left-color:${color}">
        <div class="row-icon" style="background:${color}22;${pulse}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2">
            ${locked
              ? '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
              : '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>'}
          </svg>
        </div>
        <div class="row-info">
          <div class="row-title">${_esc(name)}</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="dot" style="background:${color}"></div>
      </div>`;
  }

  _moreInfo(entity) {
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      composed: true, bubbles: true, detail: { entityId: entity }
    }));
  }

  getCardSize() { return 4; }
}

if (!customElements.get("secure-me-info-card")) {
  customElements.define("secure-me-info-card", SecureMeInfoCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.find(c => c.type === "secure-me-info-card")) {
  window.customCards.push({
    type: "secure-me-info-card",
    name: "Secure Me - Info",
    description: "Viser personer, vejr, alarm-status og laas i eet kort.",
    preview: true,
  });
}
