// info-alarm-card.js
// Standalone Lovelace card: personer + vejr + alarm + laas
// Usage:
//   type: custom:info-alarm-card

function _iac_esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

class InfoAlarmCard extends HTMLElement {
  static getStubConfig() { return {}; }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._shellBuilt = false;
  }

  setConfig() {}

  set hass(h) {
    this._hass = h;
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
    } else {
      this._update();
    }
  }

  _state(e)    { return this._hass?.states?.[e]?.state ?? "unknown"; }
  _attr(e, a)  { return this._hass?.states?.[e]?.attributes?.[a]; }
  _picture(e)  { return this._attr(e, "entity_picture"); }

  // ------------------------------------------------------------
  _buildShell() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .card {
          --bg:   var(--card-background-color, #1a2535);
          --bg2:  var(--secondary-background-color, #243044);
          --text: var(--primary-text-color, #e2e8f0);
          --sub:  var(--secondary-text-color, #94a3b8);
          --div:  var(--divider-color, rgba(148,163,184,0.12));
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
          background: var(--bg);
          border-radius: 18px;
          padding: 14px 16px;
          color: var(--text);
          box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.15));
          border-left: 5px solid #10b981;
          background-image: linear-gradient(135deg, #10b98112 0%, transparent 50%);
        }
        .back-btn {
          display: inline-flex; align-items: center; gap: 6px;
          background: var(--bg2); border-radius: 18px;
          padding: 6px 14px; margin-bottom: 12px;
          font-size: 12px; font-weight: 600; color: var(--sub);
          cursor: pointer; transition: opacity .15s;
          border: none; outline: none;
        }
        .back-btn:active { opacity: .6; }
        .card-title {
          font-size: 13px; font-weight: 700; color: var(--sub);
          text-transform: uppercase; letter-spacing: .8px;
          margin-bottom: 12px;
        }
        .row {
          display: flex; align-items: center; gap: 12px;
          background: var(--bg2);
          border-radius: 12px;
          border-left: 4px solid #10b981;
          padding: 10px 12px;
          margin-bottom: 8px;
          cursor: pointer;
          transition: opacity .15s;
        }
        .row:active { opacity: .7; }
        .row.no-action { cursor: default; }
        .row:last-child { margin-bottom: 0; }
        .avatar {
          width: 40px; height: 40px; border-radius: 50%;
          object-fit: cover; flex-shrink: 0;
        }
        .avatar-icon {
          display: flex; align-items: center; justify-content: center;
          background: var(--bg); font-size: 20px;
          width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
        }
        .row-info { flex: 1; min-width: 0; }
        .row-title { font-size: 14px; font-weight: 700; line-height: 1.2; }
        .row-sub   { font-size: 11px; margin-top: 2px; }
        .row-right { text-align: right; flex-shrink: 0; }
        .row-dot   { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:.4} }
        .divider {
          height: 1px; background: var(--div);
          margin: 10px 0;
        }
      </style>
      <ha-card>
        <div class="card">
          <button class="back-btn" id="back-btn">\u2190 Tilbage</button>
          <div class="card-title">Info</div>
          <div id="person-flemming"></div>
          <div id="person-sebastian"></div>
          <div class="divider"></div>
          <div id="weather-row"></div>
          <div class="divider"></div>
          <div id="alarm-row"></div>
          <div id="lock-row"></div>
        </div>
      </ha-card>`;

    // Listeners bound once on static elements
    this.shadowRoot.getElementById("back-btn").addEventListener("click", () => {
      history.back();
    });

    // Event delegation on the card - handles alarm and lock clicks
    this.shadowRoot.querySelector(".card").addEventListener("click", (e) => {
      const row = e.target.closest("[data-action]");
      if (!row) return;
      const action = row.dataset.action;
      if (action === "alarm") this._moreInfo("alarm_control_panel.secure_me");
      if (action === "lock")  this._moreInfo("lock.frontdoor");
    });

    // Render initial content
    this._update();
  }

  // ------------------------------------------------------------
  _update() {
    const root = this.shadowRoot;
    if (!root) return;

    const pf = root.getElementById("person-flemming");
    const ps = root.getElementById("person-sebastian");
    const wr = root.getElementById("weather-row");
    const ar = root.getElementById("alarm-row");
    const lr = root.getElementById("lock-row");

    if (pf) pf.innerHTML = this._personRow("person.flemming", "Flemming");
    if (ps) ps.innerHTML = this._personRow("person.sebastian", "Sebastian");
    if (wr) wr.innerHTML = this._weatherRow();
    if (ar) ar.innerHTML = this._alarmRow();
    if (lr) lr.innerHTML = this._lockRow();
  }

  // ------------------------------------------------------------
  _personRow(entity, name) {
    const state  = this._state(entity);
    const home   = state === "home";
    const color  = home ? "#10b981" : "#ef4444";
    const label  = home ? "Hjemme" : _iac_esc(state === "unknown" ? "Ukendt" : state);
    const pic    = this._picture(entity);
    const avatar = pic
      ? `<img src="${pic}" class="avatar">`
      : `<div class="avatar avatar-icon">\uD83D\uDC64</div>`;
    return `
      <div class="row no-action" style="border-left-color:${color};background-image:linear-gradient(90deg,${color}0e 0%,transparent 40%);">
        ${avatar}
        <div class="row-info">
          <div class="row-title">${_iac_esc(name)}</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="row-dot" style="background:${color}"></div>
      </div>`;
  }

  _weatherRow() {
    const e     = "weather.hjem";
    const state = this._state(e);
    const temp  = this._attr(e, "temperature");
    const hum   = this._attr(e, "humidity");
    const color = "#0ea5e9";
    const icons = {
      "sunny":"\u2600\uFE0F","clear-night":"\uD83C\uDF19","partlycloudy":"\u26C5",
      "cloudy":"\u2601\uFE0F","rainy":"\uD83C\uDF27\uFE0F","snowy":"\u2744\uFE0F",
      "lightning":"\u26A1","windy":"\uD83C\uDF2C\uFE0F","fog":"\uD83C\uDF2B\uFE0F",
      "hail":"\uD83C\uDF27\uFE0F","pouring":"\uD83C\uDF27\uFE0F"
    };
    const icon    = icons[state] || "\uD83C\uDF24\uFE0F";
    const tempStr = temp != null ? `${parseFloat(temp).toFixed(1)}\u00a0\u00b0C` : "\u2013";
    const humStr  = hum  != null ? `${Math.round(hum)}\u00a0%` : "";
    return `
      <div class="row no-action" style="border-left-color:${color};background-image:linear-gradient(90deg,${color}0e 0%,transparent 40%);">
        <div class="avatar-icon" style="font-size:26px">${icon}</div>
        <div class="row-info">
          <div class="row-title">${_iac_esc(this._attr(e,"friendly_name") || "Vejr")}</div>
          <div class="row-sub" style="color:var(--sub)">${_iac_esc(state)}</div>
        </div>
        <div class="row-right">
          <div class="row-title" style="color:${color}">${tempStr}</div>
          ${humStr ? `<div class="row-sub">\uD83D\uDCA7 ${humStr}</div>` : ""}
        </div>
      </div>`;
  }

  _alarmRow() {
    const e     = "alarm_control_panel.secure_me";
    const state = this._state(e);

    // Colors per state
    const color =
      state === "armed_away"       ? "#ef4444"
    : state === "armed_home"       ? "#f59e0b"
    : state === "armed_night"      ? "#6366f1"
    : state === "armed_vacation"   ? "#8b5cf6"
    : state === "armed_home_alone" ? "#10b981"
    : state === "arming"           ? "#f59e0b"
    : state === "pending"          ? "#f59e0b"
    : state === "triggered"        ? "#ef4444"
    :                                "#10b981";  // disarmed

    // Danish labels
    const label =
      state === "armed_away"       ? "Aktiveret - v\u00e6k"
    : state === "armed_home"       ? "Aktiveret - hjemme"
    : state === "armed_night"      ? "Aktiveret - nat"
    : state === "armed_vacation"   ? "Aktiveret - ferie"
    : state === "armed_home_alone" ? "Hjemme alene"
    : state === "arming"           ? "Aktiverer..."
    : state === "pending"          ? "Indgang registreret"
    : state === "triggered"        ? "ALARM!"
    : state === "disarmed"         ? "Deaktiveret"
    :                                _iac_esc(state);

    // Icons (unicode escapes only - no raw emoji)
    const icon =
      state === "armed_away"       ? "\uD83D\uDEA8"
    : state === "armed_home"       ? "\uD83D\uDD14"
    : state === "armed_night"      ? "\uD83C\uDF19"
    : state === "armed_vacation"   ? "\uD83C\uDFD6\uFE0F"
    : state === "armed_home_alone" ? "\uD83D\uDC66"
    : state === "triggered"        ? "\uD83D\uDEA8"
    :                                "\uD83D\uDEE1\uFE0F";

    const pulse =
      state === "armed_away"  ? "animation:blink 1.5s infinite;"
    : state === "triggered"   ? "animation:blink 0.8s infinite;"
    : state === "arming"      ? "animation:blink 1s infinite;"
    : state === "pending"     ? "animation:blink 1s infinite;"
    :                           "";

    return `
      <div class="row" data-action="alarm" style="border-left-color:${color};background-image:linear-gradient(90deg,${color}0e 0%,transparent 40%);">
        <div class="avatar-icon" style="font-size:24px;${pulse}">${icon}</div>
        <div class="row-info">
          <div class="row-title">Alarm</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="row-dot" style="background:${color}"></div>
      </div>`;
  }

  _lockRow() {
    const e      = "lock.frontdoor";
    const state  = this._state(e);
    const locked = state === "locked";
    const color  = locked ? "#10b981" : "#ef4444";
    const label  = locked ? "L\u00e5st" : "Ul\u00e5st";
    const icon   = locked ? "\uD83D\uDD12" : "\uD83D\uDD13";
    const pulse  = locked ? "" : "animation:blink 2s infinite;";
    return `
      <div class="row" data-action="lock" style="border-left-color:${color};background-image:linear-gradient(90deg,${color}0e 0%,transparent 40%);">
        <div class="avatar-icon" style="font-size:24px;${pulse}">${icon}</div>
        <div class="row-info">
          <div class="row-title">Ford\u00f8r</div>
          <div class="row-sub" style="color:${color}">${label}</div>
        </div>
        <div class="row-dot" style="background:${color}"></div>
      </div>`;
  }

  _moreInfo(entity) {
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      composed: true, bubbles: true, detail: { entityId: entity }
    }));
  }

  getCardSize() { return 5; }
}

if (!customElements.get("info-alarm-card")) {
  customElements.define("info-alarm-card", InfoAlarmCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.find(c => c.type === "info-alarm-card")) {
  window.customCards.push({
    type: "info-alarm-card",
    name: "Info & Alarm",
    description: "Personer, vejr, alarm og laas i et kort",
    preview: true,
  });
}
