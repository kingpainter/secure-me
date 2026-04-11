/**
 * Secure Me Alarm Card
 * VERSION: 1.3.0
 *
 * Custom Lovelace card for Home Assistant.
 * Provides alarm arm/disarm, Home Alone mode, and TTS drop-in messaging
 * from mobile or dashboard without opening the full Secure Me panel.
 *
 * Usage (ui-lovelace.yaml / UI card editor):
 *   type: custom:secure-me-alarm-card
 *   entity: alarm_control_panel.secure_me   (optional, auto-detected)
 *   tts_messages:
 *     - label: "Mad er klar"
 *       message: "Hej, maden er klar. Kom ned til bordet."
 *     - label: "Ring til mig"
 *       message: "Hej, ring venligst til mig nu."
 *     - label: "Gaa i seng"
 *       message: "Det er sengetid. Sluk for skaermen."
 *   show_home_alone: true
 *   show_tts: true
 *   require_code: false
 */

const DOMAIN = "secure_me";
const CARD_VERSION = "1.3.0";

// ── Helpers ──────────────────────────────────────────────────────────────────

function icon(name) {
  const icons = {
    shield:   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    home:     '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    lock:     '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    moon:     '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    vacation: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    unlock:   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
    child:    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M6 20v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/></svg>',
    camera:   '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
    speaker:  '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
    send:     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    eye:      '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    edit:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    check:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    close:    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  };
  return icons[name] || "";
}

// ── State helpers ─────────────────────────────────────────────────────────────

function stateLabel(state) {
  const map = {
    disarmed:        "Disarmed",
    arming:          "Arming...",
    armed_away:      "Armed Away",
    armed_home:      "Armed Home",
    armed_night:     "Armed Night",
    armed_vacation:  "Armed Vacation",
    pending:         "Entry Delay",
    triggered:       "TRIGGERED",
  };
  return map[state] || state;
}

function stateColor(state) {
  if (state === "disarmed")  return "#10b981";
  if (state === "triggered") return "#ef4444";
  if (state === "arming" || state === "pending") return "#f59e0b";
  return "#ef4444"; // any armed state
}

function stateBg(state) {
  if (state === "disarmed")  return "rgba(16,185,129,0.14)";
  if (state === "triggered") return "rgba(239,68,68,0.18)";
  if (state === "arming" || state === "pending") return "rgba(245,158,11,0.18)";
  return "rgba(239,68,68,0.14)";
}

// ── Card class ────────────────────────────────────────────────────────────────

class SecureMeAlarmCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass       = null;
    this._config     = {};
    this._pinBuffer  = "";
    this._pendingAction = null; // arm mode waiting for PIN
    this._homeAlone  = false;
    this._ttsLoading = {};      // { idx: true } while sending
    this._editIdx    = null;    // which TTS message is being edited
    this._editText   = "";
    this._toastTimer = null;
    this._rendered   = false;
  }

  // ── Lovelace lifecycle ────────────────────────────────────────────────────

  setConfig(config) {
    this._config = {
      entity:           config.entity  || null,
      show_home_alone:  config.show_home_alone  !== false,
      show_tts:         config.show_tts         !== false,
      require_code:     config.require_code      || false,
      tts_messages:     config.tts_messages      || [
        { label: "Mad er klar",  message: "Hej, maden er klar. Kom ned til bordet." },
        { label: "Ring til mig", message: "Hej, ring venligst til mig nu." },
        { label: "Gaa i seng",   message: "Det er sengetid. Sluk for skaermen." },
      ],
    };
    // Deep-copy so edits don't mutate config directly
    this._messages = this._config.tts_messages.map(m => ({ ...m }));
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  static getConfigElement() {
    return document.createElement("secure-me-alarm-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "",
      show_home_alone: true,
      show_tts: true,
      require_code: false,
      tts_messages: [
        { label: "Mad er klar",  message: "Hej, maden er klar. Kom ned til bordet." },
        { label: "Ring til mig", message: "Hej, ring venligst til mig nu." },
        { label: "Gaa i seng",   message: "Det er sengetid. Sluk for skaermen." },
      ],
    };
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  _alarmEntity() {
    if (!this._hass) return null;
    // Use configured entity or auto-detect first alarm_control_panel
    const entityId = this._config.entity ||
      Object.keys(this._hass.states).find(k => k.startsWith("alarm_control_panel."));
    return entityId ? this._hass.states[entityId] : null;
  }

  _alarmEntityId() {
    const e = this._alarmEntity();
    return e ? e.entity_id : null;
  }

  async _callWS(type, data = {}) {
    if (!this._hass) return null;
    try {
      return await this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
    } catch (err) {
      console.error(`Secure Me card WS error (${type}):`, err);
      return null;
    }
  }

  _toast(msg, type = "info") {
    const el = this.shadowRoot.getElementById("card-toast");
    if (!el) return;
    el.textContent = msg;
    el.className = `card-toast ${type} show`;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      el.className = "card-toast";
    }, 3000);
  }

  // ── Arm / disarm ──────────────────────────────────────────────────────────

  async _arm(mode) {
    const entityId = this._alarmEntityId();
    if (!entityId) return;

    const needsCode = this._config.require_code ||
      this._alarmEntity()?.attributes?.code_format;

    if (needsCode && mode !== "disarm") {
      this._pendingAction = mode;
      this._pinBuffer = "";
      this._render();
      return;
    }

    await this._doArm(mode, "");
  }

  async _doArm(mode, code) {
    const entityId = this._alarmEntityId();
    if (!entityId) return;

    const service = mode === "disarm" ? "disarm" : `arm_${mode}`;
    const data = { entity_id: entityId };
    if (code) data.code = code;

    try {
      await this._hass.callService("alarm_control_panel", service, data);
      this._pendingAction = null;
      this._pinBuffer = "";
    } catch (err) {
      this._toast("Failed: " + (err.message || "unknown error"), "error");
    }
    this._render();
  }

  // ── Home Alone ────────────────────────────────────────────────────────────

  async _toggleHomeAlone() {
    const newState = !this._homeAlone;
    const result = await this._callWS("set_fake_presence", { active: newState });
    if (result !== null) {
      this._homeAlone = result.active ?? newState;
      this._toast(
        this._homeAlone ? "Home Alone mode activated" : "Home Alone mode deactivated",
        this._homeAlone ? "success" : "info"
      );
      this._render();
    }
  }

  async _loadHomeAloneState() {
    const result = await this._callWS("get_fake_presence");
    if (result) {
      this._homeAlone = result.active || false;
      this._render();
    }
  }

  // ── TTS ───────────────────────────────────────────────────────────────────

  async _sendTTS(idx) {
    const msg = this._messages[idx];
    if (!msg || this._ttsLoading[idx]) return;
    this._ttsLoading[idx] = true;
    this._render();

    const result = await this._callWS("test_tts", { message: msg.message });
    this._ttsLoading[idx] = false;

    if (result && !result.error) {
      this._toast(`Sent: "${msg.label}"`, "success");
    } else {
      this._toast("TTS failed — check TTS module config", "error");
    }
    this._render();
  }

  _startEdit(idx) {
    this._editIdx  = idx;
    this._editText = this._messages[idx].message;
    this._render();
    // Focus textarea after render
    setTimeout(() => {
      const ta = this.shadowRoot.getElementById("tts-edit-area");
      if (ta) { ta.focus(); ta.select(); }
    }, 50);
  }

  _saveEdit() {
    if (this._editIdx === null) return;
    this._messages[this._editIdx].message = this._editText.trim() || this._messages[this._editIdx].message;
    this._editIdx = null;
    this._editText = "";
    this._render();
  }

  _cancelEdit() {
    this._editIdx = null;
    this._editText = "";
    this._render();
  }

  // ── PIN pad ───────────────────────────────────────────────────────────────

  _pinPress(ch) {
    if (ch === "backspace") {
      this._pinBuffer = this._pinBuffer.slice(0, -1);
    } else if (ch === "clear") {
      this._pinBuffer = "";
    } else if (this._pinBuffer.length < 8) {
      this._pinBuffer += ch;
    }
    this._renderPin();
  }

  _pinConfirm() {
    if (!this._pinBuffer) return;
    this._doArm(this._pendingAction, this._pinBuffer);
  }

  _pinCancel() {
    this._pendingAction = null;
    this._pinBuffer = "";
    this._render();
  }

  _renderPin() {
    const dots = this.shadowRoot.getElementById("pin-dots");
    if (dots) {
      dots.innerHTML = Array.from({ length: 8 }, (_, i) =>
        `<div class="pin-dot ${i < this._pinBuffer.length ? "filled" : ""}"></div>`
      ).join("");
    }
  }

  // ── CSS ───────────────────────────────────────────────────────────────────

  _css() {
    return `
      :host {
        --accent:  #7c3aed;
        --accent2: #3b82f6;
        --green:   #10b981;
        --red:     #ef4444;
        --amber:   #f59e0b;
        --bg:      var(--ha-card-background, var(--card-background-color, #1a2535));
        --bg2:     rgba(255,255,255,0.05);
        --bg3:     rgba(255,255,255,0.09);
        --text:    var(--primary-text-color, #e2e8f0);
        --sub:     var(--secondary-text-color, #94a3b8);
        --div:     var(--divider-color, rgba(148,163,184,0.15));
        --radius:  16px;
        display: block;
        font-family: var(--paper-font-body1_-_font-family, sans-serif);
      }

      ha-card {
        background: var(--bg);
        border-radius: var(--radius);
        overflow: hidden;
        padding: 0;
      }

      * { box-sizing: border-box; margin: 0; padding: 0; }

      /* ── Header ── */
      .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px 12px;
        border-bottom: 1px solid var(--div);
      }
      .card-logo {
        width: 38px; height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(124,58,237,0.25);
      }
      .card-logo svg { width: 20px; height: 20px; color: #fff; }
      .card-title { font-size: 16px; font-weight: 700; color: var(--text); }
      .card-sub   { font-size: 11px; color: var(--sub); margin-top: 1px; }

      /* ── Status pill ── */
      .status-pill {
        margin-left: auto;
        display: inline-flex; align-items: center; gap: 6px;
        padding: 5px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 700;
        flex-shrink: 0;
      }
      .status-dot {
        width: 7px; height: 7px;
        border-radius: 50%; background: currentColor;
        box-shadow: 0 0 6px currentColor;
      }
      .status-pill.triggered { animation: pulse-red 1s ease-in-out infinite; }
      @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
        50%       { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
      }

      /* ── Sections ── */
      .section {
        padding: 16px 20px;
        border-bottom: 1px solid var(--div);
      }
      .section:last-child { border-bottom: none; }
      .section-label {
        font-size: 10px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: var(--sub); margin-bottom: 12px;
      }

      /* ── Arm buttons grid ── */
      .arm-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 10px;
      }
      .arm-btn {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 6px;
        padding: 14px 8px;
        border-radius: 12px;
        border: 1.5px solid transparent;
        background: var(--bg2);
        color: var(--sub);
        cursor: pointer;
        font-size: 12px; font-weight: 600;
        font-family: inherit;
        transition: all 0.15s ease;
        -webkit-tap-highlight-color: transparent;
      }
      .arm-btn svg { width: 22px; height: 22px; }
      .arm-btn:hover { background: var(--bg3); color: var(--text); }
      .arm-btn:active { transform: scale(0.96); }
      .arm-btn.active {
        border-color: currentColor;
      }
      .arm-btn.home    { color: var(--green); }
      .arm-btn.away    { color: var(--accent2); }
      .arm-btn.night   { color: var(--accent); }
      .arm-btn.vacation{ color: var(--amber); }
      .arm-btn.home.active    { background: rgba(16,185,129,0.12); }
      .arm-btn.away.active    { background: rgba(59,130,246,0.12); }
      .arm-btn.night.active   { background: rgba(124,58,237,0.12); }
      .arm-btn.vacation.active{ background: rgba(245,158,11,0.12); }

      .disarm-btn {
        width: 100%; padding: 13px;
        border-radius: 12px; border: none;
        background: rgba(16,185,129,0.15);
        color: var(--green); font-size: 14px; font-weight: 700;
        font-family: inherit; cursor: pointer;
        display: flex; align-items: center; justify-content: center; gap: 8px;
        transition: all 0.15s;
        -webkit-tap-highlight-color: transparent;
      }
      .disarm-btn:hover  { background: rgba(16,185,129,0.22); }
      .disarm-btn:active { transform: scale(0.98); }

      /* ── PIN pad ── */
      .pin-overlay {
        padding: 4px 0 8px;
      }
      .pin-label {
        text-align: center; font-size: 13px; color: var(--sub);
        margin-bottom: 14px;
      }
      .pin-dots {
        display: flex; justify-content: center; gap: 10px;
        margin-bottom: 18px;
      }
      .pin-dot {
        width: 12px; height: 12px; border-radius: 50%;
        border: 2px solid var(--div);
        background: transparent;
        transition: background 0.1s;
      }
      .pin-dot.filled { background: var(--accent); border-color: var(--accent); }
      .pin-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
      }
      .pin-key {
        padding: 16px; border-radius: 12px;
        border: none; background: var(--bg2);
        color: var(--text); font-size: 18px; font-weight: 600;
        font-family: inherit; cursor: pointer;
        transition: background 0.1s;
        -webkit-tap-highlight-color: transparent;
      }
      .pin-key:hover  { background: var(--bg3); }
      .pin-key:active { background: var(--bg3); transform: scale(0.95); }
      .pin-key.confirm { background: var(--accent); color: #fff; font-size: 14px; }
      .pin-key.cancel  { background: rgba(239,68,68,0.15); color: var(--red); font-size: 13px; }
      .pin-key.back    { color: var(--sub); font-size: 14px; }

      /* ── Home Alone ── */
      .home-alone-row {
        display: flex; align-items: center; gap: 12px;
      }
      .home-alone-icon {
        width: 40px; height: 40px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0; transition: background 0.2s;
      }
      .home-alone-icon.on  { background: rgba(124,58,237,0.18); color: var(--accent); }
      .home-alone-icon.off { background: var(--bg2); color: var(--sub); }
      .home-alone-icon svg { width: 22px; height: 22px; }
      .home-alone-info { flex: 1; }
      .home-alone-title {
        font-size: 14px; font-weight: 600; color: var(--text);
      }
      .home-alone-sub {
        font-size: 12px; color: var(--sub); margin-top: 2px;
      }
      .toggle {
        width: 48px; height: 26px; border-radius: 26px;
        background: var(--bg3); cursor: pointer;
        position: relative; transition: background 0.2s;
        flex-shrink: 0; border: none; padding: 0;
        -webkit-tap-highlight-color: transparent;
      }
      .toggle.on { background: var(--accent); }
      .toggle .dot {
        width: 20px; height: 20px; border-radius: 50%;
        background: #fff; position: absolute; top: 3px; left: 3px;
        transition: left 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,0.35);
      }
      .toggle.on .dot { left: 25px; }

      /* ── Camera badges ── */
      .cam-badges {
        display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;
      }
      .cam-badge {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 500;
        background: rgba(124,58,237,0.12);
        color: var(--accent);
      }
      .cam-badge svg { width: 12px; height: 12px; }

      /* ── TTS messages ── */
      .tts-list { display: flex; flex-direction: column; gap: 8px; }
      .tts-row {
        display: flex; align-items: center; gap: 10px;
        background: var(--bg2); border-radius: 10px;
        padding: 10px 12px;
        border: 1px solid var(--div);
      }
      .tts-info { flex: 1; min-width: 0; }
      .tts-label {
        font-size: 13px; font-weight: 600; color: var(--text);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      }
      .tts-msg {
        font-size: 11px; color: var(--sub); margin-top: 2px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      }
      .tts-actions { display: flex; gap: 6px; flex-shrink: 0; }
      .tts-btn {
        display: flex; align-items: center; justify-content: center;
        width: 32px; height: 32px; border-radius: 8px; border: none;
        cursor: pointer; font-family: inherit; transition: all 0.15s;
        -webkit-tap-highlight-color: transparent;
      }
      .tts-btn.send { background: var(--accent); color: #fff; }
      .tts-btn.send:hover { filter: brightness(1.15); }
      .tts-btn.send:disabled { opacity: 0.5; cursor: default; }
      .tts-btn.edit { background: var(--bg3); color: var(--sub); }
      .tts-btn.edit:hover { color: var(--text); }

      /* ── TTS edit inline ── */
      .tts-edit-box {
        background: var(--bg2); border-radius: 10px;
        padding: 12px; border: 1px solid var(--accent);
      }
      .tts-edit-label {
        font-size: 11px; color: var(--sub); margin-bottom: 6px;
      }
      textarea.tts-area {
        width: 100%; min-height: 64px; resize: vertical;
        background: rgba(255,255,255,0.07); color: var(--text);
        border: 1px solid var(--div); border-radius: 8px;
        padding: 8px 10px; font-size: 13px; font-family: inherit;
        margin-bottom: 8px;
      }
      textarea.tts-area:focus { outline: none; border-color: var(--accent); }
      .tts-edit-actions { display: flex; gap: 8px; justify-content: flex-end; }
      .btn-sm {
        padding: 6px 14px; border-radius: 8px; border: none;
        font-size: 12px; font-weight: 600; cursor: pointer;
        font-family: inherit; display: flex; align-items: center; gap: 4px;
        transition: all 0.15s; -webkit-tap-highlight-color: transparent;
      }
      .btn-sm.primary { background: var(--accent); color: #fff; }
      .btn-sm.ghost   { background: var(--bg3); color: var(--sub); }
      .btn-sm:hover   { filter: brightness(1.1); }

      /* ── Toast ── */
      .card-toast {
        position: absolute; bottom: 12px; left: 50%;
        transform: translateX(-50%) translateY(8px);
        background: #1e293b; color: var(--text);
        padding: 8px 16px; border-radius: 20px;
        font-size: 13px; font-weight: 500;
        opacity: 0; pointer-events: none;
        transition: opacity 0.2s, transform 0.2s;
        white-space: nowrap; z-index: 10;
        border: 1px solid var(--div);
      }
      .card-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
      .card-toast.success { border-color: rgba(16,185,129,0.4);  color: var(--green); }
      .card-toast.error   { border-color: rgba(239,68,68,0.4);   color: var(--red); }
      .card-toast.info    { border-color: rgba(124,58,237,0.3);  color: var(--accent); }

      /* Spinner */
      .spin {
        width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3);
        border-top-color: #fff; border-radius: 50%;
        animation: spin 0.6s linear infinite;
      }
      @keyframes spin { to { transform: rotate(360deg); } }
    `;
  }

  // ── Render ────────────────────────────────────────────────────────────────

  _render() {
    const alarm    = this._alarmEntity();
    const state    = alarm?.state || "disarmed";
    const attrs    = alarm?.attributes || {};
    const isPIN    = !!this._pendingAction;
    const color    = stateColor(state);
    const bg       = stateBg(state);

    const armed    = state !== "disarmed" && state !== "arming";
    const arming   = state === "arming" || state === "pending";
    const triggered = state === "triggered";

    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>
      <ha-card>
        <!-- Header -->
        <div class="card-header">
          <div class="card-logo">${icon("shield")}</div>
          <div>
            <div class="card-title">Secure Me</div>
            <div class="card-sub">Alarm Card</div>
          </div>
          <div class="status-pill ${triggered ? "triggered" : ""}"
               style="background:${bg};color:${color}">
            <span class="status-dot"></span>
            ${stateLabel(state)}${arming && attrs.countdown ? ` &mdash; ${attrs.countdown}s` : ""}
          </div>
        </div>

        <!-- Alarm section -->
        <div class="section">
          <div class="section-label">${icon("shield")} Alarm</div>
          ${isPIN ? this._renderPIN() : this._renderArmButtons(state)}
        </div>

        <!-- Home Alone section -->
        ${this._config.show_home_alone ? `
        <div class="section">
          <div class="section-label">${icon("child")} Home Alone</div>
          ${this._renderHomeAlone()}
        </div>` : ""}

        <!-- TTS section -->
        ${this._config.show_tts ? `
        <div class="section">
          <div class="section-label">${icon("speaker")} Drop-in / TTS</div>
          ${this._renderTTS()}
        </div>` : ""}

        <div class="card-toast" id="card-toast"></div>
      </ha-card>
    `;

    this._attachListeners();

    if (!this._rendered) {
      this._rendered = true;
      this._loadHomeAloneState();
    }
  }

  _renderArmButtons(state) {
    const modes = [
      { key: "home",     label: "Home",     ico: "home"    },
      { key: "away",     label: "Away",     ico: "lock"    },
      { key: "night",    label: "Night",    ico: "moon"    },
      { key: "vacation", label: "Vacation", ico: "vacation" },
    ];

    const disarmed = state === "disarmed";

    return `
      <div class="arm-grid">
        ${modes.map(m => `
          <button class="arm-btn ${m.key} ${state === "armed_" + m.key ? "active" : ""}"
                  data-arm="${m.key}">
            ${icon(m.ico)}
            ${m.label}
          </button>
        `).join("")}
      </div>
      ${!disarmed ? `
        <button class="disarm-btn" data-arm="disarm">
          ${icon("unlock")} Disarm
        </button>` : ""}
    `;
  }

  _renderPIN() {
    const mode = this._pendingAction || "";
    const label = mode.charAt(0).toUpperCase() + mode.slice(1);
    return `
      <div class="pin-overlay">
        <div class="pin-label">Enter code to arm <strong>${label}</strong></div>
        <div class="pin-dots" id="pin-dots">
          ${Array.from({ length: 8 }, (_, i) =>
            `<div class="pin-dot ${i < this._pinBuffer.length ? "filled" : ""}"></div>`
          ).join("")}
        </div>
        <div class="pin-grid">
          ${[1,2,3,4,5,6,7,8,9].map(n => `
            <button class="pin-key" data-pin="${n}">${n}</button>
          `).join("")}
          <button class="pin-key cancel" data-pin-action="cancel">Cancel</button>
          <button class="pin-key" data-pin="0">0</button>
          <button class="pin-key back" data-pin-action="backspace">&#9003;</button>
        </div>
        <div style="display:flex;gap:8px;margin-top:10px;">
          <button class="disarm-btn" style="background:rgba(124,58,237,0.15);color:var(--accent);"
                  data-pin-action="confirm">
            ${icon("check")} Confirm
          </button>
        </div>
      </div>
    `;
  }

  _renderHomeAlone() {
    const on = this._homeAlone;
    return `
      <div class="home-alone-row">
        <div class="home-alone-icon ${on ? "on" : "off"}">${icon("child")}</div>
        <div class="home-alone-info">
          <div class="home-alone-title">Home Alone Mode</div>
          <div class="home-alone-sub">
            ${on
              ? "Active &mdash; cameras in live view"
              : "Inactive &mdash; cameras off"}
          </div>
        </div>
        <button class="toggle ${on ? "on" : ""}" id="ha-toggle">
          <div class="dot"></div>
        </button>
      </div>
      ${on ? `
        <div class="cam-badges" id="cam-badges">
          <div class="cam-badge">${icon("camera")} Loading cameras...</div>
        </div>` : ""}
    `;
  }

  _renderTTS() {
    return `
      <div class="tts-list">
        ${this._messages.map((m, i) => {
          if (this._editIdx === i) return this._renderTTSEdit(i, m);
          return `
            <div class="tts-row">
              <div class="tts-info">
                <div class="tts-label">${m.label}</div>
                <div class="tts-msg">${m.message}</div>
              </div>
              <div class="tts-actions">
                <button class="tts-btn edit" data-tts-edit="${i}" title="Edit message">
                  ${icon("edit")}
                </button>
                <button class="tts-btn send" data-tts-send="${i}"
                        ${this._ttsLoading[i] ? "disabled" : ""} title="Send message">
                  ${this._ttsLoading[i]
                    ? '<div class="spin"></div>'
                    : icon("send")}
                </button>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  _renderTTSEdit(i, m) {
    return `
      <div class="tts-edit-box">
        <div class="tts-edit-label">Edit message for: <strong>${m.label}</strong></div>
        <textarea class="tts-area" id="tts-edit-area"
                  placeholder="Type message...">${this._editText}</textarea>
        <div class="tts-edit-actions">
          <button class="btn-sm ghost" data-tts-cancel-edit>Cancel</button>
          <button class="btn-sm primary" data-tts-save-edit>
            ${icon("check")} Save
          </button>
        </div>
      </div>
    `;
  }

  // ── Event listeners ───────────────────────────────────────────────────────

  _attachListeners() {
    const root = this.shadowRoot;

    // Arm/disarm
    root.querySelectorAll("[data-arm]").forEach(btn => {
      btn.addEventListener("click", () => this._arm(btn.dataset.arm));
    });

    // PIN
    root.querySelectorAll("[data-pin]").forEach(btn => {
      btn.addEventListener("click", () => this._pinPress(btn.dataset.pin));
    });
    root.querySelectorAll("[data-pin-action]").forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.pinAction;
        if (action === "confirm")   this._pinConfirm();
        else if (action === "cancel")    this._pinCancel();
        else if (action === "backspace") this._pinPress("backspace");
      });
    });

    // Home Alone toggle
    const haToggle = root.getElementById("ha-toggle");
    if (haToggle) haToggle.addEventListener("click", () => this._toggleHomeAlone());

    // Load camera badges when Home Alone is on
    if (this._homeAlone) this._loadCamBadges();

    // TTS
    root.querySelectorAll("[data-tts-send]").forEach(btn => {
      btn.addEventListener("click", () => this._sendTTS(parseInt(btn.dataset.ttsSend)));
    });
    root.querySelectorAll("[data-tts-edit]").forEach(btn => {
      btn.addEventListener("click", () => this._startEdit(parseInt(btn.dataset.ttsEdit)));
    });

    // TTS edit
    const ta = root.getElementById("tts-edit-area");
    if (ta) {
      ta.addEventListener("input", e => { this._editText = e.target.value; });
    }
    const saveBtn = root.querySelector("[data-tts-save-edit]");
    if (saveBtn) saveBtn.addEventListener("click", () => this._saveEdit());
    const cancelBtn = root.querySelector("[data-tts-cancel-edit]");
    if (cancelBtn) cancelBtn.addEventListener("click", () => this._cancelEdit());
  }

  async _loadCamBadges() {
    const result = await this._callWS("get_fake_presence");
    const cams   = result?.home_alone_cameras || [];
    const el     = this.shadowRoot.getElementById("cam-badges");
    if (!el) return;

    if (cams.length === 0) {
      el.innerHTML = `<div class="cam-badge" style="color:var(--sub)">No cameras configured</div>`;
    } else {
      el.innerHTML = cams.map(c => {
        const name = c.replace("camera.", "").replace(/_/g, " ");
        return `<div class="cam-badge">${icon("camera")} ${name}</div>`;
      }).join("");
    }
  }
}

// ── Simple config editor ──────────────────────────────────────────────────────

class SecureMeAlarmCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _fire(config) {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config }, bubbles: true, composed: true,
    }));
  }

  _render() {
    const c = this._config || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        * { box-sizing: border-box; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
        .row { margin-bottom: 12px; }
        label { display: block; font-size: 12px; color: var(--secondary-text-color, #94a3b8); margin-bottom: 4px; }
        input, select { width: 100%; padding: 8px 10px; border-radius: 6px; background: var(--secondary-background-color, #1a2535); color: var(--primary-text-color, #e2e8f0); border: 1px solid var(--divider-color, rgba(148,163,184,0.2)); font-size: 13px; }
        .check-row { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--primary-text-color, #e2e8f0); }
        input[type=checkbox] { width: auto; }
        h4 { font-size: 13px; color: var(--secondary-text-color, #94a3b8); margin: 16px 0 8px; text-transform: uppercase; letter-spacing: 0.05em; }
        .msg-row { display: grid; grid-template-columns: 1fr 2fr; gap: 8px; margin-bottom: 8px; }
      </style>

      <div class="row">
        <label>Alarm entity (leave blank for auto-detect)</label>
        <input id="entity" value="${c.entity || ""}" placeholder="alarm_control_panel.secure_me">
      </div>

      <div class="row">
        <label class="check-row">
          <input type="checkbox" id="show_ha" ${c.show_home_alone !== false ? "checked" : ""}>
          Show Home Alone section
        </label>
      </div>
      <div class="row">
        <label class="check-row">
          <input type="checkbox" id="show_tts" ${c.show_tts !== false ? "checked" : ""}>
          Show TTS / Drop-in section
        </label>
      </div>
      <div class="row">
        <label class="check-row">
          <input type="checkbox" id="require_code" ${c.require_code ? "checked" : ""}>
          Require PIN code to arm
        </label>
      </div>

      <h4>TTS Messages</h4>
      <div style="font-size:11px;color:var(--secondary-text-color,#94a3b8);margin-bottom:8px">Label | Message text</div>
      ${(c.tts_messages || []).map((m, i) => `
        <div class="msg-row">
          <input class="msg-label" data-idx="${i}" value="${m.label}" placeholder="Label">
          <input class="msg-text"  data-idx="${i}" value="${m.message}" placeholder="Message">
        </div>
      `).join("")}
    `;

    this.shadowRoot.getElementById("entity")
      .addEventListener("change", e => this._fire({ ...c, entity: e.target.value }));
    this.shadowRoot.getElementById("show_ha")
      .addEventListener("change", e => this._fire({ ...c, show_home_alone: e.target.checked }));
    this.shadowRoot.getElementById("show_tts")
      .addEventListener("change", e => this._fire({ ...c, show_tts: e.target.checked }));
    this.shadowRoot.getElementById("require_code")
      .addEventListener("change", e => this._fire({ ...c, require_code: e.target.checked }));

    const msgs = [...(c.tts_messages || [])];
    this.shadowRoot.querySelectorAll(".msg-label, .msg-text").forEach(inp => {
      inp.addEventListener("change", e => {
        const i   = parseInt(e.target.dataset.idx);
        const key = e.target.classList.contains("msg-label") ? "label" : "message";
        msgs[i] = { ...msgs[i], [key]: e.target.value };
        this._fire({ ...c, tts_messages: msgs });
      });
    });
  }
}

// ── Register ──────────────────────────────────────────────────────────────────

if (!customElements.get("secure-me-alarm-card")) {
  customElements.define("secure-me-alarm-card", SecureMeAlarmCard);
}
if (!customElements.get("secure-me-alarm-card-editor")) {
  customElements.define("secure-me-alarm-card-editor", SecureMeAlarmCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.find(c => c.type === "secure-me-alarm-card")) {
  window.customCards.push({
    type:        "secure-me-alarm-card",
    name:        "Secure Me Alarm Card",
    description: "Alarm arm/disarm, Home Alone mode, and TTS drop-in for Secure Me.",
    preview:     false,
  });
}
