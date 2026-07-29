// secure-me-alarm-card.js
// Secure Me — Alarm control card
// VERSION = "1.5.3"

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
  skip:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>',
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
  armed_custom_bypass: { label: "Tilkoblet — Alene",  color: "#10b981", glow: "rgba(16,185,129,0.4)",   pulse: false },
  unknown:          { label: "Henter status...",   color: "#64748b", glow: "rgba(100,116,139,0.2)",  pulse: false },
};

// v1.5.0: short label + icon per arm mode, used by the dedicated "arming"
// countdown view (see _renderArming()) to show what's being armed into.
const _MODE_LABEL = {
  armed_away: "Borte", armed_home: "Hjemme", armed_night: "Nat",
  armed_vacation: "Ferie", armed_home_alone: "Alene",
};
const _MODE_ICON = {
  armed_away: SMI.lock, armed_home: SMI.home, armed_night: SMI.moon,
  armed_vacation: SMI.plane, armed_home_alone: SMI.users,
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
    this._hass              = null;
    this._config            = {};
    this._shellBuilt        = false;
    this._pinValue          = "";
    this._pinMode           = null;
    this._pinError          = "";
    this._ttsSending        = null;
    this._ttsError          = null;
    this._dynamicMsgs       = null;
    this._locks             = [];
    this._localCountdown    = null;
    this._countdownTimer    = null;
    this._floorplan         = null;
    this._floorplanLoaded   = false;
    this._lastFpSensorStates = {};
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

    // Live floorplan sensor tracking: repaint canvas when in Home Alone mode
    // and any assigned sensor state has changed, without a full body rebuild.
    if (
      this._state() === "armed_home_alone" &&
      this._floorplanLoaded &&
      this._floorplan?.image_url
    ) {
      const allSensors = [];
      for (const room of Object.values(this._floorplan.rooms || {})) {
        (room.sensors || []).forEach(eid => allSensors.push(eid));
      }
      for (const op of (this._floorplan.openings || [])) {
        if (op.entity_id) allSensors.push(op.entity_id);
      }
      // v1.5.0 etape 3 gap-fix: individual sensor pin markers (fp.markers)
      // must also be watched, or a pin-only sensor's own state change would
      // never trigger a repaint -- it would just show whatever state it was
      // in at first load, forever.
      Object.keys(this._floorplan.markers || {}).forEach(eid => allSensors.push(eid));
      if (allSensors.length > 0) {
        const prev = this._lastFpSensorStates;
        let changed = false;
        const next = {};
        for (const eid of allSensors) {
          const v = h.states?.[eid]?.state || "off";
          next[eid] = v;
          if (prev[eid] !== v) changed = true;
        }
        if (changed) {
          this._lastFpSensorStates = next;
          this._repaintFloorplan();
        }
      }
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
      const [msgRes, modRes, fpRes] = await Promise.all([
        this._hass.callWS({ type: "secure_me/get_home_alone_messages" }),
        this._hass.callWS({ type: "secure_me/get_modules" }),
        this._hass.callWS({ type: "secure_me/get_floorplan" }).catch(() => null),
      ]);
      // Floorplan
      if (fpRes) {
        this._floorplan = {
          image_url: fpRes.image_url || null,
          width:     fpRes.width     || 0,
          height:    fpRes.height    || 0,
          rooms:     fpRes.rooms     || {},
          openings:  fpRes.openings  || [],
          // v1.5.0 etape 3 gap-fix: individual sensor pin markers were never
          // copied into this._floorplan at all, so _buildFloorplanSVGContent's
          // new pin-rendering had nothing to draw from even after being added.
          markers:   fpRes.markers   || {},
        };
      }
      this._floorplanLoaded = true;
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

  _entity() {
    const cfgId = this._config.entity;
    // If the configured entity exists in hass.states, use it.
    if (cfgId && this._hass?.states?.[cfgId]) return cfgId;
    // Fallback: auto-detect any alarm_control_panel entity that belongs to
    // Secure Me (identified by the presence of the secure_me_mode attribute).
    if (this._hass?.states) {
      const found = Object.keys(this._hass.states).find(k =>
        k.startsWith("alarm_control_panel.") &&
        this._hass.states[k].attributes?.secure_me_mode !== undefined
      );
      if (found) return found;
      // Last resort: any alarm_control_panel entity.
      const any = Object.keys(this._hass.states).find(k => k.startsWith("alarm_control_panel."));
      if (any) return any;
    }
    return cfgId || "alarm_control_panel.secure_me_alarm_system_alarm";
  }
  _requireCode() { return this._config.require_code !== false; }
  _showHA()      { return this._config.show_home_alone !== false; }
  _showTTS()     { return this._config.show_tts !== false; }
  _ttsMessages() { return this._dynamicMsgs ?? this._config.tts_messages ?? []; }
  _state() {
    // Prefer secure_me_mode attribute (true Secure Me state string) over
    // e.state (HA-canonical, which maps armed_home_alone -> armed_custom_bypass).
    const e = this._hass?.states?.[this._entity()];
    if (!e) return "unknown";
    return e.attributes?.secure_me_mode || e.state || "unknown";
  }
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

        /* ── Arming (exit-delay countdown) view ── */
        .arming-view {
          display: flex; flex-direction: column; align-items: center;
          gap: 14px; padding: 6px 0 2px;
        }
        .arming-countdown {
          font-family: 'DM Mono', monospace;
          font-size: 46px;
          font-weight: 700;
          color: #f59e0b;
          line-height: 1;
          letter-spacing: 0.02em;
          font-variant-numeric: tabular-nums;
        }
        .arming-target {
          display: flex; align-items: center; gap: 8px;
          font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.65);
        }
        .arming-target svg { width: 18px; height: 18px; color: #f59e0b; }
        .arming-actions { display: flex; gap: 8px; width: 100%; }
        .arming-btn {
          flex: 1;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          padding: 13px; border-radius: 14px; cursor: pointer;
          font-family: inherit; font-size: 13px; font-weight: 700;
          letter-spacing: 0.01em;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.7);
          transition: all 0.15s;
        }
        .arming-btn svg { width: 16px; height: 16px; }
        .arming-btn:hover { background: rgba(255,255,255,0.09); }
        .arming-btn:active { transform: scale(0.96); }
        .arming-btn.skip   { border-color: rgba(245,158,11,0.35); color: #f59e0b; background: rgba(245,158,11,0.08); }
        .arming-btn.skip:hover   { background: rgba(245,158,11,0.15); }
        .arming-btn.cancel { border-color: rgba(239,68,68,0.3);  color: #ef4444; background: rgba(239,68,68,0.1); }
        .arming-btn.cancel:hover { background: rgba(239,68,68,0.16); }

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

        /* ── Arming countdown view (v1.5.0) ── */
        .arming-view {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          padding: 6px 4px 2px;
          text-align: center;
        }
        .arming-icon {
          width: 56px; height: 56px;
          border-radius: 16px;
          display: flex; align-items: center; justify-content: center;
          margin-bottom: 4px;
        }
        .arming-icon svg { width: 28px; height: 28px; }
        .arming-label {
          font-size: 13px;
          font-weight: 600;
          color: rgba(255,255,255,0.65);
          letter-spacing: 0.01em;
        }
        .arming-countdown {
          font-family: 'DM Mono', monospace;
          font-size: 44px;
          font-weight: 700;
          line-height: 1.15;
          letter-spacing: 0.02em;
          font-variant-numeric: tabular-nums;
          animation: sm-count-pulse 0.5s ease;
        }
        .arming-actions {
          display: flex;
          gap: 8px;
          width: 100%;
          margin-top: 8px;
        }
        .arming-skip-btn, .arming-cancel-btn {
          flex: 1;
          display: flex; align-items: center; justify-content: center;
          gap: 8px;
          padding: 12px;
          border-radius: 14px;
          cursor: pointer;
          font-family: inherit;
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.01em;
          transition: all 0.15s;
          border: 1px solid rgba(255,255,255,0.07);
        }
        .arming-skip-btn svg, .arming-cancel-btn svg { width: 16px; height: 16px; }
        .arming-skip-btn {
          background: rgba(255,255,255,0.05);
          color: rgba(255,255,255,0.7);
        }
        .arming-skip-btn:hover { background: rgba(255,255,255,0.09); }
        .arming-cancel-btn {
          background: rgba(239,68,68,0.1);
          border-color: rgba(239,68,68,0.3);
          color: #ef4444;
        }
        .arming-cancel-btn:hover { background: rgba(239,68,68,0.16); }
        .arming-skip-btn:active, .arming-cancel-btn:active { transform: scale(0.96); }
        @keyframes sm-count-pulse {
          0%   { transform: scale(1);    opacity: 0.7; }
          40%  { transform: scale(1.08); opacity: 1;   }
          100% { transform: scale(1);    opacity: 1;   }
        }

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

        /* ── Floorplan ── */
        .fp-card {
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.07);
          background: rgba(0,0,0,0.35);
        }
        @keyframes fp-dot-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.6; transform: scale(1.4); }
        }
        .fp-dot-active {
          animation: fp-dot-pulse 1.1s ease-in-out infinite;
          transform-origin: center;
        }
        @keyframes fp-room-glow {
          0%, 100% { opacity: 0.32; }
          50%       { opacity: 0.48; }
        }
        .fp-room-active polygon {
          animation: fp-room-glow 2s ease-in-out infinite;
        }
        @keyframes fp-opening-pulse {
          0%, 100% { opacity: 0.9; }
          50%       { opacity: 0.5; }
        }
        .fp-opening-active {
          animation: fp-opening-pulse 1.2s ease-in-out infinite;
        }

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
    const showFp = state === "armed_home_alone" && this._floorplanLoaded && this._floorplan?.image_url;

    return [
      state === "arming" ? this._renderArming() : (armed ? this._renderDisarm() : this._renderArmGrid(state, showHA)),
      showFp        ? this._renderFloorplan()  : "",
      locks.length  ? this._renderLocks()      : "",
      msgs.length   ? this._renderTTS(msgs)    : "",
    ].join("");
  }

  // v1.5.0: dedicated exit-delay countdown view. Previously the arm-mode
  // grid stayed on screen during "arming" with only a small badge in the
  // header showing the countdown -- easy to miss, and the grid stayed
  // clickable during the delay. Backend already exposes target_mode via
  // the entity's extra_state_attributes; this was just never wired up here.
  _renderArming() {
    const modeMap = {
      armed_away:       { icon: SMI.lock,  label: "Borte"  },
      armed_home:       { icon: SMI.home,  label: "Hjemme" },
      armed_night:      { icon: SMI.moon,  label: "Nat"    },
      armed_vacation:   { icon: SMI.plane, label: "Ferie"  },
      armed_home_alone: { icon: SMI.users, label: "Alene"  },
    };
    const target = modeMap[this._attr("target_mode")] || { icon: SMI.lock, label: "" };
    const secs = this._localCountdown != null ? this._localCountdown : 0;

    return `<div class="arming-view">
      <div class="arming-countdown">${secs}s</div>
      <div class="arming-target">${target.icon} Tilkobler ${_smEsc(target.label)}…</div>
      <div class="arming-actions">
        <button class="arming-btn skip" data-sm-skip="1">${SMI.skip} Spring over</button>
        <button class="arming-btn cancel" data-sm-arm="disarm">${SMI.unlock} Fortryd</button>
      </div>
    </div>`;
  }

  // ── Floorplan live-view (Home Alone mode only) ────────────────────────────
  // Mirrors panel _renderFloorplanCanvas() in liveMode=true, editMode=false.
  // Rooms: invisible unless active (sensor = on). Openings: always visible.
  // Uses img+SVG overlay with padding-bottom aspect-ratio, same as panel.

  _fpRoomIsActive(room) {
    return (room.sensors || []).some(eid => this._hass?.states?.[eid]?.state === "on");
  }

  _fpPointsToSvgPolygon(points, vw, vh) {
    return points.map(([x, y]) => `${(x / 100 * vw).toFixed(1)},${(y / 100 * vh).toFixed(1)}`).join(" ");
  }

  // v1.5.0 etape 3 gap-fix: individual sensor pin markers (fp.markers) --
  // point-sensors not tied to a room polygon (e.g. a standalone motion
  // sensor). The panel's own "Alene-tilstand live" preview
  // (_renderFloorplanCanvas in secure-me-panel.js) has always rendered
  // these as pulsing red/green pins; this card's live view previously only
  // drew rooms + openings, so pin-only sensors were invisible on the real
  // dashboard even though they showed correctly inside the config panel.

  _sensorIsActive(entityId) {
    return this._hass?.states?.[entityId]?.state === "on";
  }

  _sensorFriendlyName(entityId) {
    return this._hass?.states?.[entityId]?.attributes?.friendly_name || entityId;
  }

  // Mirrors panel._fpRenderSensorPinInner() so both surfaces render pins
  // identically. VW/VH passed in (not recomputed) to match this card's
  // existing _buildFloorplanSVGContent/_renderFloorplan call sites.
  _fpRenderSensorPinInner(eid, m, VW, VH) {
    const x = parseFloat(m.x_pct);
    const y = parseFloat(m.y_pct);
    if (isNaN(x) || isNaN(y)) return "";
    const sx = (x / 100 * VW).toFixed(1);
    const sy = (y / 100 * VH).toFixed(1);
    const isActive = this._sensorIsActive(eid);
    const kind  = m.kind || "motion";
    const color = isActive ? "#ef4444" : "#10b981";
    const dim   = isActive ? "rgba(239,68,68,0.18)" : "rgba(16,185,129,0.12)";
    const r     = isActive ? 14 : 10;
    const label = m.label || this._sensorFriendlyName(eid);

    let iconPath = "";
    if (kind === "motion" || kind === "occupancy") {
      iconPath = `<circle cx="${sx}" cy="${sy}" r="4" fill="${color}" opacity="0.9" pointer-events="none"/>`;
    } else if (kind === "door") {
      iconPath = `<rect x="${(parseFloat(sx)-3.5).toFixed(1)}" y="${(parseFloat(sy)-5).toFixed(1)}" width="7" height="10" rx="1" fill="${color}" opacity="0.85" pointer-events="none"/>`;
    } else if (kind === "window") {
      iconPath = `<rect x="${(parseFloat(sx)-5).toFixed(1)}" y="${(parseFloat(sy)-3).toFixed(1)}" width="10" height="6" rx="1" fill="${color}" opacity="0.85" pointer-events="none"/>`;
    }

    const pulseRing = isActive ? `
      <circle cx="${sx}" cy="${sy}" r="${r + 5}" fill="none"
              stroke="${color}" stroke-width="1.5" opacity="0.4"
              pointer-events="none">
        <animate attributeName="r" values="${r}; ${r+10}; ${r}" dur="1.8s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.5; 0; 0.5" dur="1.8s" repeatCount="indefinite"/>
      </circle>` : "";

    return `
      ${pulseRing}
      <circle cx="${sx}" cy="${sy}" r="${r}" fill="${dim}" stroke="${color}"
              stroke-width="1.5" pointer-events="none"/>
      ${iconPath}
      ${isActive ? `<text x="${sx}" y="${(parseFloat(sy) + r + 14).toFixed(1)}"
            text-anchor="middle" font-family="DM Sans,sans-serif"
            font-size="16" font-weight="600" fill="${color}" opacity="0.95"
            pointer-events="none" style="user-select:none">${_smEsc(label)}</text>` : ""}
    `;
  }

  _buildFloorplanSVGContent(fp, VW, VH) {
    const rooms       = fp.rooms    || {};
    const openings    = fp.openings || [];
    const roomEntries = Object.entries(rooms);
    const palette     = ["#7c3aed","#3b82f6","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899"];

    // Rooms: only render active ones (live mode behaviour)
    const svgRooms = roomEntries.map(([, room], idx) => {
      const pts = room.points || [];
      if (pts.length < 3) return "";
      const color    = room.color || palette[idx % palette.length];
      const isActive = this._fpRoomIsActive(room);
      const polyPts  = this._fpPointsToSvgPolygon(pts, VW, VH);
      // Inactive rooms: opacity 0 (invisible), active: glow fill
      const fillOp   = isActive ? 0.35 : 0;
      const strokeOp = isActive ? 0.8  : 0;
      const cls      = isActive ? "fp-room-active" : "";
      return `<polygon points="${polyPts}"
                 fill="${color}" fill-opacity="${fillOp}"
                 stroke="${color}" stroke-opacity="${strokeOp}"
                 stroke-width="1.5" stroke-linejoin="round"
                 class="${cls}" style="pointer-events:none"/>`;
    }).join("");

    // Openings: only visible when sensor is open (state = "on").
    // If no entity_id assigned, keep invisible (consistent with rooms behaviour).
    const svgOpenings = openings.map(op => {
      if (!op.points || op.points.length < 2) return "";
      const eid    = op.entity_id || null;
      const isOpen = eid ? this._hass?.states?.[eid]?.state === "on" : false;
      if (!isOpen) return "";
      const [x1, y1] = op.points[0];
      const [x2, y2] = op.points[1];
      const sx1 = (x1 / 100 * VW).toFixed(1), sy1 = (y1 / 100 * VH).toFixed(1);
      const sx2 = (x2 / 100 * VW).toFixed(1), sy2 = (y2 / 100 * VH).toFixed(1);
      const color = op.type === "window" ? "#fbbf24" : "#ef4444";
      const cls   = "fp-opening-active";
      return `<line x1="${sx1}" y1="${sy1}" x2="${sx2}" y2="${sy2}"
                stroke="${color}" stroke-width="6" stroke-linecap="round" opacity="0.9"
                class="${cls}" style="pointer-events:none"/>
              <circle cx="${sx1}" cy="${sy1}" r="5" fill="${color}" opacity="0.85" style="pointer-events:none"/>
              <circle cx="${sx2}" cy="${sy2}" r="5" fill="${color}" opacity="0.85" style="pointer-events:none"/>`;
    }).join("");

    // Individual sensor pin markers (fp.markers) -- point-sensors not
    // assigned to any room polygon. Always rendered (color/pulse alone
    // conveys active vs inactive), matching the panel's own live preview.
    const markerEntries = Object.entries(fp.markers || {});
    const svgSensorPins = markerEntries.map(([eid, m]) => {
      const inner = this._fpRenderSensorPinInner(eid, m, VW, VH);
      if (!inner) return "";
      const isActive = this._sensorIsActive(eid);
      return `<g class="fp-pin" data-fp-pin="${eid}" data-fp-pin-active="${isActive ? 1 : 0}">${inner}</g>`;
    }).join("");

    return svgRooms + svgOpenings + svgSensorPins;
  }

  _buildFloorplanLabels(fp) {
    // Active room labels as HTML divs (same as panel live mode)
    const rooms       = fp.rooms || {};
    const roomEntries = Object.entries(rooms);
    const palette     = ["#7c3aed","#3b82f6","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899"];

    return roomEntries.map(([, room], idx) => {
      const pts = room.points || [];
      if (pts.length < 3 || !this._fpRoomIsActive(room)) return "";
      const cx    = pts.reduce((s, [x]) => s + x, 0) / pts.length;
      const cy    = pts.reduce((s, [, y]) => s + y, 0) / pts.length;
      const color = room.color || palette[idx % palette.length];
      return `<div style="position:absolute;left:${cx}%;top:${cy}%;
                          transform:translate(-50%,-50%);
                          background:${color}cc;
                          color:#fff;font-size:11px;font-weight:700;
                          padding:3px 8px;border-radius:6px;
                          white-space:nowrap;pointer-events:none">
                ${_smEsc(room.name || "")}
              </div>`;
    }).join("");
  }

  _renderFloorplan() {
    const fp  = this._floorplan;
    const url = fp.image_url;
    const aspectRatio = fp.width && fp.height ? (fp.height / fp.width) : 0.6;
    const VW  = 1000;
    const VH  = Math.round(VW * aspectRatio);

    const svgContent = this._buildFloorplanSVGContent(fp, VW, VH);
    const labels     = this._buildFloorplanLabels(fp);

    return `<div>
      <div class="sec-label">Floorplan — Live</div>
      <div class="fp-card">
        <div id="sm-fp-canvas" style="position:relative;width:100%;
              padding-bottom:${(aspectRatio * 100).toFixed(2)}%;
              background:#111;overflow:hidden;border-radius:10px">
          <img src="${_smEsc(url)}" alt="Floorplan" draggable="false"
               style="position:absolute;inset:0;width:100%;height:100%;
                      object-fit:contain;pointer-events:none">
          <svg viewBox="0 0 ${VW} ${VH}"
               style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none"
               xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id="sm-fp-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="8" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            ${svgContent}
          </svg>
          <div style="position:absolute;inset:0;pointer-events:none">
            ${labels}
          </div>
        </div>
      </div>
    </div>`;
  }

  // Repaint only the floorplan overlay without a full body rebuild
  _repaintFloorplan() {
    const canvas = this.shadowRoot?.getElementById("sm-fp-canvas");
    if (!canvas) {
      this._update(true);
      return;
    }
    const fp  = this._floorplan;
    const VW  = 1000;
    const VH  = Math.round(VW * (fp.width && fp.height ? (fp.height / fp.width) : 0.6));

    const svgEl   = canvas.querySelector("svg");
    const labelEl = canvas.querySelector("div");

    if (svgEl) {
      svgEl.innerHTML = `<defs>
        <filter id="sm-fp-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="8" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>${this._buildFloorplanSVGContent(fp, VW, VH)}`;
    }
    if (labelEl) {
      labelEl.innerHTML = this._buildFloorplanLabels(fp);
    }
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

    const skipBtn = e.target.closest("[data-sm-skip]");
    if (skipBtn) { this._handleSkip(); return; }

    const armBtn = e.target.closest("[data-sm-arm]");
    if (armBtn) { this._handleArm(armBtn.dataset.smArm); return; }
  }

  // v1.5.0: "Spring over" button in the arming countdown view -- uses the
  // existing secure_me/skip_delay WS command (added in v1.4.3 but never
  // exposed anywhere in this card until now).
  async _handleSkip() {
    try {
      await this._hass.callWS({ type: "secure_me/skip_delay" });
    } catch {
      /* ignore -- state will simply not change if it fails */
    }
    this._update(true);
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
    // v1.5.0: arm_vacation is a first-class HA AlarmControlPanelEntityFeature
    // (ARM_VACATION, since v1.4.3) so it now goes through the standard
    // alarm_control_panel service like away/home/night/disarm. Only
    // arm_home_alone remains websocket-only, since HA's alarm_control_panel
    // interface has no equivalent standard command for it.
    const haMap = { arm_away:"alarm_arm_away", arm_home:"alarm_arm_home", arm_night:"alarm_arm_night", arm_vacation:"alarm_arm_vacation", disarm:"alarm_disarm" };
    const wsMap = { arm_home_alone:"secure_me/arm_home_alone" };
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
      this._pinValue = ""; this._pinError = "";
    } catch {
      // Re-open the PIN screen so the error is visible and the user can retry.
      this._pinMode = action;
      this._pinError = this._state() === "unknown" ? "Alarm ikke fundet" : "Forkert kode";
    }
    this._update(true);
  }

  // ── PIN logic ──────────────────────────────────────────────────────────────
  _handlePin(key) {
    if (key === "cancel") { this._pinMode = null; this._pinValue = ""; this._pinError = ""; this._update(true); return; }
    if (key === "back")   { this._pinValue = this._pinValue.slice(0,-1); this._pinError = ""; this._update(true); return; }
    if (key === "ok") {
      if (this._pinValue.length >= 1) {
        const action = this._pinMode;
        const code = this._pinValue;
        // Leave the PIN screen right away and show the default/arming view;
        // _callArm() will re-open this screen with an error if the code
        // turns out to be wrong.
        this._pinMode = null;
        this._update(true);
        this._callArm(action, code);
      }
      return;
    }
    if (this._pinValue.length < 8) {
      // User must press OK to submit - no auto-submit on 4 digits to prevent accidental activation.
      this._pinValue += key; this._pinError = ""; this._update(true);
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
