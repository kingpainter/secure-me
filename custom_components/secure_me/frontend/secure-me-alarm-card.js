// secure-me-alarm-card.js
// Secure Me - Alarm control card: arm/disarm, Home Alone, TTS quick messages
// type: custom:secure-me-alarm-card
// VERSION = "1.3.0"
//
// Config:
//   entity:          alarm_control_panel.secure_me_alarm_system_alarm   (optional)
//   show_home_alone: true                            (show Home Alone arm button)
//   show_tts:        true                            (show TTS quick messages)
//   require_code:    true                            (PIN required for arm + disarm)
//   tts_messages:                                    (list of {label, message})
//     - label: Mad er klar
//       message: Hej, maden er klar.

function _smEsc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// SVG icons (no emoji, no raw non-ASCII)
const SMI = {
  shield:  '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  lock:    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  home:    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  moon:    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  plane:   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.28h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L7.91 9A16 16 0 0 0 15 16.09l1.08-1.08a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22.92 17z"/></svg>',
  users:   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  unlock:  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
  speaker: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
  close:   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  key:     '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7.5" cy="15.5" r="5.5"/><path d="M21 2l-9.6 9.6"/><path d="M15.5 7.5l3 3L22 7l-3-3"/></svg>',
};

class SecureMeAlarmCard extends HTMLElement {
  static getStubConfig() {
    return {
      entity: "alarm_control_panel.secure_me_alarm_system_alarm",
      show_home_alone: true,
      show_tts: true,
      require_code: true,
      tts_messages: [
        { label: "Mad er klar",   message: "Hej, maden er klar." },
        { label: "Ring til mig",  message: "Hej, ring venligst til mig nu. Hilsen Far" },
        { label: "Game pause",    message: "Det er pause tid. Ikke mere gaming" },
      ],
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass    = null;
    this._config  = {};
    this._shellBuilt = false;
    this._pinMode    = null;  // 'arm-away' | 'arm-home' | ... | 'disarm' | null
    this._pinValue   = "";
    this._pinError   = "";
    this._ttsOpen      = false;
    this._ttsSending   = null;   // label of in-progress TTS send
    this._ttsError     = null;   // error message from last TTS attempt
    this._dynamicMsgs  = null;   // v1.4.0: loaded from secure_me/get_home_alone_messages
    // Render cache keys -- sections only re-render when these change
    this._lastStatusState = null;
    this._lastPinState    = null;
    this._lastArmState    = null;
    this._lastTTSState    = null;
  }

  setConfig(config) {
    this._config = config || {};
  }

  set hass(h) {
    this._hass = h;
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
      this._loadDynamicMessages();
    } else {
      this._update();
    }
  }

  async _loadDynamicMessages() {
    try {
      const result = await this._hass.callWS({ type: 'secure_me/get_home_alone_messages' });
      if (result?.messages) {
        this._dynamicMsgs = result.messages;
        this._update(true);
      }
    } catch {
      this._dynamicMsgs = null;
    }
  }

  _entity()       { return this._config.entity || "alarm_control_panel.secure_me_alarm_system_alarm"; }
  _requireCode()  { return this._config.require_code !== false; }
  _showHA()       { return this._config.show_home_alone !== false; }
  _showTTS()      { return this._config.show_tts !== false; }
  _ttsMessages() {
    // v1.4.0: prefer dynamic messages from panel; fallback to yaml config
    return this._dynamicMsgs ?? this._config.tts_messages ?? [];
  }
  _state()        { return this._hass?.states?.[this._entity()]?.state ?? "unknown"; }
  _attr(a)        { return this._hass?.states?.[this._entity()]?.attributes?.[a]; }

  // -- Shell (built once) --------------------------------------------------
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
          --green:   #10b981;
          --orange:  #f59e0b;
          --red:     #ef4444;
          --purple:  #8b5cf6;
          --indigo:  #6366f1;
          font-family: 'DM Sans', var(--paper-font-body1_-_font-family, sans-serif);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }

        .card {
          background: var(--bg2);
          border-radius: 18px;
          border: 1px solid var(--div);
          padding: 16px;
          box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,.2));
          overflow: hidden;
        }

        /* Status hero */
        .status-hero {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 16px;
          border-radius: 14px;
          margin-bottom: 14px;
          transition: background .3s, border-color .3s;
          border: 1px solid var(--div);
        }
        .status-icon {
          width: 48px; height: 48px;
          border-radius: 14px;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
          transition: background .3s;
        }
        .status-info { flex: 1; }
        .status-label {
          font-size: 11px; font-weight: 700;
          text-transform: uppercase; letter-spacing: .08em;
          color: var(--sub);
        }
        .status-state {
          font-size: 20px; font-weight: 700;
          color: var(--text);
          line-height: 1.2;
        }
        .status-sub {
          font-size: 11px; color: var(--sub);
          margin-top: 2px;
        }

        /* Section label */
        .section-label {
          font-size: 10px; font-weight: 700;
          color: var(--sub);
          text-transform: uppercase; letter-spacing: .08em;
          margin: 0 0 8px 2px;
        }

        /* Arm buttons grid */
        .arm-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
          margin-bottom: 10px;
        }
        .arm-grid.with-ha { grid-template-columns: 1fr 1fr 1fr 1fr 1fr; }
        @media (max-width: 480px) {
          .arm-grid         { grid-template-columns: 1fr 1fr; }
          .arm-grid.with-ha { grid-template-columns: 1fr 1fr; }
        }
        .arm-btn {
          display: flex; flex-direction: column;
          align-items: center; justify-content: center;
          gap: 5px;
          padding: 12px 8px 10px;
          border-radius: 12px;
          border: 1px solid var(--div);
          background: var(--bg3);
          cursor: pointer;
          transition: background .15s, border-color .15s, opacity .15s;
          color: var(--sub);
          font-size: 11px; font-weight: 600;
          text-align: center;
          user-select: none;
        }
        .arm-btn:active { opacity: .7; }
        .arm-btn:hover  { border-color: rgba(148,163,184,.3); color: var(--text); }
        .arm-btn.active {
          border-color: currentColor;
        }
        .arm-btn .btn-icon {
          width: 32px; height: 32px;
          border-radius: 9px;
          display: flex; align-items: center; justify-content: center;
        }

        /* Disarm button */
        .disarm-btn {
          width: 100%;
          padding: 12px;
          border-radius: 12px;
          border: 1px solid rgba(239,68,68,.35);
          background: rgba(239,68,68,.08);
          color: #ef4444;
          font-size: 13px; font-weight: 700;
          cursor: pointer;
          transition: background .15s, opacity .15s;
          margin-top: 10px;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          user-select: none;
        }
        .disarm-btn:active { opacity: .7; }
        .disarm-btn:hover  { background: rgba(239,68,68,.14); }

        /* Divider */
        .divider { height: 1px; background: var(--div); margin: 14px 0; }

        /* PIN pad */
        .pin-overlay {
          background: var(--bg2);
          border-radius: 14px;
          border: 1px solid var(--div);
          padding: 16px;
          margin-bottom: 14px;
        }
        .pin-title {
          font-size: 13px; font-weight: 600; color: var(--text);
          margin-bottom: 12px; text-align: center;
        }
        .pin-display {
          display: flex; justify-content: center; gap: 10px;
          margin-bottom: 14px;
        }
        .pin-dot {
          width: 14px; height: 14px;
          border-radius: 50%;
          border: 2px solid var(--sub);
          background: transparent;
          transition: background .15s, border-color .15s;
        }
        .pin-dot.filled { background: var(--accent); border-color: var(--accent); }
        .pin-error {
          text-align: center; font-size: 12px;
          color: var(--red); margin-bottom: 10px; min-height: 18px;
        }
        .pin-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }
        .pin-key {
          padding: 14px 8px;
          border-radius: 10px;
          background: var(--bg3);
          border: 1px solid var(--div);
          font-size: 18px; font-weight: 600;
          color: var(--text);
          cursor: pointer;
          text-align: center;
          user-select: none;
          transition: background .1s, opacity .1s;
        }
        .pin-key:active { opacity: .6; }
        .pin-key.del { font-size: 14px; color: var(--sub); }
        .pin-key.ok  {
          background: var(--accent);
          border-color: var(--accent);
          color: #fff;
        }
        .pin-cancel {
          width: 100%; margin-top: 8px;
          padding: 10px;
          border-radius: 10px;
          border: 1px solid var(--div);
          background: transparent;
          color: var(--sub);
          font-size: 13px; cursor: pointer;
          transition: background .15s;
        }
        .pin-cancel:hover { background: var(--bg3); }

        /* TTS section */
        .tts-btn {
          width: 100%;
          padding: 11px 14px;
          border-radius: 12px;
          border: 1px solid var(--div);
          background: var(--bg3);
          color: var(--sub);
          font-size: 13px; font-weight: 600;
          cursor: pointer;
          display: flex; align-items: center; justify-content: space-between;
          transition: background .15s;
          user-select: none;
          margin-bottom: 14px;
        }
        .tts-btn:hover { background: rgba(255,255,255,.05); }
        .tts-btn svg   { color: var(--sub); }

        .tts-list { margin-bottom: 4px; }
        .tts-msg-btn {
          width: 100%;
          display: flex; align-items: center; justify-content: space-between;
          padding: 10px 12px;
          border-radius: 10px;
          border: 1px solid var(--div);
          background: var(--bg3);
          color: var(--text);
          font-size: 13px; font-weight: 500;
          cursor: pointer;
          margin-bottom: 6px;
          transition: background .15s, opacity .15s;
          user-select: none;
        }
        .tts-msg-btn:last-child { margin-bottom: 0; }
        .tts-msg-btn:hover   { background: rgba(255,255,255,.05); }
        .tts-msg-btn:active  { opacity: .7; }
        .tts-msg-btn.sending { opacity: .5; pointer-events: none; }
        .tts-msg-icon { color: #14b8a6; flex-shrink: 0; }

        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
      </style>
      <div class="card">
        <div id="status-section"></div>
        <div id="pin-section"></div>
        <div id="arm-section"></div>
        <div id="tts-section"></div>
      </div>`;

    // Event delegation - all interaction through data-sm attributes
    this.shadowRoot.querySelector(".card").addEventListener("click", (e) => {
      this._handleClick(e);
    });

    this._update(true);
  }

  // -- Update --------------------------------------------------------------
  // Each section only re-renders when its relevant state actually changes.
  // This prevents innerHTML replacement from interrupting CSS hover/transition
  // and causing visible blink on every hass tick (~1/sec).
  _update(force = false) {
    const root = this.shadowRoot;
    if (!root || !this._hass) return;

    const ss = root.getElementById("status-section");
    const ps = root.getElementById("pin-section");
    const as = root.getElementById("arm-section");
    const ts = root.getElementById("tts-section");

    // Status: re-render when alarm state or countdown changes
    const statusState = `${this._state()}:${this._attr("countdown") ?? 0}`;
    if (ss && (force || statusState !== this._lastStatusState)) {
      this._lastStatusState = statusState;
      ss.innerHTML = this._renderStatus();
    }

    // PIN: re-render only when pin mode, value or error changes
    const pinState = `${this._pinMode}:${this._pinValue}:${this._pinError}`;
    if (ps && (force || pinState !== this._lastPinState)) {
      this._lastPinState = pinState;
      ps.innerHTML = this._pinMode ? this._renderPin() : "";
    }

    // Arm buttons: re-render only when alarm state or pin-mode changes
    const armState = `${this._state()}:${!!this._pinMode}`;
    if (as && (force || armState !== this._lastArmState)) {
      this._lastArmState = armState;
      as.innerHTML = !this._pinMode ? this._renderArmButtons() : "";
    }

    // TTS: re-render only when open/sending/error state changes
    const ttsState = `${this._ttsOpen}:${this._ttsSending}:${this._ttsError}`;
    if (ts && (force || ttsState !== this._lastTTSState)) {
      this._lastTTSState = ttsState;
      ts.innerHTML = (!this._pinMode && this._showTTS()) ? this._renderTTS() : "";
    }
  }

  // -- Renders -------------------------------------------------------------
  _renderStatus() {
    const state = this._state();
    const armedBy = this._attr("changed_by") || "";
    const countdown = this._attr("countdown") || 0;

    const CFG = {
      disarmed:         { color: "#10b981", bg: "rgba(16,185,129,.10)", label: "Deaktiveret" },
      armed_away:       { color: "#ef4444", bg: "rgba(239,68,68,.12)",  label: "Aktiveret - Vaek" },
      armed_home:       { color: "#f59e0b", bg: "rgba(245,158,11,.12)", label: "Aktiveret - Hjemme" },
      armed_night:      { color: "#6366f1", bg: "rgba(99,102,241,.12)", label: "Aktiveret - Nat" },
      armed_vacation:   { color: "#8b5cf6", bg: "rgba(139,92,246,.12)", label: "Aktiveret - Ferie" },
      armed_home_alone: { color: "#10b981", bg: "rgba(16,185,129,.12)", label: "Hjemme Alene" },
      arming:           { color: "#f59e0b", bg: "rgba(245,158,11,.12)", label: `Aktiverer... ${countdown > 0 ? countdown + "s" : ""}` },
      pending:          { color: "#f59e0b", bg: "rgba(245,158,11,.18)", label: `Indgang... ${countdown > 0 ? countdown + "s" : ""}` },
      triggered:        { color: "#ef4444", bg: "rgba(239,68,68,.20)",  label: "ALARM UDLOEST!" },
    };
    const cfg = CFG[state] || { color: "#64748b", bg: "var(--bg3)", label: state === "unknown" ? "Henter status..." : _smEsc(state) };
    const pulse = ["arming","pending","triggered"].includes(state)
      ? "animation:pulse 1s infinite;" : "";

    return `
      <div class="status-hero" style="background:${cfg.bg};border-color:${cfg.color}44">
        <div class="status-icon" style="background:${cfg.color}22;${pulse};color:${cfg.color}">
          ${SMI.shield}
        </div>
        <div class="status-info">
          <div class="status-label">Alarm status</div>
          <div class="status-state" style="color:${cfg.color}">${cfg.label}</div>
          ${armedBy ? `<div class="status-sub">Af ${_smEsc(armedBy)}</div>` : ""}
        </div>
      </div>`;
  }

  _renderArmButtons() {
    const state = this._state();
    const isArmed = ["armed_away","armed_home","armed_night",
                     "armed_vacation","armed_home_alone"].includes(state);
    const showHA = this._showHA();

    const MODES = [
      { key: "arm_away",       state: "armed_away",       label: "Vaek",      color: "#ef4444", icon: SMI.plane },
      { key: "arm_home",       state: "armed_home",       label: "Hjemme",    color: "#f59e0b", icon: SMI.home  },
      { key: "arm_night",      state: "armed_night",      label: "Nat",       color: "#6366f1", icon: SMI.moon  },
      { key: "arm_vacation",   state: "armed_vacation",   label: "Ferie",     color: "#8b5cf6", icon: SMI.plane },
      ...(showHA ? [{ key: "arm_home_alone", state: "armed_home_alone", label: "Alene", color: "#10b981", icon: SMI.users }] : []),
    ];

    const cols = showHA ? "with-ha" : "";

    const buttons = MODES.map(m => {
      const active = state === m.state;
      return `
        <button class="arm-btn ${active ? "active" : ""}" data-sm-arm="${m.key}"
                style="${active ? `color:${m.color}` : ""}" title="${m.label} mode">
          <div class="btn-icon" style="background:${m.color}${active ? "33" : "18"};color:${m.color}">
            ${m.icon}
          </div>
          ${m.label}
        </button>`;
    }).join("");

    const disarmBtn = isArmed ? `
      <button class="disarm-btn" data-sm-arm="disarm">
        ${SMI.unlock} Deaktiver alarm
      </button>` : "";

    return `
      <div class="section-label">Tilkoblings-modes</div>
      <div class="arm-grid ${cols}">${buttons}</div>
      ${disarmBtn}`;
  }

  _renderPin() {
    const action = this._pinMode || "";
    const title = action === "disarm"
      ? "Indtast kode for at deaktivere"
      : "Indtast kode for at tilkoble";
    const len = this._pinValue.length;
    const dots = [0,1,2,3].map(i =>
      `<div class="pin-dot ${i < len ? "filled" : ""}"></div>`
    ).join("");

    return `
      <div class="pin-overlay">
        <div class="pin-title">${SMI.key} ${title}</div>
        <div class="pin-display">${dots}</div>
        <div class="pin-error">${_smEsc(this._pinError)}</div>
        <div class="pin-grid">
          ${[1,2,3,4,5,6,7,8,9].map(n =>
            `<button class="pin-key" data-sm-pin="${n}">${n}</button>`
          ).join("")}
          <button class="pin-key del" data-sm-pin="del">&#9003;</button>
          <button class="pin-key" data-sm-pin="0">0</button>
          <button class="pin-key ok" data-sm-pin="ok">OK</button>
        </div>
        <button class="pin-cancel" data-sm-pin="cancel">Annuller</button>
      </div>`;
  }

  _renderTTS() {
    const msgs = this._ttsMessages();
    if (!msgs.length) return "";
    const open = this._ttsOpen;

    // Use index-based lookup to avoid HTML attribute escaping issues with
    // message content (quotes, special chars break inline data attributes).
    const msgButtons = open ? msgs.map((m, i) => `
      <button class="tts-msg-btn ${this._ttsSending === m.label ? "sending" : ""}"
              data-sm-tts-idx="${i}">
        <span>${_smEsc(m.label)}</span>
        <span class="tts-msg-icon">${SMI.speaker}</span>
      </button>`).join("") : "";

    return `
      <div class="divider"></div>
      <div class="section-label">TTS hurtigbeskeder</div>
      <button class="tts-btn" data-sm-tts-toggle="1">
        <span style="display:flex;align-items:center;gap:8px;color:var(--text)">
          ${SMI.speaker} Hurtigbeskeder
        </span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
          ${open
            ? '<polyline points="18 15 12 9 6 15"/>'
            : '<polyline points="6 9 12 15 18 9"/>'}
        </svg>
      </button>
      ${open ? `<div class="tts-list">${msgButtons}</div>` : ""}
      ${this._ttsError ? `<div style="font-size:11px;color:#ef4444;margin-top:6px;padding:0 2px">${_smEsc(this._ttsError)}</div>` : ""}`;
  }

  // -- Click handler --------------------------------------------------------
  _handleClick(e) {
    // TTS toggle
    const toggle = e.target.closest("[data-sm-tts-toggle]");
    if (toggle) {
      this._ttsOpen = !this._ttsOpen;
      this._update(true);
      return;
    }

    // TTS message send (index-based to avoid attribute escaping issues)
    const ttsBtn = e.target.closest("[data-sm-tts-idx]");
    if (ttsBtn) {
      const idx = parseInt(ttsBtn.dataset.smTtsIdx, 10);
      const msgs = this._ttsMessages();
      if (msgs[idx]) this._sendTTS(msgs[idx].label, msgs[idx].message, msgs[idx].speakers);
      return;
    }

    // PIN key
    const pinKey = e.target.closest("[data-sm-pin]");
    if (pinKey) {
      this._handlePin(pinKey.dataset.smPin);
      return;
    }

    // Arm/disarm button
    const armBtn = e.target.closest("[data-sm-arm]");
    if (armBtn) {
      this._handleArm(armBtn.dataset.smArm);
      return;
    }
  }

  // -- Arm logic ---------------------------------------------------------
  _handleArm(action) {
    if (this._requireCode()) {
      this._pinMode  = action;
      this._pinValue = "";
      this._pinError = "";
      this._update();
    } else {
      this._callArm(action, null);
    }
  }

  async _callArm(action, code) {
    const entity = this._entity();

    // Standard HA services for common modes.
    // Custom modes (vacation, home_alone) use Secure Me WS API
    // so code validation goes through our bcrypt authenticate_user().
    const haServiceMap = {
      "arm_away":  "alarm_arm_away",
      "arm_home":  "alarm_arm_home",
      "arm_night": "alarm_arm_night",
      "disarm":    "alarm_disarm",
    };

    const smWSTypes = {
      "arm_vacation":   "secure_me/arm_vacation",
      "arm_home_alone": "secure_me/arm_home_alone",
    };

    try {
      if (haServiceMap[action]) {
        const data = { entity_id: entity };
        if (code) data.code = code;
        await this._hass.callService("alarm_control_panel", haServiceMap[action], data);
      } else if (smWSTypes[action]) {
        const ws = { type: smWSTypes[action] };
        if (code) ws.code = code;
        await this._hass.callWS(ws);
      } else {
        return;
      }
      this._pinMode  = null;
      this._pinValue = "";
      this._pinError = "";
    } catch (err) {
      const entityMissing = this._state() === "unknown";
      this._pinError = entityMissing
        ? "Alarm ikke fundet. Genstart HA."
        : "Forkert kode eller fejl";
    }
    this._update();
  }

    // -- PIN logic --------------------------------------------------------
  _handlePin(key) {
    if (key === "cancel") {
      this._pinMode  = null;
      this._pinValue = "";
      this._pinError = "";
      this._update();
      return;
    }
    if (key === "del") {
      this._pinValue = this._pinValue.slice(0, -1);
      this._pinError = "";
      this._update();
      return;
    }
    if (key === "ok") {
      if (this._pinValue.length < 1) {
        this._pinError = "Indtast kode";
        this._update();
        return;
      }
      this._callArm(this._pinMode, this._pinValue);
      return;
    }
    if (this._pinValue.length < 8) {
      this._pinValue += key;
      this._pinError = "";
      this._update();
    }
  }

  // -- TTS logic --------------------------------------------------------
  async _sendTTS(label, message, speakers) {
    if (this._ttsSending) return;
    this._ttsSending = label;
    this._ttsError = null;
    this._update(true);
    try {
      // Route via Secure Me WebSocket -- handles media_player selection internally
      await this._hass.callWS({
        type: "secure_me/test_tts",
        message: message,
        ...(speakers?.length ? { speaker_ids: speakers } : {}),
      });
    } catch (err) {
      // Do NOT fall through to tts/speak -- it requires media_player_entity_id
      // which the card does not have. Show a UI error instead.
      this._ttsError = "TTS fejlede. Tjek at Secure Me er aktiv og HA er restartet.";
    }
    this._ttsSending = null;
    this._update(true);
  }

  getCardSize() { return 4; }
}

if (!customElements.get("secure-me-alarm-card")) {
  customElements.define("secure-me-alarm-card", SecureMeAlarmCard);
}
window.customCards = window.customCards || [];
if (!window.customCards.find(c => c.type === "secure-me-alarm-card")) {
  window.customCards.push({
    type: "secure-me-alarm-card",
    name: "Secure Me - Alarm Control",
    description: "Tilkob/afkob alarm, Home Alone mode og TTS hurtigbeskeder.",
    preview: true,
  });
}
