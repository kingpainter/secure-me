// secure-me-alarm-card.js
// Secure Me — Alarm control card
// VERSION = "1.4.0"

function _smEsc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

const SMI = {
  shield:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  lock:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  unlock:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
  home:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  moon:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
  plane:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.28h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L7.91 9A16 16 0 0 0 15 16.09l1.08-1.08a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22.92 17z"/></svg>',
  users:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  speaker: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
  key:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>',
  back:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
};

const STATE_CFG = {
  disarmed:         { label: "Deaktiveret",       color: "#10b981", glow: "rgba(16,185,129,0.4)",   pulse: false },
  arming:           { label: "Tilkobles",          color: "#f59e0b", glow: "rgba(245,158,11,0.4)",   pulse: true  },
  armed_away:       { label: "Tilkoblet — Borte",  color: "#ef4444", glow: "rgba(239,68,68,0.45)",   pulse: false },
  armed_home:       { label: "Tilkoblet — Hjemme", color: "#3b82f6", glow: "rgba(59,130,246,0.4)",   pulse: false },
  armed_night:      { label: "Tilkoblet — Nat",    color: "#6366f1", glow: "rgba(99,102,241,0.4)",   pulse: false },
  armed_vacation:   { label: "Tilkoblet — Ferie",  color: "#8b5cf6", glow: "rgba(139,92,246,0.4)",   pulse: false },
  armed_home_alone: { label: "Tilkoblet — Alene",  color: "#10b981", glow: "rgba(16,185,129,0.4)",   pulse: false },
  pending:          { label: "Afventer indgang",   color: "#f97316", glow: "rgba(249,115,22,0.45)",  pulse: true  },
  triggered:        { label: "ALARM UDLOST",       color: "#ef4444", glow: "rgba(239,68,68,0.6)",    pulse: true  },
  unknown:          { label: "Henter status...",   color: "#64748b", glow: "rgba(100,116,139,0.2)",  pulse: false },
};

class SecureMeAlarmCard extends HTMLElement {
  static getStubConfig() {
    return {
      entity: "alarm_control_panel.secure_me_alarm_system_alarm",
      show_home_alone: true,
      show_tts: true,
      require_code: true,
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass           = null;
    this._config         = {};
    this._shellBuilt     = false;
    this._pinValue       = "";
    this._pinMode        = null;
    this._pinError       = "";
    this._ttsSending     = null;
    this._ttsError       = null;
    this._dynamicMsgs    = null;
    this._locks          = [];
    this._localCountdown = null;
    this._countdownTimer = null;
  }

  setConfig(config) { this._config = config; }

  set hass(h) {
    this._hass = h;
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
      this._loadDynamic();
    } else {
      this._update();
    }
    const state = this._state();
    const cd = this._attr("countdown");
    if ((state === "arming" || state === "pending") && cd != null) {
      if (this._localCountdown === null || Math.abs(this._localCountdown - cd) > 2) this._localCountdown = cd;
      if (!this._countdownTimer) {
        this._countdownTimer = setInterval(() => {
          if (this._localCountdown > 0) { this._localCountdown--; this._update(true); }
        }, 1000);
      }
    } else {
      if (this._countdownTimer) { clearInterval(this._countdownTimer); this._countdownTimer = null; }
      this._localCountdown = null;
    }
  }

  async _loadDynamic() {
    try {
      const [msgRes, modRes] = await Promise.all([
        this._hass.callWS({ type: "secure_me/get_home_alone_messages" }),
        this._hass.callWS({ type: "secure_me/get_modules" }),
      ]);
      this._dynamicMsgs = msgRes?.messages ?? null;
      const lockMod = modRes?.modules?.lock;
      if (lockMod?.enabled && lockMod.locks?.length) {
        this._locks = lockMod.locks.map(l => ({
          entity_id: typeof l === "string" ? l : l.entity_id,
          name: typeof l === "string"
            ? l.split(".")[1].replace(/_/g, " ")
            : (l.name || l.entity_id.split(".")[1].replace(/_/g, " ")),
        }));
      } else {
        this._locks = [];
      }
      this._update(true);
    } catch {
      this._dynamicMsgs = null;
      this._locks = [];
    }
  }

  _entity()      { return this._config.entity || "alarm_control_panel.secure_me_alarm_system_alarm"; }
  _requireCode() { return this._config.require_code !== false; }
  _showHA()      { return this._config.show_home_alone !== false; }
  _showTTS()     { return this._config.show_tts !== false; }
  _ttsMessages() { return this._dynamicMsgs ?? this._config.tts_messages ?? []; }
  _state()       { return this._hass?.states?.[this._entity()]?.state ?? "unknown"; }
  _attr(a)       { return this._hass?.states?.[this._entity()]?.attributes?.[a]; }

  _buildShell() {
    this.shadowRoot.innerHTML = `
      <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :host { display: block; }

        .card {
          background: var(--ha-card-background, #111827);
          border-radius: 22px;
          overflow: hidden;
          font-family: 'DM Sans', var(--primary-font-family, sans-serif);
          color: var(--primary-text-color, #f1f5f9);
          box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        }

        /* ── Header ── */
        .header {
          position: relative;
          padding: 22px 22px 20px;
          overflow: hidden;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .header-bg {
          position: absolute;
          inset: 0;
          opacity: 0;
          transition: opacity 0.5s ease;
          pointer-events: none;
        }
        .header-content {
          position: relative;
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .shield-wrap {
          position: relative;
          flex-shrink: 0;
        }
        .shield-ring {
          width: 52px; height: 52px;
          border-radius: 16px;
          display: flex; align-items: center; justify-content: center;
          transition: background 0.4s, box-shadow 0.4s;
        }
        .shield-ring svg { width: 26px; height: 26px; }
        .status-meta { flex: 1; min-width: 0; }
        .status-eyebrow {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          opacity: 0.45;
          margin-bottom: 4px;
        }
        .status-text {
          font-size: 19px;
          font-weight: 700;
          line-height: 1.15;
          transition: color 0.35s;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .countdown-badge {
          display: inline-flex;
          align-items: center;
          font-family: 'DM Mono', monospace;
          font-size: 13px;
          font-weight: 500;
          padding: 3px 10px;
          border-radius: 20px;
          margin-left: 10px;
          background: rgba(255,255,255,0.1);
          vertical-align: middle;
          letter-spacing: 0.04em;
        }

        /* ── Body ── */
        .body { padding: 18px; display: flex; flex-direction: column; gap: 16px; }

        /* ── Section label ── */
        .sec-label {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: rgba(255,255,255,0.3);
          margin-bottom: 8px;
        }

        /* ── Arm grid ── */
        .arm-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }
        .arm-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 14px 6px;
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.07);
          background: rgba(255,255,255,0.04);
          cursor: pointer;
          font-family: inherit;
          font-size: 12px;
          font-weight: 600;
          color: rgba(255,255,255,0.55);
          transition: all 0.18s;
          letter-spacing: 0.01em;
        }
        .arm-btn-icon {
          width: 32px; height: 32px;
          border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.18s;
          background: rgba(255,255,255,0.06);
        }
        .arm-btn-icon svg { width: 17px; height: 17px; }
        .arm-btn:hover { background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.8); }
        .arm-btn:active { transform: scale(0.95); }
        .arm-btn.active {
          border-color: var(--c);
          background: color-mix(in srgb, var(--c) 12%, transparent);
          color: var(--c);
        }
        .arm-btn.active .arm-btn-icon {
          background: color-mix(in srgb, var(--c) 18%, transparent);
          color: var(--c);
        }
        .arm-btn:not(.active) .arm-btn-icon { color: rgba(255,255,255,0.4); }

        /* ── Disarm button ── */
        .disarm-btn {
          width: 100%;
          display: flex; align-items: center; justify-content: center;
          gap: 10px;
          padding: 16px;
          border-radius: 16px;
          border: 1px solid rgba(239,68,68,0.3);
          background: rgba(239,68,68,0.1);
          cursor: pointer;
          font-family: inherit;
          font-size: 15px;
          font-weight: 700;
          color: #ef4444;
          letter-spacing: 0.02em;
          transition: all 0.15s;
        }
        .disarm-btn svg { width: 18px; height: 18px; }
        .disarm-btn:hover { background: rgba(239,68,68,0.16); }
        .disarm-btn:active { transform: scale(0.99); }

        /* ── Lock section ── */
        .lock-row {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 14px;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 14px;
        }
        .lock-icon-wrap {
          width: 36px; height: 36px;
          border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
          transition: all 0.25s;
        }
        .lock-icon-wrap svg { width: 16px; height: 16px; }
        .lock-details { flex: 1; min-width: 0; }
        .lock-name {
          font-size: 13px;
          font-weight: 600;
          text-transform: capitalize;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .lock-state-label {
          font-size: 11px;
          margin-top: 1px;
          font-weight: 500;
        }
        .lock-btns { display: flex; gap: 6px; flex-shrink: 0; }
        .lock-action-btn {
          display: flex; align-items: center; gap: 5px;
          padding: 7px 12px;
          border-radius: 10px;
          border: 1px solid transparent;
          cursor: pointer;
          font-family: inherit;
          font-size: 12px;
          font-weight: 600;
          transition: all 0.15s;
          white-space: nowrap;
        }
        .lock-action-btn svg { width: 13px; height: 13px; }
        .lock-action-btn:active { transform: scale(0.95); }
        .lock-action-btn:disabled { opacity: 0.25; cursor: default; pointer-events: none; }
        .btn-open {
          background: rgba(16,185,129,0.1);
          border-color: rgba(16,185,129,0.3);
          color: #10b981;
        }
        .btn-open:hover { background: rgba(16,185,129,0.18); }
        .btn-close {
          background: rgba(239,68,68,0.08);
          border-color: rgba(239,68,68,0.25);
          color: #f87171;
        }
        .btn-close:hover { background: rgba(239,68,68,0.15); }

        /* ── TTS section ── */
        .tts-list { display: flex; flex-direction: column; gap: 7px; }
        .tts-btn {
          display: flex; align-items: center; justify-content: space-between;
          padding: 12px 15px;
          border-radius: 13px;
          border: 1px solid rgba(139,92,246,0.18);
          background: rgba(139,92,246,0.07);
          cursor: pointer;
          font-family: inherit;
          font-size: 13px;
          font-weight: 500;
          color: #c4b5fd;
          transition: all 0.15s;
        }
        .tts-btn svg { width: 15px; height: 15px; opacity: 0.65; flex-shrink: 0; }
        .tts-btn:hover { background: rgba(139,92,246,0.14); }
        .tts-btn:active { transform: scale(0.98); }
        .tts-btn.sending { opacity: 0.45; pointer-events: none; }
        .tts-err { font-size: 11px; color: #f87171; margin-top: 4px; padding: 0 2px; }

        /* ── PIN pad ── */
        .pin-wrap { display: flex; flex-direction: column; gap: 12px; }
        .pin-title {
          display: flex; align-items: center; justify-content: center;
          gap: 8px; font-size: 13px; font-weight: 600;
          color: rgba(255,255,255,0.5);
        }
        .pin-title svg { width: 15px; height: 15px; }
        .pin-dots { display: flex; gap: 12px; justify-content: center; }
        .pin-dot {
          width: 13px; height: 13px; border-radius: 50%;
          background: rgba(255,255,255,0.12);
          transition: background 0.15s, transform 0.12s;
        }
        .pin-dot.filled { background: #ef4444; transform: scale(1.15); }
        .pin-err { text-align: center; font-size: 12px; color: #f87171; min-height: 16px; }
        .pin-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        .pin-key {
          padding: 15px 8px;
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 14px;
          cursor: pointer;
          font-size: 19px; font-weight: 600; font-family: inherit;
          background: rgba(255,255,255,0.04);
          color: var(--primary-text-color, #f1f5f9);
          transition: all 0.1s;
        }
        .pin-key:active { background: rgba(255,255,255,0.1); transform: scale(0.94); }
        .pin-key.ok {
          background: #ef4444; color: #fff;
          border-color: #ef4444; font-size: 13px; font-weight: 700;
        }
        .pin-key.ok:active { background: #dc2626; }
        .pin-cancel {
          width: 100%; padding: 12px;
          border: 1px solid rgba(255,255,255,0.07);
          border-radius: 13px; cursor: pointer;
          font-size: 13px; font-family: inherit;
          background: transparent;
          color: rgba(255,255,255,0.4);
          transition: background 0.15s;
        }
        .pin-cancel:hover { background: rgba(255,255,255,0.04); }

        /* ── Animations ── */
        @keyframes sm-pulse-ring {
          0%   { box-shadow: 0 0 0 0 var(--glow); }
          70%  { box-shadow: 0 0 0 10px transparent; }
          100% { box-shadow: 0 0 0 0 transparent; }
        }
        @keyframes sm-blink {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.6; }
        }
        .pulse-ring { animation: sm-pulse-ring 1.4s ease-out infinite; }
        .blink { animation: sm-blink 1s ease-in-out infinite; }
      </style>
      <div class="card">
        <div class="header">
          <div class="header-bg" id="sm-hbg"></div>
          <div class="header-content">
            <div class="shield-wrap">
              <div class="shield-ring" id="sm-shield">${SMI.shield}</div>
            </div>
            <div class="status-meta">
              <div class="status-eyebrow">Secure Me</div>
              <div class="status-text" id="sm-stxt">Henter...</div>
            </div>
          </div>
        </div>
        <div class="body" id="sm-body"></div>
      </div>`;

    this.shadowRoot.addEventListener("click", e => this._handleClick(e));
    this._update(true);
  }

  _update(force = false) {
    const state   = this._state();
    const pinMode = this._pinMode;
    const lockKey = this._locks.map(l => this._hass?.states?.[l.entity_id]?.state || "?").join(",");
    const key = `${state}:${pinMode}:${this._pinValue.length}:${this._pinError}:${this._ttsSending}:${this._ttsError}:${this._localCountdown}:${lockKey}`;
    if (!force && this._lastKey === key) return;
    this._lastKey = key;

    const root = this.shadowRoot;
    const cfg  = STATE_CFG[state] || STATE_CFG.unknown;

    // Header
    const hbg    = root.getElementById("sm-hbg");
    const shield = root.getElementById("sm-shield");
    const stxt   = root.getElementById("sm-stxt");
    if (hbg) {
      hbg.style.background = `radial-gradient(ellipse at 0% 50%, ${cfg.glow} 0%, transparent 70%)`;
      hbg.style.opacity = "1";
    }
    if (shield) {
      shield.style.background = cfg.color + "22";
      shield.style.color = cfg.color;
      shield.style.boxShadow = `0 0 18px ${cfg.glow}`;
      shield.style.setProperty("--glow", cfg.glow);
      shield.className = "shield-ring" + (cfg.pulse ? " pulse-ring" : "");
    }
    if (stxt) {
      let cdBadge = "";
      if ((state === "arming" || state === "pending") && this._localCountdown != null) {
        cdBadge = `<span class="countdown-badge">${this._localCountdown}s</span>`;
      }
      stxt.style.color = cfg.color;
      stxt.className = "status-text" + (state === "triggered" ? " blink" : "");
      stxt.innerHTML = _smEsc(cfg.label) + cdBadge;
    }

    // Body
    const body = root.getElementById("sm-body");
    if (body) body.innerHTML = pinMode ? this._renderPin() : this._renderBody(state);
  }

  _renderBody(state) {
    const armed  = !["disarmed","unknown","arming"].includes(state);
    const msgs   = this._showTTS() ? this._ttsMessages() : [];
    const locks  = this._locks;
    const showHA = this._showHA();

    return [
      armed ? this._renderDisarm() : this._renderArmGrid(state, showHA),
      locks.length  ? this._renderLocks()      : "",
      msgs.length   ? this._renderTTS(msgs)    : "",
    ].join("");
  }

  _renderDisarm() {
    return `<div>
      <button class="disarm-btn" data-sm-arm="disarm">
        ${SMI.unlock} Deaktiver alarm
      </button>
    </div>`;
  }

  _renderArmGrid(state, showHA) {
    const modes = [
      { action: "arm_away",       icon: SMI.lock,  label: "Borte",  c: "#ef4444" },
      { action: "arm_home",       icon: SMI.home,  label: "Hjemme", c: "#3b82f6" },
      { action: "arm_night",      icon: SMI.moon,  label: "Nat",    c: "#6366f1" },
      { action: "arm_vacation",   icon: SMI.plane, label: "Ferie",  c: "#8b5cf6" },
    ];
    if (showHA) modes.push({ action: "arm_home_alone", icon: SMI.users, label: "Alene", c: "#10b981" });

    const btns = modes.map(m => {
      const active = state === `armed_${m.action.replace("arm_","")}`;
      return `<button class="arm-btn${active?" active":""}" data-sm-arm="${m.action}" style="--c:${m.c}">
        <div class="arm-btn-icon" style="${active?`color:${m.c}`:""}">
          ${m.icon}
        </div>
        <span>${_smEsc(m.label)}</span>
      </button>`;
    }).join("");

    return `<div>
      <div class="sec-label">Tilkobl alarm</div>
      <div class="arm-grid">${btns}</div>
    </div>`;
  }

  _renderLocks() {
    const rows = this._locks.map(l => {
      const st       = this._hass?.states?.[l.entity_id];
      const isLocked = st?.state === "locked";
      const unavail  = !st || ["unavailable","unknown"].includes(st.state);
      const c        = unavail ? "#475569" : isLocked ? "#ef4444" : "#10b981";
      const bg       = unavail ? "rgba(71,85,105,0.12)" : isLocked ? "rgba(239,68,68,0.1)" : "rgba(16,185,129,0.1)";
      const stLabel  = unavail ? "Utilgængelig" : isLocked ? "Låst" : "Ulåst";

      return `<div class="lock-row">
        <div class="lock-icon-wrap" style="background:${bg};color:${c}">
          ${isLocked ? SMI.lock : SMI.unlock}
        </div>
        <div class="lock-details">
          <div class="lock-name">${_smEsc(l.name)}</div>
          <div class="lock-state-label" style="color:${c}">${stLabel}</div>
        </div>
        <div class="lock-btns">
          <button class="lock-action-btn btn-open"
                  data-sm-lock="${l.entity_id}" data-sm-lock-action="unlock"
                  ${unavail || !isLocked ? "disabled" : ""}>
            ${SMI.unlock} Lås op
          </button>
          <button class="lock-action-btn btn-close"
                  data-sm-lock="${l.entity_id}" data-sm-lock-action="lock"
                  ${unavail || isLocked ? "disabled" : ""}>
            ${SMI.lock} Lås
          </button>
        </div>
      </div>`;
    }).join("");

    return `<div>
      <div class="sec-label">Låse</div>
      ${rows}
    </div>`;
  }

  _renderTTS(msgs) {
    const btns = msgs.map((m, i) => `
      <button class="tts-btn${this._ttsSending === m.label ? " sending" : ""}" data-sm-tts-idx="${i}">
        <span>${_smEsc(m.label)}</span>
        ${SMI.speaker}
      </button>`).join("");

    return `<div>
      <div class="sec-label">Hurtigbeskeder</div>
      <div class="tts-list">${btns}</div>
      ${this._ttsError ? `<div class="tts-err">${_smEsc(this._ttsError)}</div>` : ""}
    </div>`;
  }

  _renderPin() {
    const dots = [0,1,2,3].map(i =>
      `<div class="pin-dot${i < this._pinValue.length ? " filled" : ""}"></div>`
    ).join("");
    const modeLabel = {
      disarm: "Kode for at deaktivere",
      arm_away: "Kode for at tilkoble",
      arm_home: "Kode for at tilkoble",
      arm_night: "Kode for at tilkoble",
      arm_vacation: "Kode for at tilkoble",
      arm_home_alone: "Kode for at tilkoble",
    }[this._pinMode] || "Indtast kode";

    return `<div class="pin-wrap">
      <div class="pin-title">${SMI.key} ${_smEsc(modeLabel)}</div>
      <div class="pin-dots">${dots}</div>
      <div class="pin-err">${_smEsc(this._pinError)}</div>
      <div class="pin-grid">
        ${[1,2,3,4,5,6,7,8,9].map(n =>
          `<button class="pin-key" data-sm-pin="${n}">${n}</button>`
        ).join("")}
        <button class="pin-key" data-sm-pin="back">${SMI.back}</button>
        <button class="pin-key" data-sm-pin="0">0</button>
        <button class="pin-key ok" data-sm-pin="ok">OK</button>
      </div>
      <button class="pin-cancel" data-sm-pin="cancel">Annuller</button>
    </div>`;
  }

  // ── Click handler ──────────────────────────────────────────────────────────
  _handleClick(e) {
    const lockBtn = e.target.closest("[data-sm-lock]");
    if (lockBtn && !lockBtn.disabled) {
      this._callLock(lockBtn.dataset.smLock, lockBtn.dataset.smLockAction);
      return;
    }
    const ttsBtn = e.target.closest("[data-sm-tts-idx]");
    if (ttsBtn) {
      const idx = parseInt(ttsBtn.dataset.smTtsIdx, 10);
      const msgs = this._ttsMessages();
      if (msgs[idx]) this._sendTTS(msgs[idx].label, msgs[idx].message, msgs[idx].speakers);
      return;
    }
    const pinKey = e.target.closest("[data-sm-pin]");
    if (pinKey) { this._handlePin(pinKey.dataset.smPin); return; }

    const armBtn = e.target.closest("[data-sm-arm]");
    if (armBtn) { this._handleArm(armBtn.dataset.smArm); return; }
  }

  // ── Arm logic ──────────────────────────────────────────────────────────────
  _handleArm(action) {
    if (this._requireCode()) {
      this._pinMode = action; this._pinValue = ""; this._pinError = "";
      this._update(true);
    } else {
      this._callArm(action, null);
    }
  }

  async _callArm(action, code) {
    const haMap = { arm_away:"alarm_arm_away", arm_home:"alarm_arm_home", arm_night:"alarm_arm_night", disarm:"alarm_disarm" };
    const wsMap = { arm_vacation:"secure_me/arm_vacation", arm_home_alone:"secure_me/arm_home_alone" };
    try {
      if (haMap[action]) {
        const d = { entity_id: this._entity() };
        if (code) d.code = code;
        await this._hass.callService("alarm_control_panel", haMap[action], d);
      } else if (wsMap[action]) {
        const w = { type: wsMap[action] };
        if (code) w.code = code;
        await this._hass.callWS(w);
      }
      this._pinMode = null; this._pinValue = ""; this._pinError = "";
    } catch {
      this._pinError = this._state() === "unknown" ? "Alarm ikke fundet" : "Forkert kode";
    }
    this._update(true);
  }

  // ── PIN logic ──────────────────────────────────────────────────────────────
  _handlePin(key) {
    if (key === "cancel") { this._pinMode = null; this._pinValue = ""; this._pinError = ""; this._update(true); return; }
    if (key === "back")   { this._pinValue = this._pinValue.slice(0,-1); this._pinError = ""; this._update(true); return; }
    if (key === "ok")     { if (this._pinValue.length >= 1) this._callArm(this._pinMode, this._pinValue); return; }
    if (this._pinValue.length < 8) {
      this._pinValue += key; this._pinError = ""; this._update(true);
      if (this._pinValue.length === 4) this._callArm(this._pinMode, this._pinValue);
    }
  }

  // ── Lock ──────────────────────────────────────────────────────────────────
  async _callLock(entityId, action) {
    try {
      await this._hass.callService("lock", action, { entity_id: entityId });
      setTimeout(() => this._update(true), 700);
    } catch(err) { console.error("Lock action failed:", err); }
  }

  // ── TTS ──────────────────────────────────────────────────────────────────
  async _sendTTS(label, message, speakers) {
    if (this._ttsSending) return;
    this._ttsSending = label; this._ttsError = null; this._update(true);
    try {
      await this._hass.callWS({
        type: "secure_me/test_tts",
        message,
        ...(speakers?.length ? { speaker_ids: speakers } : {}),
      });
    } catch {
      this._ttsError = "TTS fejlede — er TTS-modulet aktiveret?";
    } finally {
      this._ttsSending = null; this._update(true);
    }
  }

  // ── Cleanup ───────────────────────────────────────────────────────────────
  disconnectedCallback() {
    if (this._countdownTimer) { clearInterval(this._countdownTimer); this._countdownTimer = null; }
  }

  getCardSize() { return 4; }
  static getConfigElement() { return document.createElement("secure-me-alarm-card-editor"); }
}

customElements.define("secure-me-alarm-card", SecureMeAlarmCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "secure-me-alarm-card",
  name: "Secure Me Alarm Card",
  description: "Alarm control card for Secure Me — arm, disarm, locks, TTS",
  preview: true,
});
