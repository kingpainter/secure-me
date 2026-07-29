/**
 * Secure Me - Configuration Panel
 * VERSION: 1.5.3
 *
 * Custom panel for Home Assistant using vanilla Custom Elements.
 * Uses HA CSS custom properties for theme compatibility.
 * Communicates with backend via WebSocket API.
 */

const DOMAIN = "secure_me";
const VERSION = "1.5.3";

// === Styles ===
const panelStyles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap');

  :host {
    --sm-accent:     #7c3aed;
    --sm-accent2:    #3b82f6;
    --sm-accent3:    #06b6d4;
    --sm-accent-dim: rgba(124,58,237,0.14);
    --sm-accent-glow: rgba(124,58,237,0.22);
    --sm-danger:     #ef4444;  --sm-danger-dim: rgba(239,68,68,0.14);
    --sm-warning:    #f59e0b;  --sm-warning-dim: rgba(245,158,11,0.14);
    --sm-green:      #10b981;  --sm-green-dim: rgba(16,185,129,0.12);
    --sm-blue:       #3b82f6;  --sm-blue-dim: rgba(59,130,246,0.12);
    --sm-cyan:       #06b6d4;  --sm-cyan-dim: rgba(6,182,212,0.12);
    --sm-purple:     #7c3aed;  --sm-purple-dim: rgba(124,58,237,0.12);
    --sm-teal:       #14b8a6;  --sm-teal-dim: rgba(20,184,166,0.12);
    --sm-bg:      var(--primary-background-color,   #0f1923);
    --sm-surface: var(--secondary-background-color, #1a2535);
    --sm-bg3:     #243044;
    --sm-text:           var(--primary-text-color,   #e2e8f0);
    --sm-text-secondary: var(--secondary-text-color, #94a3b8);
    --sm-text-tertiary:  var(--disabled-text-color,  rgba(148,163,184,0.55));
    --sm-border: var(--divider-color, rgba(148,163,184,0.12));
    --sm-card-radius: 18px;
    display: flex; flex-direction: column;
    font-family: 'DM Sans', var(--paper-font-body1_-_font-family, sans-serif);
    background: var(--sm-bg); color: var(--sm-text);
    height: 100%; overflow: hidden; -webkit-font-smoothing: antialiased;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  .panel-topbar { flex-shrink: 0; padding: 16px 28px 12px; background: var(--sm-bg); border-bottom: 1px solid var(--sm-border); }
  @media (max-width: 600px) { .panel-topbar { padding: 12px 16px 8px; } }

  .sm-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
  .sm-header-icon { width: 42px; height: 42px; border-radius: 12px; background: linear-gradient(135deg, var(--sm-accent), var(--sm-accent2)); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 16px var(--sm-accent-glow); flex-shrink: 0; }
  .sm-header-icon svg { width: 22px; height: 22px; color: #fff; }
  .sm-header-text { flex: 1; min-width: 0; }
  .sm-header-title { font-size: 20px; font-weight: 700; letter-spacing: -0.3px; color: var(--sm-text); }
  .sm-header-sub { font-size: 11px; color: var(--sm-text-tertiary); font-family: 'DM Mono', monospace; margin-top: 1px; }
  .sm-header-pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; flex-shrink: 0; }
  .sm-header-pill .pill-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 6px currentColor; }
  .sm-header-pill.disarmed  { background: var(--sm-green-dim);   color: var(--sm-green); }
  .sm-header-pill.armed     { background: var(--sm-danger-dim);  color: var(--sm-danger); }
  .sm-header-pill.arming    { background: var(--sm-warning-dim); color: var(--sm-warning); }
  .sm-header-pill.triggered { background: var(--sm-danger-dim);  color: var(--sm-danger); animation: sm-pulse-red 1s ease-in-out infinite; }
  .sm-header-pill.pending   { background: var(--sm-warning-dim); color: var(--sm-warning); }
  .sm-ws-banner { display:flex;align-items:center;gap:8px;padding:8px 16px;
    background:var(--sm-warning-dim);color:var(--sm-warning);font-size:12px;font-weight:600;
    border-bottom:1px solid rgba(245,158,11,0.2);animation:sm-fade-in 0.3s ease; }
  .sm-ws-banner svg { flex-shrink:0;animation:sm-spin 1.2s linear infinite; }
  @keyframes sm-spin { to { transform:rotate(360deg); } }
  .sm-skeleton { background:linear-gradient(90deg,var(--sm-bg2) 25%,var(--sm-bg3) 50%,var(--sm-bg2) 75%);
    background-size:200% 100%;animation:sm-shimmer 1.4s infinite;border-radius:8px; }
  @keyframes sm-shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

  .sm-tabs { display: flex; gap: 2px; flex-wrap: wrap; }
  .sm-tab { padding: 7px 14px; border-radius: 10px; border: none; background: transparent; color: var(--sm-text-secondary); cursor: pointer; font-size: 13px; font-weight: 500; font-family: 'DM Sans', sans-serif; transition: all 0.2s; white-space: nowrap; display: flex; align-items: center; gap: 6px; }
  .sm-tab svg { width: 15px; height: 15px; }
  .sm-tab.active { background: var(--sm-bg3); border: 1px solid var(--sm-border); color: var(--sm-accent); }
  .sm-tab:hover:not(.active) { color: var(--sm-text); background: rgba(255,255,255,0.04); }
  @media (max-width: 600px) { .sm-tab span.tab-label { display: none; } .sm-header-title { font-size: 17px; } }

  .panel-scroll { flex: 1; min-height: 0; overflow-y: auto; overflow-x: hidden; padding: 20px 28px 48px; }
  .panel-scroll::-webkit-scrollbar { width: 5px; }
  .panel-scroll::-webkit-scrollbar-track { background: transparent; }
  .panel-scroll::-webkit-scrollbar-thumb { background: var(--sm-bg3); border-radius: 3px; }
  @media (max-width: 600px) { .panel-scroll { padding: 12px 16px 32px; } }

  .sm-card { background: var(--sm-surface); border-radius: var(--sm-card-radius); border: 1px solid var(--sm-border); padding: 20px; margin-bottom: 12px; transition: border-color 0.2s; }
  .sm-card:hover { border-color: rgba(148,163,184,0.28); }
  .sm-card.no-pad { padding: 0; }

  .sm-list-header { display: grid; gap: 0; align-items: center; padding: 10px 16px; background: rgba(255,255,255,0.03); border-bottom: 1px solid var(--sm-border); font-size: 11px; font-weight: 600; color: var(--sm-text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; }
  .sm-list-row { display: flex; flex-direction: column; align-items: stretch; gap: 5px; padding: 12px 16px; border-bottom: 1px solid var(--sm-border); transition: opacity 0.2s; }
  .sm-list-row:last-child { border-bottom: none; }
  .sm-list-row.disabled { opacity: 0.45; }
  .sm-list-row-top { display: flex; align-items: center; gap: 8px; min-width: 0; }
  .sm-list-row-name { flex: 1; font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
  .sm-list-row-eid { font-size: 11px; color: var(--sm-text-tertiary); font-family: 'DM Mono', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.02em; }
  .badge.contact      { color: var(--sm-blue);    background: var(--sm-blue-dim); }
  .badge.environmental{ color: var(--sm-danger);  background: var(--sm-danger-dim); font-weight: 700; }
  .badge.motion       { color: var(--sm-purple);  background: var(--sm-purple-dim); }
  .badge.presence     { color: var(--sm-teal);    background: var(--sm-teal-dim); }
  .badge.entry        { color: var(--sm-warning); background: var(--sm-warning-dim); }
  .badge.interior     { color: var(--sm-blue);    background: var(--sm-blue-dim); }
  .badge.perimeter    { color: var(--sm-danger);  background: var(--sm-danger-dim); }
  .badge.instant      { color: var(--sm-purple);  background: var(--sm-purple-dim); }
  .badge.accent       { color: var(--sm-accent);  background: var(--sm-accent-dim); }
  .badge.actions      { color: var(--sm-purple);  background: var(--sm-purple-dim); }

  .sm-checkbox { width: 20px; height: 20px; border-radius: 6px; border: 2px solid var(--sm-text-tertiary); background: transparent; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s; padding: 0; flex-shrink: 0; }
  .sm-checkbox.checked { border: none; background: var(--sm-accent); }
  .sm-checkbox svg { width: 14px; height: 14px; color: #fff; }

  .sm-toggle { width: 44px; height: 24px; border-radius: 24px; background: rgba(255,255,255,0.15); cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; border: none; padding: 0; }
  .sm-toggle.on { background: var(--sm-accent); }
  .sm-toggle .dot { width: 18px; height: 18px; border-radius: 50%; background: #fff; position: absolute; top: 3px; left: 3px; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
  .sm-toggle.on .dot { left: 23px; }

  .sm-btn { border: none; border-radius: 10px; padding: 8px 16px; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.15s; font-family: inherit; }
  .sm-btn.sm { padding: 6px 12px; font-size: 12px; }
  .sm-btn.primary { background: var(--sm-accent); color: #fff; font-weight: 600; }
  .sm-btn.default { background: rgba(255,255,255,0.08); color: var(--sm-text); }
  .sm-btn.danger  { background: var(--sm-danger-dim); color: var(--sm-danger); }
  .sm-btn.ghost   { background: transparent; color: var(--sm-text-secondary); }
  .sm-btn.ghost-outlined { background: transparent; color: var(--sm-text-secondary); border: 1px solid var(--sm-text-tertiary); border-radius: 20px; padding: 6px 14px; font-size: 12px; }
  .sm-btn.ghost-outlined:hover { border-color: var(--sm-text-secondary); background: rgba(255,255,255,0.04); }
  .sm-btn:hover { filter: brightness(1.1); }
  .sm-btn svg { width: 14px; height: 14px; }

  .sm-input, .sm-select { width: 100%; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.08); color: var(--sm-text); border: 1px solid var(--sm-border); font-size: 13px; font-family: inherit; box-sizing: border-box; }
  .sm-select { appearance: auto; }
  .sm-label { font-size: 11px; color: var(--sm-text-secondary); display: block; margin-bottom: 4px; }

  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .section-title  { font-size: 11px; font-weight: 700; color: var(--sm-text-secondary); text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 10px 2px; }
  .section-subtitle { font-size: 13px; color: var(--sm-text-secondary); margin: 4px 0 0; }

  .info-card { padding: 14px 16px; border-radius: 12px; display: flex; gap: 12px; align-items: flex-start; margin-bottom: 12px; }
  .info-card.warning { background: var(--sm-warning-dim); border: 1px solid rgba(245,158,11,0.2); }
  .info-card.info    { background: var(--sm-blue-dim);    border: 1px solid rgba(59,130,246,0.2); }
  .info-card .info-title { font-size: 13px; font-weight: 600; }
  .info-card .info-text  { font-size: 12px; color: var(--sm-text-secondary); margin-top: 4px; }

  .sensor-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
  @media (max-width: 600px) { .sensor-two-col { grid-template-columns: 1fr; } }
  .zone-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media (max-width: 600px) { .zone-grid { grid-template-columns: 1fr; } }
  .zone-card { cursor: pointer; }
  .zone-modes { display: flex; gap: 4px; margin-top: 8px; }
  .zone-mode { padding: 2px 6px; border-radius: 4px; font-size: 10px; background: rgba(255,255,255,0.08); color: var(--sm-text-secondary); }

  .user-avatar { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; flex-shrink: 0; }
  .nfc-tag { padding: 8px 12px; border-radius: 8px; display: flex; align-items: center; gap: 8px; border: 1px solid rgba(124,58,237,0.15); background: var(--sm-purple-dim); margin-top: 12px; }
  .nfc-tag-id { font-size: 12px; color: var(--sm-purple); font-family: 'DM Mono', monospace; }

  .module-header { display: flex; align-items: center; gap: 14px; padding: 14px 16px; transition: opacity 0.2s; }
  .module-header.disabled { opacity: 0.45; }
  .module-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; cursor: pointer; }
  .module-icon:hover { filter: brightness(1.2); transform: scale(1.05); }
  .module-icon.disabled-icon { cursor: default; }
  .module-icon.disabled-icon:hover { filter: none; transform: none; }
  .module-name-area { flex: 1; cursor: pointer; }
  .module-header.disabled .module-name-area { cursor: default; }
  .module-config { padding: 0 16px 16px; border-top: 1px solid var(--sm-border); padding-top: 16px; }
  .module-entity-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--sm-border); }

  .segment-control { display: flex; background: var(--sm-bg3); border-radius: 10px; padding: 3px; margin-bottom: 16px; }
  .segment-btn { flex: 1; padding: 8px 12px; border-radius: 8px; border: none; background: transparent; color: var(--sm-text-secondary); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: inherit; }
  .segment-btn.active { background: var(--sm-surface); color: var(--sm-text); }

  .notif-message { font-size: 12px; color: var(--sm-text-secondary); margin-top: 6px; padding: 6px 10px; border-radius: 6px; background: rgba(255,255,255,0.04); font-family: 'DM Mono', monospace; }
  .notif-actions { display: flex; gap: 8px; margin-top: 12px; }

  .placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; }
  .placeholder-icon { width: 64px; height: 64px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 0; margin-bottom: 16px; }
  .placeholder-icon svg { width: 32px; height: 32px; }
  .placeholder h3 { margin: 0; font-size: 18px; font-weight: 600; }
  .placeholder p { color: var(--sm-text-secondary); font-size: 14px; max-width: 320px; margin-top: 8px; }

  .info-card svg { width: 20px; height: 20px; flex-shrink: 0; }
  .test-overall-icon svg { width: 28px; height: 28px; }
  .module-status-icon svg { width: 16px; height: 16px; }
  .dialog-close svg { width: 18px; height: 18px; }
  .dialog-close { background: none; border: none; color: var(--sm-text-secondary); cursor: pointer; padding: 4px; display: flex; align-items: center; border-radius: 6px; transition: color 0.15s, background 0.15s; }
  .dialog-close:hover { color: var(--sm-text); background: rgba(255,255,255,0.08); }

  .collapsible-header { display: flex; align-items: center; justify-content: space-between; cursor: pointer; padding: 12px 0; user-select: none; }
  .collapsible-header .chevron { width: 16px; height: 16px; transition: transform 0.2s; color: var(--sm-text-tertiary); }
  .collapsible-header.expanded .chevron { transform: rotate(180deg); }
  .collapsible-body { overflow: hidden; max-height: 0; transition: max-height 0.3s ease; }
  .collapsible-body.expanded { max-height: 2000px; }

  .sensor-status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .sensor-status-dot.online  { background: var(--sm-green);  box-shadow: 0 0 6px var(--sm-green); }
  .sensor-status-dot.offline { background: var(--sm-danger); box-shadow: 0 0 6px var(--sm-danger); }

  /* v1.6.0 floorplan room glow */
  @keyframes fp-room-glow {
    0%, 100% { opacity: 0.35; }
    50%       { opacity: 0.55; }
  }
  .fp-room-active { animation: fp-room-glow 1.8s ease-in-out infinite; }
  .fp-room { transition: fill-opacity 0.4s ease, stroke-opacity 0.4s ease; }
  .fp-opening-group { transition: opacity 0.4s ease; }

  .test-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  @media (max-width: 600px) { .test-grid-3 { grid-template-columns: 1fr; } }

  .config-dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.75); display: flex; align-items: center; justify-content: center; z-index: 10000; backdrop-filter: blur(4px); animation: fadeIn 0.2s ease; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  .config-dialog { max-width: 650px; max-height: 90vh; width: 90%; background: var(--sm-surface); border-radius: var(--sm-card-radius); border: 1px solid var(--sm-border); padding: 24px; overflow-y: auto; animation: slideUp 0.3s ease; }
  @media (max-width: 768px) { .config-dialog-overlay { align-items: flex-end; } .config-dialog { width: 100%; max-height: 90vh; border-radius: 16px 16px 0 0; padding: 20px; } }
  @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
  .dialog-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--sm-border); }
  .dialog-title  { font-size: 20px; font-weight: 700; flex: 1; }
  .item-list { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
  .item-card { background: var(--sm-bg3); border: 1px solid var(--sm-border); border-radius: 12px; padding: 16px; }
  .item-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .item-number { font-size: 16px; font-weight: 600; color: var(--sm-text); }
  .form-group { margin-bottom: 16px; }
  .form-group:last-child { margin-bottom: 0; }
  .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--sm-text-secondary); }
  .form-label .optional-hint { font-size: 12px; color: var(--sm-text-tertiary); font-style: italic; font-weight: 400; }
  .form-select, .form-input { width: 100%; padding: 10px 12px; background: rgba(255,255,255,0.08); border: 1px solid var(--sm-border); border-radius: 8px; color: var(--sm-text); font-size: 14px; font-family: inherit; box-sizing: border-box; }
  .form-select { cursor: pointer; }
  select { background: #1a2535; color: var(--sm-text); border: 1px solid var(--sm-border); font-family: inherit; cursor: pointer; }
  select option { background: #1a2535; color: var(--sm-text); padding: 8px; }
  select option:hover, select option:focus, select option:checked { background: #243044; color: var(--sm-text); }
  .form-select option { background: #1a2535; color: var(--sm-text); padding: 8px; }
  .form-select option:hover, .form-select option:focus { background: rgba(124,58,237,0.22); color: #fff; }
  .form-select:focus, .form-input:focus { outline: none; border-color: var(--sm-accent); background: rgba(255,255,255,0.1); }
  .entity-search { width: 100%; padding: 8px 12px; background: rgba(255,255,255,0.08); border: 1px solid var(--sm-border); border-radius: 8px; color: var(--sm-text); font-size: 14px; font-family: inherit; box-sizing: border-box; }
  .form-slider { width: 100%; height: 6px; border-radius: 3px; background: var(--sm-border); outline: none; -webkit-appearance: none; }
  .form-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 50%; background: var(--sm-accent); cursor: pointer; }
  .form-slider::-moz-range-thumb { width: 18px; height: 18px; border-radius: 50%; background: var(--sm-accent); cursor: pointer; border: none; }
  .entity-chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: var(--sm-accent-dim); border: 1px solid var(--sm-accent); border-radius: 16px; font-size: 12px; margin: 4px; }
  .entity-chip button { background: none; border: none; color: var(--sm-text); cursor: pointer; font-size: 16px; line-height: 1; padding: 0; margin-left: 4px; }
  .checkbox-option { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background 0.2s; margin-bottom: 8px; }
  .checkbox-option:hover { background: rgba(255,255,255,0.05); }
  .checkbox-option input[type="checkbox"] { width: 18px; height: 18px; cursor: pointer; margin: 0; }
  .checkbox-option span { cursor: pointer; font-size: 14px; flex: 1; }
  .sm-confirm-cancel { padding: 8px 16px; border-radius: 8px; border: 1px solid var(--sm-border); background: transparent; color: var(--sm-text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; }
  .sm-confirm-ok     { padding: 8px 16px; border-radius: 8px; border: none; background: var(--sm-danger); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; }
  .sm-confirm-cancel:hover { filter: brightness(1.1); }
  .sm-confirm-ok:hover     { filter: brightness(1.1); }
  .sm-toast-container { position: fixed; bottom: 24px; right: 24px; z-index: 20000; display: flex; flex-direction: column; gap: 8px; }
  .sm-toast { padding: 12px 16px; border-radius: 10px; font-size: 13px; font-weight: 500; color: var(--sm-text); max-width: 320px; animation: slideUp 0.3s ease; display: flex; align-items: center; gap: 8px; border: 1px solid var(--sm-border); }
  .sm-toast.success { background: var(--sm-green-dim);   border-color: rgba(16,185,129,0.3);  color: var(--sm-green); }
  .sm-toast.error   { background: var(--sm-danger-dim);  border-color: rgba(239,68,68,0.3);   color: var(--sm-danger); }
  .sm-toast.warning { background: var(--sm-warning-dim); border-color: rgba(245,158,11,0.3);  color: var(--sm-warning); }
  .sm-toast.info    { background: var(--sm-accent-dim);  border-color: rgba(124,58,237,0.3);  color: var(--sm-accent); }
  .sm-toast.fading  { animation: sm-toast-out 0.2s ease forwards; }
  @keyframes sm-toast-out { to { opacity: 0; transform: translateX(20px); } }
  .module-health-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 20px; font-size: 10px; font-weight: 600; letter-spacing: 0.3px; }
  .module-health-badge.ok      { background: var(--sm-green-dim);   color: var(--sm-green); }
  .module-health-badge.warn    { background: var(--sm-warning-dim); color: var(--sm-warning); }
  .module-health-badge.error   { background: var(--sm-danger-dim);  color: var(--sm-danger); }
  .module-health-badge.degraded{ background: var(--sm-danger-dim);  color: var(--sm-danger); }
  .module-health-badge.unknown { background: rgba(255,255,255,0.07);color: var(--sm-text-tertiary); }
  .module-health-badge svg { width: 10px; height: 10px; }
  .arming-countdown { font-variant-numeric: tabular-nums; font-family: 'DM Mono', monospace; }
  @keyframes sm-pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
    50%       { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
  }
`;

// === Icons ===
const ICONS = {
  shield: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  sensor: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  zone: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  user: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  module: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
  bell: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
  flask: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6v5l4 9H5l4-9V3z"/><line x1="10" y1="3" x2="14" y2="3"/></svg>',
  rocket: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>',
  check: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  plus: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  trash: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  play: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
  camera: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
  lock: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  bulb: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>',
  thermo: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
  siren: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><line x1="12" y1="2" x2="12" y2="4"/></svg>',
  speaker: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>',
  nfc: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8.32a7.43 7.43 0 0 1 0 7.36"/><path d="M9.46 6.21a11.76 11.76 0 0 1 0 11.58"/><path d="M12.91 4.1a15.91 15.91 0 0 1 .01 15.8"/><path d="M16.37 2a20.16 20.16 0 0 1 0 20"/></svg>',
  chevron: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
  wifi: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>',
  dots: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="19" cy="12" r="1" fill="currentColor"/></svg>',
  ok: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>',
  warn: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  fail: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  close: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  edit: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
  circle: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>',
  // v1.5.0 floorplan icons
  map: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>',
  upload: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  move: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="5 9 2 12 5 15"/><polyline points="9 5 12 2 15 5"/><polyline points="15 19 12 22 9 19"/><polyline points="19 9 22 12 19 15"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="12" y1="2" x2="12" y2="22"/></svg>',
  door: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v16"/><line x1="3" y1="21" x2="21" y2="21"/><circle cx="15" cy="12" r="1"/></svg>',
  window: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="1"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="12" y1="4" x2="12" y2="20"/></svg>',
  motion: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 4.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/><path d="M9 11l3-1.5L15 11v5l-3 5"/><path d="M9 11l-3 5"/><path d="M15 14l3 1"/></svg>',
};

const icon = (name) => ICONS[name] || "";

// === Tab Definitions ===
const TABS = [
  { key: "sensors", label: "Sensorer", icon: "sensor" },
  { key: "zones", label: "Zoner", icon: "zone" },
  { key: "users", label: "Brugere", icon: "user" },
  { key: "modules", label: "Moduler", icon: "module" },
  { key: "floorplan", label: "Etageplan", icon: "map" },
  { key: "automations", label: "Handlinger", icon: "bell" },
  { key: "testing", label: "Test", icon: "flask" },
  { key: "special", label: "Special", icon: "shield" },
  { key: "future", label: "Fremtid", icon: "rocket" },
];

// Module definitions
const MODULE_DEFS = {
  camera: { name: "Kamera", icon: "camera", desc: "POE-styring & optagelse", color: "var(--sm-blue)", domain: "camera" },
  lock: { name: "Lås", icon: "lock", desc: "Smart låsestyring med automatisk gentagelse", color: "var(--sm-accent)", domain: "lock" },
  lights: { name: "Lys", icon: "bulb", desc: "Automatisk lys & alarmblink", color: "var(--sm-warning)", domain: "light" },
  climate: { name: "Klima", icon: "thermo", desc: "Multi-zone opvarmning", color: "var(--sm-danger)", domain: "climate" },
  siren: { name: "Sirene", icon: "siren", desc: "Alarmlyd med failsafe", color: "var(--sm-danger)", domain: "siren" },
  tts: { name: "TTS", icon: "speaker", desc: "Danske talebeskeder", color: "var(--sm-purple)", domain: "tts" },
};


// ===
// MAIN PANEL ELEMENT
// ===

class SecureMePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._activeTab = "sensors";
    this._alarmState = "disarmed";
    this._alarmCountdown = 0;
    this._data = {
      sensors: [],
      zones: {},
      users: {},
      modules: {},
      notifications: {},
      automations: {},
      scheduledTests: {},
      autoActions: null,
      fakePresenceV2: null,
      // v1.5.0 floorplan state -- updated by _loadFloorplan() once Floorplan tab is opened
      floorplan: { image_url: null, width: 0, height: 0, rooms: {}, openings: [] },
    };
    this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
    this._autoSection = "notifications";
    this._renderTimeout = null;
    this._testRunning = false;
    this._testDescExpanded = false;
    this._schedTemp   = null;    // temp config for scheduled test editing
    this._schedSaving    = false;   // prevents double-submit
    this._ttsTestRunning = false;  // prevents duplicate TTS test calls
    this._speakerProfiles = [];    // v1.4.3: speaker profiles
    this._cameraSaving   = false;  // prevents duplicate camera saves
    this._lockSaving     = false;
    this._climateSaving  = false;
    this._sirenSaving    = false;
    this._lightsSaving   = false;
    this._batteryOkExpanded = false;  // Collapsible: batteries >50%
    this._testHistoryExpanded = false; // Collapsible: test history older entries
    this._envExpanded = false;           // Collapsible: environmental sensors (default collapsed)
    this._hiddenSensorsExpanded = false; // Collapsible: auto-hidden sensors
    this._availablePersons = null;       // Cached person entities for user dialog
    this._sensorStatusExpanded = false; // Collapsible: sensor status hidden entries
    this._sensorsInactiveExpanded = false; // Collapsible: inactive sensors
	this._healthUpdateUnsubscribe = null;
    this._lastHealthUpdate = null;
    // v1.5.0 floorplan state machine
    this._floorplanLoaded = false;
    this._floorplanEditMode = false;
    this._floorplanDrawTool = "rect";
    this._floorplanSelectedRoom = null;
    this._floorplanSelectedOpening = null;
    this._floorplanDrawing = null;
    this._fpSaveDebounce = null;
    this._floorplanUploading = false;
    this._wsConnected = true;  // tracks WS connection health for banner
    this._fpUndoStack = [];       // undo stack: max 20 snapshots
    this._fpKeyboardCleanup = null; // keyboard handler cleanup ref
    // Tab render caches — invalidated on data save
    this._sensorsRenderCache   = null;
    this._sensorsRenderKey     = null;
    this._zonesRenderCache     = null;
    this._zonesRenderKey       = null;
    this._automationsRenderCache = null;
    this._automationsRenderKey   = null;



  }


  // PERF: In-place patch of alarm state pills — avoids full re-render on every state change.
  // Mirrors the _updateWattDisplay / _updateBarsInPlace pattern from pc-user-statistics-panel.
  _updateStatusPills() {
    const root = this.shadowRoot;
    if (!root) return;
    const pill = root.getElementById("shell-status-pill");
    const textEl = root.getElementById("shell-status-text");
    if (!pill) return;
    const state = this._alarmState || "disarmed";
    const cd = this._armingCountdown;
    let cls = "disarmed", label = "Deaktiveret";
    if      (state === "armed_away")       { cls = "armed";    label = "Tilkoblet Borte"; }
    else if (state === "armed_home")       { cls = "armed";    label = "Tilkoblet Hjemme"; }
    else if (state === "armed_night")      { cls = "armed";    label = "Tilkoblet Nat"; }
    else if (state === "armed_vacation")   { cls = "armed";    label = "Tilkoblet Ferie"; }
    else if (state === "armed_home_alone") { cls = "armed";    label = "Alene"; }
    else if (state === "arming")         { cls = "arming";   label = cd > 0 ? `Tilkobler ${cd}s` : "Tilkobler"; }
    else if (state === "pending")        { cls = "pending";  label = cd > 0 ? `Indgang ${cd}s` : "Afventer"; }
    else if (state === "triggered") {
      cls = "triggered";
      const tb = this._alarmTriggeredBy;
      if (tb) {
        const tbName = this._hass?.states?.[tb]?.attributes?.friendly_name || tb.split('.').pop().replace(/_/g,' ');
        label = tbName.length > 22 ? tbName.slice(0,20) + '...' : tbName;
      } else {
        label = "Triggered";
      }
    }
    pill.className = "sm-header-pill " + cls;
    if (textEl) textEl.textContent = label;

    // Open sensors badge — shown when disarmed and sensors are open
    const badgeEl = this.shadowRoot?.getElementById("shell-open-badge");
    if (badgeEl) {
      const openCount = (this._alarmOpenSensors || []).length;
      if (state === "disarmed" && openCount > 0) {
        badgeEl.textContent = openCount + " open";
        badgeEl.style.display = "inline-flex";
      } else {
        badgeEl.style.display = "none";
      }
    }
  }
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._loadData();
    }

    // Track alarm state directly from hass.states — fires immediately on state change
    // without waiting for the 5s health event interval.
    // NOTE: HA's AlarmControlPanelState enum has no 'armed_home_alone' entry —
    // the entity state is 'armed_custom_bypass' when Home Alone is active.
    // The true Secure Me mode is always in the 'secure_me_mode' attribute.
    const alarmEntity = Object.values(hass.states || {}).find(
      s => s.entity_id.startsWith('alarm_control_panel.')
    );
    if (alarmEntity) {
      // Resolve the true Secure Me state.
      // Priority 1: secure_me_mode attribute (set by alarm_control_panel.py — always the coordinator truth)
      // Priority 2: standard HA states (disarmed, arming, pending, triggered, armed_away/home/night/vacation)
      // Ignored:    armed_custom_bypass — HA's internal mapping for armed_home_alone; must never
      //             overwrite a valid state that was already set from the WS endpoint.
      const smMode = alarmEntity.attributes?.secure_me_mode;
      const haState = alarmEntity.state;
      const resolvedMode = smMode
        ? smMode
        : (haState === "armed_custom_bypass" ? this._alarmState : haState);
      if (resolvedMode !== this._alarmState) {
        this._alarmState = resolvedMode;
        this._alarmCountdown = parseInt(alarmEntity.attributes?.countdown || 0);
        this._alarmTriggeredBy = alarmEntity.attributes?.triggered_by || null;
        this._alarmOpenSensors = alarmEntity.attributes?.open_sensors || [];
        this._updateStatusPills();
        // Also queue a render so countdown/armed_by etc. refresh.
        // Skip naar flyout er aaben -- render river inspector-DOM ned.
        if (!this._fpFlyoutActive()) this._queueRender();
      }
    }

    // v1.5.0: Live floorplan refresh in Home Alone mode.
    // Only re-render when (a) the Floorplan tab is open, (b) Home Alone is active,
    // and (c) at least one marker's sensor state actually changed since last check.
    // Without this gate every HA state update would trigger a full re-render.
    if (
      this._activeTab === "floorplan"
      && this._alarmState === "armed_home_alone"
      && this._floorplanLoaded
      && this._data.floorplan?.image_url
      && !this._fpFlyoutActive()
    ) {
      // Collect all sensor entity_ids from rooms AND openings
      const allRoomSensors = [];
      for (const room of Object.values(this._data.floorplan?.rooms || {})) {
        (room.sensors || []).forEach(eid => allRoomSensors.push(eid));
      }
      for (const op of (this._data.floorplan?.openings || [])) {
        if (op.entity_id) allRoomSensors.push(op.entity_id);
      }
      if (allRoomSensors.length > 0) {
        const prev = this._lastMarkerStates || {};
        const next = {};
        let changed = false;
        for (const eid of allRoomSensors) {
          const st = hass.states?.[eid];
          const v = st ? st.state : null;
          next[eid] = v;
          if (prev[eid] !== v) changed = true;
        }
        this._lastMarkerStates = next;
        if (changed) {
          // Targeted DOM patch instead of a full re-render -- see
          // _fpUpdateLiveState() for why this matters for smoothness.
          // Fall back to a full render if the canvas isn't mounted yet
          // (e.g. the very first update right after entering the tab).
          if (!this._fpUpdateLiveState()) this._queueRender();
        }
      }
    }
  }

  set narrow(narrow) {
    this._narrow = narrow;
    if (narrow) this.setAttribute("narrow", "");
    else this.removeAttribute("narrow");
  }

  set panel(panel) { this._panel = panel; }
  set route(route) { this._route = route; }

  disconnectedCallback() {
    // Guard: only call if it's actually a function (subscription may still be pending)
    if (typeof this._healthUpdateUnsubscribe === 'function') {
      this._healthUpdateUnsubscribe();
      this._healthUpdateUnsubscribe = null;
    } else {
      this._healthUpdateUnsubscribe = null;
    }
    this._healthSubscribePending = false;
    
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
      this._renderTimeout = null;
    }
  }

// === F2 FIX: Health Event Subscription (v0.5.0: await Promise to get unsubscribe fn) ===

  async _subscribeToHealthUpdates() {
    if (!this._hass || !this._hass.connection) {
      console.warn('[Secure Me] Cannot subscribe to health updates: no connection');
      return;
    }

    // Guard against race condition: async subscribe called multiple times
    // before the first await returns
    if (this._healthUpdateUnsubscribe || this._healthSubscribePending) {
      return;
    }
    this._healthSubscribePending = true;

    // subscribeEvents() returns a Promise<unsubscribe_fn>.
    // Must be awaited — storing the raw Promise causes "not a function" on disconnectedCallback.
    try {
      this._healthUpdateUnsubscribe = await this._hass.connection.subscribeEvents(
        (event) => {
          if (event.data && event.data.modules) {
            this._healthStatus = event.data.modules;
            this._healthScore = event.data.health_score || 100;
            this._lastHealthUpdate = event.data.timestamp;

            // PERF: Only queue a full re-render if Testing tab is active or
            // health status actually changed. Status pill is patched in-place separately.
            if (this._activeTab === 'testing' || this._shouldUpdateDisplay(event.data)) {
              this._queueRender();
            }

            // PERF: Update alarm state pill in-place without full re-render
            if (event.data.alarm_state && event.data.alarm_state !== this._alarmState) {
              this._alarmState = event.data.alarm_state;
              if (event.data.countdown != null) this._alarmCountdown = event.data.countdown;
              if (event.data.triggered_by != null) this._alarmTriggeredBy = event.data.triggered_by;
              if (event.data.open_sensors != null) this._alarmOpenSensors = event.data.open_sensors;
              this._updateStatusPills();
            }
          }
        },
        'secure_me_health_updated'
      );
      this._healthSubscribePending = false;
      console.log('[Secure Me] Subscribed to health updates');
    } catch (err) {
      console.warn('[Secure Me] Health subscription failed:', err);
      this._healthUpdateUnsubscribe = null;
      this._healthSubscribePending = false;
    }
  }

  _shouldUpdateDisplay(newHealthData) {
    if (!this._lastHealthUpdate) {
      return true;
    }
    
    const oldHealth = this._healthStatus || {};
    const newHealth = newHealthData.modules || {};
    
    for (const moduleId in newHealth) {
      const oldStatus = oldHealth[moduleId]?.status;
      const newStatus = newHealth[moduleId]?.status;
      
      if (oldStatus !== newStatus) {
        console.log(`[Secure Me F2] Module ${moduleId} status changed: ${oldStatus} -> ${newStatus}`);
        return true;
      }
    }
    
    const oldScore = this._healthScore || 100;
    const newScore = newHealthData.health_score || 100;
    
    if (Math.abs(oldScore - newScore) >= 5) {
      console.log(`[Secure Me F2] Health score changed significantly: ${oldScore} -> ${newScore}`);
      return true;
    }
    
    return false;
  }

  // === Web Socket Helpers ===

  // === Web Socket Helpers ===
  async _callWS(type, data = {}) {
    if (!this._hass) return null;
    try {
      const result = await this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
      // Connection succeeded — hide banner if it was visible
      if (!this._wsConnected) {
        this._wsConnected = true;
        const banner = this.shadowRoot?.getElementById("shell-ws-banner");
        if (banner) banner.style.display = "none";
      }
      return result;
    } catch (err) {
      console.error(`Secure Me WS error (${type}):`, err);
      // Show reconnecting banner for connection-level errors (not app errors)
      const isConnErr = err?.code === "connection_lost" || err?.message?.includes("Connection");
      if (isConnErr && this._wsConnected) {
        this._wsConnected = false;
        const banner = this.shadowRoot?.getElementById("shell-ws-banner");
        if (banner) banner.style.display = "flex";
        // Auto-retry data load after 3s when connection is lost
        setTimeout(() => {
          if (!this._wsConnected) this._loadData();
        }, 3000);
      }
      return null;
    }
  }

  async _loadData() {
    // Invalidate all tab render caches on data reload
    this._sensorsRenderCache = null;
    this._zonesRenderCache   = null;
    this._automationsRenderCache = null;
    // Subscribe to health updates once — called from _loadData which only runs once
    this._subscribeToHealthUpdates();
    // PERF: Split into two phases.
    // Phase 1 — fast: 7 essential calls needed to render any tab immediately.
    // Phase 2 — lazy: health + test results are only needed on the Testing tab.
    const [sensors, zones, users, modules, notifications, automations, state, fakePresence, speakerProfiles] =
      await Promise.all([
        this._callWS("get_sensors"),
        this._callWS("get_zones"),
        this._callWS("get_users"),
        this._callWS("get_modules"),
        this._callWS("get_notifications"),
        this._callWS("get_automations"),
        this._callWS("get_alarm_state"),
        this._callWS("get_fake_presence"),
        this._callWS("get_speaker_profiles"),
      ]);

    if (sensors) this._data.sensors = sensors.sensors || [];
    if (zones) this._data.zones = zones.zones || {};
    if (users) this._data.users = users.users || {};
    if (modules) this._data.modules = modules.modules || {};
    if (notifications) this._data.notifications = notifications.notifications || {};
    if (automations) this._data.automations = automations.automations || {};
    if (state) {
      this._alarmState       = state.state       || "disarmed";
      this._alarmCountdown   = state.countdown   || 0;
      this._alarmTriggeredBy = state.triggered_by || null;
      this._alarmOpenSensors = state.open_sensors || [];
    }
    if (fakePresence) {
      this._data.fakePresence = fakePresence.active || false;
      this._data.homeAloneCameras = fakePresence.home_alone_cameras || [];
    }
    if (speakerProfiles) this._speakerProfiles = speakerProfiles.profiles || [];

    // Render immediately with essential data — no waiting for heavy tabs
    this._queueRender();

    // Phase 2 — lazy: fetch health + test results in background
    this._loadTestingData();
  }

  async _loadTestingData() {
    const [health, testResults, scheduledTests] = await Promise.all([
      this._callWS("get_health_summary"),
      this._callWS("get_test_results"),
      this._callWS("get_scheduled_tests"),
    ]);
    if (health) this._data.health = health;
    if (testResults) this._data.testResults = testResults.results || [];
    if (scheduledTests) this._data.scheduledTests = scheduledTests.scheduled_tests || {};
    // Only re-render if user is already on the testing tab
    if (this._activeTab === "testing") this._queueRender();
  }

  async _loadSpecialData() {
    const [autoActions, fakePresenceV2] = await Promise.all([
      this._callWS("get_auto_actions"),
      this._callWS("get_fake_presence_v2"),
    ]);
    if (autoActions) this._data.autoActions = autoActions.config || {};
    if (fakePresenceV2) this._data.fakePresenceV2 = fakePresenceV2.config || {};
    if (this._activeTab === "special") this._queueRender();
  }

  // === Event ===
  _setTab(tab) {
    this._activeTab = tab;
    // Lazy-load testing data on first visit if not yet fetched
    if (tab === "testing" && !this._data.health && !this._testingDataLoading) {
      this._testingDataLoading = true;
      this._loadTestingData().finally(() => { this._testingDataLoading = false; });
    }
    if (tab === "future" && !this._availableEntities.camera) {
      this._loadEntitiesByDomain('camera').then(() => this._render());
    }
    // v1.5.0: lazy-load floorplan on first visit
    if (tab === "floorplan" && !this._floorplanLoaded && !this._floorplanLoading) {
      this._floorplanLoading = true;
      this._loadFloorplan().finally(() => { this._floorplanLoading = false; });
    }
    // v1.5.0: lazy-load Special Features data on first visit
    if (tab === "special" && this._data.autoActions === null && !this._specialDataLoading) {
      this._specialDataLoading = true;
      this._loadSpecialData().finally(() => { this._specialDataLoading = false; });
    }
    this._render();
  }

  async _toggleSensor(entityId) {
    const sensor = this._data.sensors.find(s => s.entity_id === entityId);
    if (!sensor) return;
    sensor.enabled = !sensor.enabled;

    // Build bulk save object
    const bulk = {};
    for (const s of this._data.sensors) {
      if (s.enabled) {
        bulk[s.entity_id] = { enabled: true, sensor_type: s.sensor_type };
      }
    }
    await this._callWS("save_sensors", { sensors: bulk });
    this._render();
  }

  async _toggleModule(moduleId) {
    const mod = this._data.modules[moduleId];
    if (!mod) return;
    mod.enabled = !mod.enabled;
    if (mod.enabled) this._expandedModule = moduleId;
    await this._callWS("save_module", { module_id: moduleId, config: mod });
    this._modulesRenderCache = null;  // invalidate cache after save
    this._render();
  }

  _expandModule(moduleId) {
    if (this._expandedModule === moduleId) this._expandedModule = null;
    else this._expandedModule = moduleId;
    this._render();
  }

  async _toggleNotification(notifId) {
    const notif = this._data.notifications[notifId];
    if (!notif) return;
    notif.enabled = !notif.enabled;
    await this._callWS("save_notification", { notification_id: notifId, config: notif });
    this._render();
  }

  async _testNotification(notifId) {
    const result = await this._callWS("test_notification", { notification_id: notifId });
    if (result && result.success) {
      this._toast("Testnotifikation sendt!", "success");
    } else {
      this._toast("Kunne ikke sende: " + (result?.error || "Ukendt fejl"), "error");
    }
  }

  async _testAutomation(autoId) {
    const result = await this._callWS("test_automation", { automation_id: autoId });
    if (result && result.success) {
      this._toast("Testautomatisering udført!", "success");
    } else {
      this._toast("Kunne ikke udføre: " + (result?.error || "Ukendt fejl"), "error");
    }
  }

  _setAutoSection(section) { this._autoSection = section; this._render(); }

  // === Shell Architecture (v0.9.0) ===
  // _buildShell() is called ONCE from connectedCallback.
  // It writes the static chrome (style, sidebar, nav, main placeholder) to shadowRoot.
  // _render() then patches ONLY main-content.innerHTML — no CSS reparse, no full DOM teardown.

  connectedCallback() {
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
    }
  }

  _buildShell() {
    this.shadowRoot.innerHTML = `
      <style>${panelStyles}</style>

      <!-- TOP BAR — never scrolls -->
      <div class="panel-topbar">
        <div class="sm-header">
          <div class="sm-header-icon">${icon("shield")}</div>
          <div class="sm-header-text">
            <div class="sm-header-title">Secure Me</div>
            <div class="sm-header-sub">v${VERSION} by KingPainter</div>
          </div>
          <div class="sm-header-pill disarmed" id="shell-status-pill">
            <span class="pill-dot"></span>
            <span id="shell-status-text">Deaktiveret</span>
          </div>
          <div id="shell-open-badge" style="display:none;align-items:center;
               padding:4px 10px;border-radius:16px;font-size:11px;font-weight:600;
               background:var(--sm-warning-dim);color:var(--sm-warning);
               border:1px solid rgba(245,158,11,0.25);white-space:nowrap"></div>
        </div>
        <div class="sm-tabs" id="shell-nav-tabs">
          ${TABS.map(t => `
            <button class="sm-tab ${this._activeTab === t.key ? "active" : ""}"
                    data-tab="${t.key}">
              <span class="nav-icon">${icon(t.icon)}</span>
              <span class="tab-label">${t.label}</span>
              ${t.badge ? `<span style="font-size:9px;padding:1px 5px;border-radius:4px;background:rgba(255,255,255,0.08);color:var(--sm-text-tertiary)">${t.badge}</span>` : ""}
            </button>
          `).join("")}
        </div>
      </div>

      <!-- WS RECONNECT BANNER — shown when connection is lost -->
      <div id="shell-ws-banner" style="display:none" class="sm-ws-banner">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
        Reconnecting to Home Assistant...
      </div>

      <!-- MAIN CONTENT — patched by _render() -->
      <div class="panel-scroll" id="shell-main"></div>

      <!-- DIALOG MOUNT POINT — managed by _render() -->
      <div id="shell-dialog-mount"></div>

      <!-- TOAST CONTAINER -->
      <div class="sm-toast-container" id="shell-toast"></div>
    `;

    this._attachShellListeners();
  }

  // Attach nav/drawer listeners once on the shell — these never need re-binding.
  _attachShellListeners() {
    const root = this.shadowRoot;
    // Topbar tab navigation
    root.querySelectorAll(".sm-tab[data-tab]").forEach(btn => {
      btn.addEventListener("click", () => this._setTab(btn.dataset.tab));
    });
  }

  // Update nav active state without full re-render
  _updateNavActive() {
    this.shadowRoot.querySelectorAll(".sm-tab[data-tab]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === this._activeTab);
    });
  }

  // === Debounced render — coalesces rapid back-to-back updates into one paint ===
  // Uses a 50ms timeout so multiple state changes (e.g. hass update + health event)
  // only trigger a single _render() call instead of causing visual flicker.
  _queueRender() {
    if (this._renderTimeout) clearTimeout(this._renderTimeout);
    this._renderTimeout = setTimeout(() => {
      this._renderTimeout = null;
      this._render();
    }, 50);
  }

  _fpFlyoutActive() {
    return !!(this._fpActiveFlyout && this._fpActiveFlyout.style.display === "block");
  }

  _fpSnapshotForUndo() {
    const fp = this._data.floorplan;
    if (!fp) return;
    this._fpUndoStack.push({
      rooms:    JSON.parse(JSON.stringify(fp.rooms    || {})),
      openings: JSON.parse(JSON.stringify(fp.openings || [])),
    });
    if (this._fpUndoStack.length > 20) this._fpUndoStack.shift();
  }

  _fpUndo() {
    if (!this._fpUndoStack.length) { this._toast("Ingen handlinger at fortryde", "info"); return; }
    const snap = this._fpUndoStack.pop();
    if (!this._data.floorplan) return;
    this._data.floorplan.rooms    = snap.rooms;
    this._data.floorplan.openings = snap.openings;
    this._floorplanSelectedRoom    = null;
    this._floorplanSelectedOpening = null;
    this._floorplanDrawing         = null;
    this._render();
    this._fpSaveRooms();
    this._toast("Fortryd", "success");
  }

  _fpAttachKeyboard() {
    if (this._fpKeyboardCleanup) return;
    const handler = e => {
      const tag = (e.target?.tagName || "").toLowerCase();
      if (["input","textarea","select"].includes(tag)) return;
      if (e.key === "Escape") {
        e.preventDefault();
        if (this._floorplanDrawing) { this._floorplanDrawing = null; this._render(); }
        else if (this._floorplanSelectedRoom || this._floorplanSelectedOpening !== null) {
          this._floorplanSelectedRoom = null; this._floorplanSelectedOpening = null; this._render();
        } else { this._floorplanEditMode = false; this._floorplanSelectedRoom = null; this._fpDetachKeyboard(); this._render(); }
        return;
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        if (this._floorplanSelectedRoom) {
          e.preventDefault(); this._fpSnapshotForUndo();
          delete this._data.floorplan.rooms[this._floorplanSelectedRoom];
          this._floorplanSelectedRoom = null; this._render(); this._fpSaveRooms(); return;
        }
        if (this._floorplanSelectedOpening !== null) {
          e.preventDefault(); this._fpSnapshotForUndo();
          this._data.floorplan.openings.splice(this._floorplanSelectedOpening, 1);
          this._floorplanSelectedOpening = null; this._render(); this._fpSaveRooms(); return;
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "z") { e.preventDefault(); this._fpUndo(); return; }
      if (!e.ctrlKey && !e.metaKey && !e.altKey) {
        if (e.key === "r" || e.key === "R") { this._floorplanDrawTool = "rect";    this._floorplanDrawing = null; this._render(); }
        else if (e.key === "p" || e.key === "P") { this._floorplanDrawTool = "polygon"; this._floorplanDrawing = null; this._render(); }
        else if (e.key === "o" || e.key === "O") { this._floorplanDrawTool = "opening"; this._floorplanDrawing = null; this._render(); }
      }
    };
    document.addEventListener("keydown", handler);
    this._fpKeyboardCleanup = () => document.removeEventListener("keydown", handler);
  }

  _fpDetachKeyboard() {
    if (this._fpKeyboardCleanup) { this._fpKeyboardCleanup(); this._fpKeyboardCleanup = null; }
  }

  // === Toast notifications (v1.4.3) ===
  // Show ephemeral status messages in the bottom-right toast container.
  // Types: 'success', 'error', 'warning', 'info'. Default: 'info'.
  _toast(message, type = "info") {
    const root = this.shadowRoot;
    if (!root) return;
    const container = root.getElementById("shell-toast");
    if (!container) return;

    const el = document.createElement("div");
    el.className = `sm-toast ${type}`;
    el.textContent = message;
    container.appendChild(el);

    // Auto-dismiss after 4 seconds with fade-out animation
    setTimeout(() => {
      el.classList.add("fading");
      setTimeout(() => el.remove(), 250);
    }, 4000);
  }

  // === Confirm dialog (v1.4.3) ===
  // Returns Promise<boolean>. Renders a styled overlay with OK/Cancel
  // buttons; resolves true on OK, false on Cancel or backdrop click.
  // Replaces window.confirm() which is blocking and unstyled.
  _confirm(message, title = "Bekræft") {
    return new Promise((resolve) => {
      const root = this.shadowRoot;
      if (!root) { resolve(false); return; }

      const overlay = document.createElement("div");
      overlay.style.cssText =
        "position:fixed;inset:0;background:rgba(0,0,0,0.6);" +
        "z-index:25000;display:flex;align-items:center;justify-content:center;" +
        "animation:fadeIn 0.15s ease;";

      const dialog = document.createElement("div");
      dialog.style.cssText =
        "background:var(--sm-card-bg, #1f1f23);border:1px solid var(--sm-border, #333);" +
        "border-radius:12px;padding:24px;max-width:420px;width:90%;" +
        "box-shadow:0 10px 40px rgba(0,0,0,0.5);";

      const titleEl = document.createElement("div");
      titleEl.style.cssText =
        "font-size:16px;font-weight:600;color:var(--sm-text);margin-bottom:8px;";
      titleEl.textContent = title;

      const msgEl = document.createElement("div");
      msgEl.style.cssText =
        "font-size:14px;color:var(--sm-text-dim, #aaa);margin-bottom:20px;line-height:1.5;";
      msgEl.textContent = message;

      const btnRow = document.createElement("div");
      btnRow.style.cssText = "display:flex;gap:8px;justify-content:flex-end;";

      const cancelBtn = document.createElement("button");
      cancelBtn.className = "sm-btn ghost";
      cancelBtn.textContent = "Annuller";
      cancelBtn.style.cssText = "padding:8px 16px;";

      const okBtn = document.createElement("button");
      okBtn.className = "sm-btn primary";
      okBtn.textContent = "OK";
      okBtn.style.cssText = "padding:8px 16px;";

      const cleanup = (result) => {
        overlay.remove();
        resolve(result);
      };

      cancelBtn.addEventListener("click", () => cleanup(false));
      okBtn.addEventListener("click", () => cleanup(true));
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) cleanup(false);
      });
      // ESC = cancel
      const onKey = (e) => {
        if (e.key === "Escape") {
          document.removeEventListener("keydown", onKey);
          cleanup(false);
        } else if (e.key === "Enter") {
          document.removeEventListener("keydown", onKey);
          cleanup(true);
        }
      };
      document.addEventListener("keydown", onKey);

      btnRow.append(cancelBtn, okBtn);
      dialog.append(titleEl, msgEl, btnRow);
      overlay.appendChild(dialog);
      root.appendChild(overlay);
      okBtn.focus();
    });
  }

  // === Render — patches main-content only ===
  _render() {
    // Guard: shell must exist before we can patch it
    if (!this._shellBuilt) {
      this._buildShell();
      this._shellBuilt = true;
    }

    const mainContent = this.shadowRoot.getElementById("shell-main");
    if (!mainContent) return;

    // Save scroll position
    const scrollTop = mainContent.scrollTop;

    // Patch tab content.
    // Skip rebuild hvis sensor-flyout er aaben -- det ville rive inspector ned.
    if (this._fpFlyoutActive()) return;
    mainContent.innerHTML = this._renderTab();

    // Update nav active classes (no DOM teardown)
    this._updateNavActive();

    // Update status pills in-place
    this._updateStatusPills();

    // Manage dialog: inject or remove from mount point.
    // IMPORTANT: Never rebuild an open dialog — it loses focus and causes blinking.
    // Only update the dialog mount if:
    //   1. A dialog needs to be shown that isn't currently shown, OR
    //   2. The dialog should be closed (no _showDialog)
    const dialogMount = this.shadowRoot.getElementById("shell-dialog-mount");
    if (dialogMount) {
      const currentlyShown = dialogMount.dataset.currentDialog || '';
      const wantDialog = this._showDialog || '';

      // Only rebuild if the dialog type changes or is being closed
      if (currentlyShown !== wantDialog) {
        const dialogHtml = wantDialog === 'camera'  ? this._renderCameraDialog()
          : wantDialog === 'lock'    ? this._renderLockDialog()
          : wantDialog === 'climate' ? this._renderClimateDialog()
          : wantDialog === 'siren'   ? this._renderSirenDialog()
          : wantDialog === 'lights'  ? this._renderLightsDialog()
          : wantDialog === 'tts'          ? this._renderTTSDialog()
          : wantDialog === 'notification'  ? this._renderNotificationDialog()
          : wantDialog === 'user'         ? this._renderUserDialog()
          : wantDialog === 'sched-test'   ? this._renderSchedDialog()
          : wantDialog === 'zone'         ? this._renderZoneDialog()
          : '';
        dialogMount.innerHTML = dialogHtml;
        dialogMount.dataset.currentDialog = wantDialog;
        // Attach dialog-specific listeners once, right after building the dialog.
        // These must NOT be in _attachTabListeners() to avoid accumulation.
        if (wantDialog) this._attachDialogListeners();
      }
    }

    this._attachTabListeners();

    // Restore scroll position
    requestAnimationFrame(() => {
      const m = this.shadowRoot.getElementById("shell-main");
      if (m && scrollTop > 0) m.scrollTop = scrollTop;
    });
  }

  _renderTab() {
    // Show skeleton cards on first load before data arrives
    if (!this._data.sensors || !this._data.zones) {
      return `
        <div style="padding:0 0 16px">
          <div class="section-header"><h3 class="section-title">Indlæser...</h3></div>
          ${[1,2,3].map(() => `
            <div class="sm-card" style="margin-bottom:10px;height:72px" class="sm-skeleton">
              <div class="sm-skeleton" style="height:72px;border-radius:8px"></div>
            </div>
          `).join("")}
        </div>
      `;
    }
    switch (this._activeTab) {
      case "sensors": return this._renderSensors();
      case "zones": return this._renderZones();
      case "users": return this._renderUsers();
      case "modules": return this._renderModules();
      case "floorplan": return this._renderFloorplan();
      case "automations": return this._renderAutomations();
      case "testing": return this._renderTesting();
      case "special": return this._renderSpecialFeatures();
      case "future": return this._renderFuture();
      default: return "";
    }
  }

  // ===
  // TAB: SENSORS
  // ===
  _renderSensors() {
    // BUG FIX: cache key referenced `this._data.fakePresenceActive`, a field
    // that is never set anywhere (the real field is `this._data.fakePresence`,
    // only ever read into a local const below). Because that key component
    // was always `undefined`, toggling Fake Presence never changed the cache
    // key, so this tab kept serving the stale cached HTML and silently
    // reverted the toggle's visual state right after it was clicked.
    const sCacheKey = JSON.stringify({ s: this._data.sensors, fp: this._data.fakePresence, env: this._envExpanded, hidden: this._hiddenSensorsExpanded });
    if (this._sensorsRenderKey === sCacheKey && this._sensorsRenderCache) return this._sensorsRenderCache;
    const sensors = this._data.sensors || [];
    const envSensors    = sensors.filter(s => s.is_environmental && !s.env_unmarked);
    const normalSensors = sensors.filter(s => !s.is_environmental || s.env_unmarked);
    const enabled       = normalSensors.filter(s => s.enabled && !s.auto_hidden);
    const disabled      = normalSensors.filter(s => !s.enabled && !s.auto_hidden);
    const autoHidden    = normalSensors.filter(s => s.auto_hidden);
    const typeLabels    = { contact: "Kontakt", motion: "Bevægelse", presence: "Tilstedeværelse", environmental: "Miljø" };

    // v1.5.0: group by HA area/room (falls back to 'Andet' when unassigned).
    // Areas sorted alphabetically (da locale); 'Andet' is always pushed last
    // since it's a catch-all, not a real room. Sensors within each area are
    // sorted alphabetically by name.
    const groupByArea = (list) => {
      const groups = {};
      for (const s of list) {
        const area = s.area || "Andet";
        if (!groups[area]) groups[area] = [];
        groups[area].push(s);
      }
      const areaNames = Object.keys(groups).sort((a, b) => {
        if (a === "Andet") return 1;
        if (b === "Andet") return -1;
        return a.localeCompare(b, "da");
      });
      for (const area of areaNames) {
        groups[area].sort((a, b) => a.name.localeCompare(b.name, "da"));
      }
      return areaNames.map(area => ({ area, sensors: groups[area] }));
    };

    const renderSensorRow = (s) => `
      <div class="sm-list-row ${s.enabled ? "" : "disabled"}">
        <div class="sm-list-row-top">
          <span class="sm-list-row-name">${s.name}</span>
          <span class="badge ${s.sensor_type}" style="flex-shrink:0">${typeLabels[s.sensor_type] || s.sensor_type}</span>
          ${!s.enabled ? `<button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;color:var(--sm-danger);flex-shrink:0"
                  data-hide-sensor="${s.entity_id}" title="Skjul denne sensor">${icon("trash")}</button>` : ''}
          <button class="sm-checkbox ${s.enabled ? "checked" : ""}"
                  data-sensor="${s.entity_id}"
                  style="flex-shrink:0">
            ${s.enabled ? icon("check") : ""}
          </button>
        </div>
        <div class="sm-list-row-eid">${s.entity_id}</div>
        ${s.enabled ? `
          <div style="display:flex;align-items:center;gap:6px;margin-top:4px">
            <button class="sm-btn ghost sm ${s.allow_open ? 'active' : ''}"
                    data-allow-open="${s.entity_id}"
                    title="Allow Open: sensor ignoreres ved arming (permanent bypass)"
                    style="padding:3px 8px;font-size:11px;${s.allow_open ? 'color:var(--sm-warning,#f59e0b);border-color:var(--sm-warning,#f59e0b)' : 'color:var(--sm-text-tertiary)'}">
              ${icon("unlock")} Allow Open
            </button>
            ${s.allow_open ? `<span style="font-size:11px;color:var(--sm-warning,#f59e0b)">Altid bypassed ved arming</span>` : ''}
          </div>
        ` : ''}
      </div>
    `;

    const renderAreaGroup = (areaGroups, emptyMessage) => {
      if (areaGroups.length === 0) {
        return `<div style="padding:20px;text-align:center;color:var(--sm-text-tertiary);font-size:13px">${emptyMessage}</div>`;
      }
      return areaGroups.map(({ area, sensors: areaSensors }) => `
        <div class="sm-area-group">
          <div style="padding:6px 16px;font-size:11px;font-weight:600;color:var(--sm-text-tertiary);
                      text-transform:uppercase;letter-spacing:0.3px;background:rgba(255,255,255,0.02)">
            ${area}
          </div>
          ${areaSensors.map(s => renderSensorRow(s)).join("")}
        </div>
      `).join("");
    };

    const renderEnvRow = (s) => `
      <div style="display:flex;flex-direction:column;gap:4px;
                  padding:10px 16px;border-bottom:1px solid var(--sm-border)">
        <div style="font-size:14px;font-weight:500">${s.name}</div>
        <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:'DM Mono',monospace;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${s.entity_id}</div>
        <div style="display:flex;align-items:center;gap:8px;margin-top:2px">
          <span class="badge environmental">Krævet</span>
          <button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;color:var(--sm-text-tertiary)"
                  data-unmark-env="${s.entity_id}" title="Fjern forkert miljøklassificering">
            Fjern
          </button>
        </div>
      </div>
    `;

    const renderHiddenRow = (s) => `
      <div style="display:grid;grid-template-columns:1fr auto auto;align-items:center;
                  padding:8px 16px;border-bottom:1px solid var(--sm-border);opacity:0.65">
        <div>
          <div style="font-size:13px;font-weight:400;color:var(--sm-text-secondary)">${s.name}</div>
          <div style="font-size:10px;color:var(--sm-text-tertiary);font-family:'DM Mono',monospace">${s.entity_id}</div>
        </div>
        <span class="badge" style="background:rgba(255,255,255,0.06);color:var(--sm-text-tertiary)">Automatisk skjult</span>
        <button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;margin-left:8px"
                data-hide-sensor="${s.entity_id}" title="Udeluk denne sensor permanent">
          Exclude
        </button>
      </div>
    `;

    const fakePresenceActive = this._data.fakePresence || false;

    const __html = `
      <div class="section-header">
        <div>
          <h3 class="section-title">Tilgængelige sensorer</h3>
          <p class="section-subtitle">${enabled.length} af ${normalSensors.filter(s=>!s.auto_hidden).length} almindelige sensorer aktive</p>
        </div>
        <span class="badge accent">${enabled.length} aktive</span>
      </div>

      <div class="sm-card" style="padding:16px;margin-bottom:16px;border-color:${fakePresenceActive ? 'var(--sm-warning)' : 'var(--sm-border)'}">
        <div style="display:flex;align-items:center;gap:14px">
          <div style="width:38px;height:38px;border-radius:10px;background:${fakePresenceActive ? 'var(--sm-warning-dim)' : 'rgba(255,255,255,0.06)'};
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${fakePresenceActive ? 'var(--sm-warning)' : 'var(--sm-text-tertiary)'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;color:${fakePresenceActive ? 'var(--sm-warning)' : 'var(--sm-text)'}">
              Fake Presence
            </div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              ${fakePresenceActive
                ? 'Active &mdash; automatic arming is blocked'
                : 'Blocks automatic arming while you are nearby but away from home'}
            </div>
          </div>
          <button class="sm-toggle ${fakePresenceActive ? 'on' : ''}" data-action="toggle-fake-presence">
            <div class="dot"></div>
          </button>
        </div>
        ${fakePresenceActive ? `
          <div style="margin-top:12px;padding:10px 12px;border-radius:8px;background:var(--sm-warning-dim);
                      border:1px solid rgba(255,159,10,0.2);font-size:12px;color:var(--sm-warning)">
            Fake Presence is ON. The alarm will not auto-arm while this is active.
            Remember to turn it off when you leave.
          </div>
        ` : ''}
      </div>

      ${envSensors.length > 0 ? `
        <div class="sm-card no-pad" style="overflow:hidden;margin-bottom:16px;border-color:rgba(255,59,48,0.3)">
          <div class="collapsible-header ${this._envExpanded ? 'expanded' : ''}"
               data-action="toggle-env-sensors"
               style="background:rgba(255,59,48,0.08);border-bottom:${this._envExpanded ? '1px solid rgba(255,59,48,0.2)' : 'none'};padding:10px 16px;margin:0;display:flex;flex-direction:column;align-items:flex-start;gap:4px">
            <div style="display:flex;justify-content:space-between;align-items:center;width:100%">
              <span style="display:flex;align-items:center;gap:6px;color:var(--sm-danger)">
                ${icon("warn")}
                <span style="font-weight:500">Miljøsensorer &mdash; Altid aktive (${envSensors.length})</span>
              </span>
              <span class="chevron">${icon("chevron")}</span>
            </div>
            ${!this._envExpanded ? `
              <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:2px;padding-left:22px">
                ${envSensors.map(s => `<span style="font-size:11px;color:var(--sm-text-secondary);background:rgba(255,59,48,0.10);border:1px solid rgba(255,59,48,0.18);border-radius:4px;padding:1px 6px">${s.name}</span>`).join("")}
              </div>
            ` : `
              <span style="font-size:11px;color:var(--sm-text-secondary);padding-left:2px">Notifikationer kan ikke deaktiveres</span>
            `}
          </div>
          <div class="collapsible-body ${this._envExpanded ? 'expanded' : ''}">
            ${envSensors.map(s => renderEnvRow(s)).join("")}
          </div>
        </div>
      ` : ""}

      <div class="sensor-two-col">
        <div class="sm-card no-pad" style="overflow:hidden">
          <div class="sm-list-header" style="display:flex;justify-content:space-between;align-items:center">
            <span>Aktive (${enabled.length})</span><span>Type / Til</span>
          </div>
          ${renderAreaGroup(groupByArea(enabled), "Ingen sensorer aktiveret endnu.")}
        </div>

        <div class="sm-card no-pad" style="overflow:hidden">
          <div class="sm-list-header" style="display:flex;justify-content:space-between;align-items:center">
            <span>Inactive (${disabled.length})</span><span>Type / On</span>
          </div>
          ${renderAreaGroup(groupByArea(disabled), "All sensors are active.")}
        </div>
      </div>

      ${autoHidden.length > 0 ? `
        <div class="sm-card no-pad" style="overflow:hidden;margin-top:16px;border-color:rgba(255,255,255,0.06)">
          <div class="collapsible-header ${this._hiddenSensorsExpanded ? 'expanded' : ''}"
               data-action="toggle-hidden-sensors"
               style="padding:12px 16px;margin:0">
            <span style="font-size:12px;color:var(--sm-text-secondary)">
              ${autoHidden.length} auto-hidden irrelevant sensors (network devices, TVs, etc.)
            </span>
            <span class="chevron">${icon("chevron")}</span>
          </div>
          <div class="collapsible-body ${this._hiddenSensorsExpanded ? 'expanded' : ''}">
            ${autoHidden.map(s => renderHiddenRow(s)).join("")}
          </div>
        </div>
      ` : ""}

      <div class="info-card warning" style="margin-top:16px">
        <span style="color:var(--sm-warning);display:flex;align-items:center">${icon("warn")}</span>
        <div>
          <div class="info-title" style="color:var(--sm-warning)">Minimumskrav</div>
          <div class="info-text">
            The alarm requires at least 1 contact sensor AND 1 motion sensor to be activated.
            Presence sensors are optional but recommended.
          </div>
        </div>
      </div>
    `;
    this._sensorsRenderKey = sCacheKey; this._sensorsRenderCache = __html; return __html;
  }

  // ===
  // TAB: ZONES
  // ===
  _renderZones() {
    const zCacheKey = JSON.stringify({ z: this._data.zones, s: this._data.sensors });
    if (this._zonesRenderKey === zCacheKey && this._zonesRenderCache) return this._zonesRenderCache;
    const zones = this._data.zones || {};
    const enabledSensors = (this._data.sensors || []).filter(s => s.enabled);
    const typeLabels = { entry: "Indgang/Udgang", interior: "Indendørs", perimeter: "Perimeter", instant: "Øjeblikkelig" };
    const modeColors = { away: "var(--sm-danger)", home: "var(--sm-accent)", night: "var(--sm-blue)", vacation: "var(--sm-purple)", home_alone: "var(--sm-green)" };

    const __zhtml = `
      <div class="section-header">
        <h3 class="section-title">Zoner</h3>
        <button class="sm-btn primary sm" data-action="add-zone">
          ${icon("plus")} Tilføj zone
        </button>
      </div>

      <div class="zone-grid">
        ${Object.entries(zones).map(([id, z]) => {
          const armModes = z.arm_modes || z.modes || ["away"];
          return `
          <div class="sm-card zone-card" style="padding:16px;
               border-color:${z.enabled ? "var(--sm-" + (z.type === "entry" ? "warning" : z.type === "perimeter" ? "danger" : "blue") + ")" : "var(--sm-border)"};
               opacity:${z.enabled ? 1 : 0.5}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div>
                <div style="font-size:15px;font-weight:600">${z.name || id}</div>
                <span class="badge ${z.type}">${typeLabels[z.type] || z.type}</span>
              </div>
              <div style="display:flex;gap:8px;align-items:center">
                <button class="sm-btn default sm" data-edit-zone="${id}" title="Rediger zone" style="font-size:11px;padding:4px 10px">Rediger</button>
                <button class="sm-btn ghost sm" data-delete-zone="${id}" title="Slet zone">${icon("trash")}</button>
                <button class="sm-toggle ${z.enabled ? "on" : ""}" data-zone-toggle="${id}">
                  <div class="dot"></div>
                </button>
              </div>
            </div>
            <div style="margin-top:10px;font-size:12px;color:var(--sm-text-secondary)">
              ${(z.sensors || []).length} sensors assigned
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px">
              ${armModes.map(m => `
                <span style="font-size:10px;font-weight:600;padding:2px 8px;border-radius:10px;
                             background:${modeColors[m] || "var(--sm-primary)"}22;
                             color:${modeColors[m] || "var(--sm-primary)"}">
                  ${m}
                </span>
              `).join("")}
            </div>
          </div>
        `}).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">Ingen zoner oprettet endnu. Klik "Tilføj zone" for at starte.</div>'}
      </div>

    `;
    this._zonesRenderKey = zCacheKey; this._zonesRenderCache = __zhtml; return __zhtml;
  }

  _renderZoneDialog() {
    const enabledSensors = (this._data.sensors || []).filter(s => s.enabled);
    const temp = this._tempConfig || {};
    const isEdit = !!temp._zoneId;
    const armModes = temp.arm_modes || ['away'];
    const modeColors = { away: 'var(--sm-danger)', home: 'var(--sm-accent)', night: 'var(--sm-blue)', vacation: 'var(--sm-purple)', home_alone: 'var(--sm-green)' };
    const modeDesc = {
      away: 'All sensors active',
      home: 'Perimeter only, no interior',
      night: 'Perimeter + selected interior',
      vacation: 'Like Away with extra alerts',
      home_alone: 'Kids home alone — cameras on, doors notify',
    };

    return '<div class="config-dialog-overlay">' +
      '<div class="config-dialog">' +
        '<div class="dialog-header">' +
          icon('shield') +
          '<div class="dialog-title">' + (isEdit ? 'Rediger zone' : 'Tilføj zone') + '</div>' +
          '<button class="dialog-close" data-action="close-dialog">' + icon("close") + '</button>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Zonenavn</label>' +
          '<input type="text" class="form-input" id="zone-name" placeholder="f.eks. Entredør, Stue" value="' + (temp.name || '') + '">' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Zonetype</label>' +
          '<select class="form-select" id="zone-type">' +
            '<option value="entry"' + (temp.type === 'entry' ? ' selected' : '') + '>Entry/Exit — Doors with delay</option>' +
            '<option value="interior"' + (temp.type === 'interior' ? ' selected' : '') + '>Interior — Motion sensors</option>' +
            '<option value="perimeter"' + (temp.type === 'perimeter' ? ' selected' : '') + '>Perimeter — Instant windows</option>' +
            '<option value="instant"' + (temp.type === 'instant' ? ' selected' : '') + '>Instant — No delay trigger</option>' +
          '</select>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Aktiv i tilkoblingstilstande</label>' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">' +
            ['away', 'home', 'night', 'vacation', 'home_alone'].map(m => {
              const checked = armModes.includes(m);
              const c = modeColors[m];
              return '<label style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px;cursor:pointer;' +
                'background:' + (checked ? c + '18' : 'rgba(255,255,255,0.04)') + ';' +
                'border:1px solid ' + (checked ? c + '66' : 'var(--sm-border)') + ';font-size:12px">' +
                '<input type="checkbox" class="zone-mode-cb" value="' + m + '"' + (checked ? ' checked' : '') + '>' +
                '<div>' +
                  '<div style="font-weight:600;color:' + (checked ? c : 'var(--sm-text)') + '">' + (m === 'home_alone' ? 'Home Alone' : m.charAt(0).toUpperCase() + m.slice(1)) + '</div>' +
                  '<div style="font-size:10px;color:var(--sm-text-tertiary)">' + modeDesc[m] + '</div>' +
                '</div>' +
              '</label>';
            }).join('') +
          '</div>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Tildel sensorer (' + enabledSensors.length + ' tilgængelige)</label>' +
          (enabledSensors.length > 0 ?
            enabledSensors.map(s =>
              '<label style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px;cursor:pointer;border:1px solid var(--sm-border);margin-bottom:6px;font-size:13px">' +
                '<input type="checkbox" class="zone-sensor-cb" value="' + s.entity_id + '"' + ((temp.sensors || []).includes(s.entity_id) ? ' checked' : '') + '>' +
                '<span style="flex:1">' + s.name + '</span>' +
                '<span style="font-size:10px;color:var(--sm-text-tertiary);margin-right:4px">' + s.entity_id + '</span>' +
                '<span class="badge ' + s.sensor_type + '" style="font-size:10px">' + s.sensor_type + '</span>' +
              '</label>'
            ).join('') :
            '<div style="padding:12px;text-align:center;color:var(--sm-text-tertiary);font-size:12px">Ingen sensorer aktiveret. Aktivér sensorer under Sensorer-fanen først.</div>'
          ) +
        '</div>' +

        // v1.4.3: Per-sensor auto-bypass per arm mode.
        // Bypass is a sensor property (stored globally on the sensor), but
        // edited here in the zone dialog because that's where the user
        // already manages mode-specific behaviour. The dropdown below shows
        // every sensor currently assigned to this zone and lets you tick
        // which arm modes silently bypass the sensor when it's open at arm
        // time. Empty = sensor must be closed before that mode can arm.
        ((temp.sensors || []).length > 0 ? (
          '<div class="form-group" style="border-top:1px solid var(--sm-border);padding-top:16px;margin-top:4px">' +
            '<label class="form-label">' + icon('shield') + ' Auto-Bypass per Sensor' + '</label>' +
            '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:10px">' +
              'For each sensor, tick the arm modes where it should silently bypass if open at arm time. Empty = blocks arming. (Saved on the sensor itself, shared across zones.)' +
            '</div>' +
            (temp.sensors || []).map(eid => {
              const s = (this._data.sensors || []).find(x => x.entity_id === eid);
              const sName = s ? s.name : eid;
              const sType = s ? s.sensor_type : '';
              const currentModes = (s && Array.isArray(s.auto_bypass_modes)) ? s.auto_bypass_modes : [];
              const allModes = ['away', 'home', 'night', 'vacation', 'home_alone'];
              const modeLabel = { away: 'Away', home: 'Home', night: 'Night', vacation: 'Vacation', home_alone: 'Home Alone' };
              return '<div style="padding:10px 12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:6px">' +
                '<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">' +
                  '<span class="badge ' + sType + '" style="font-size:10px">' + sType + '</span>' +
                  '<span style="font-size:13px;font-weight:600">' + sName + '</span>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:4px">' +
                  allModes.map(m => {
                    const checked = currentModes.includes(m);
                    const c = modeColors[m];
                    return '<label style="display:flex;align-items:center;justify-content:center;gap:4px;padding:6px 4px;border-radius:6px;cursor:pointer;font-size:11px;' +
                      'background:' + (checked ? c + '18' : 'rgba(255,255,255,0.04)') + ';' +
                      'border:1px solid ' + (checked ? c + '66' : 'var(--sm-border)') + ';' +
                      'color:' + (checked ? c : 'var(--sm-text-secondary)') + '">' +
                      '<input type="checkbox" class="sensor-bypass-cb" data-sensor-eid="' + eid + '" data-mode="' + m + '"' + (checked ? ' checked' : '') + ' style="margin:0">' +
                      '<span>' + modeLabel[m] + '</span>' +
                    '</label>';
                  }).join('') +
                '</div>' +
              '</div>';
            }).join('') +
          '</div>'
        ) : '') +

        // Home Alone per-sensor config — only shown when home_alone mode is selected
        (armModes.includes('home_alone') && (temp.sensors || []).length > 0 ? (
          '<div class="form-group" style="border-top:1px solid var(--sm-border);padding-top:16px;margin-top:4px">' +
            '<label class="form-label" style="color:var(--sm-green)">' +
              icon('user') + ' Home Alone — Per-Sensor Config' +
            '</label>' +
            '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:10px">' +
              'Configure camera snapshot and TTS speaker for each door sensor when Home Alone mode is active.' +
            '</div>' +
            (temp.sensors || []).map(eid => {
              const s = (this._data.sensors || []).find(x => x.entity_id === eid);
              const sName = s ? s.name : eid;
              const sType = s ? s.sensor_type : '';
              const haCfg = (temp.home_alone_sensor_config || {})[eid] || {};
              const availCams = this._availableEntities.camera || [];
              const availSpeakers = this._availableEntities.media_player || [];
              return '<div style="padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:8px">' +
                '<div style="display:flex;align-items:center;gap:6px;margin-bottom:10px">' +
                  '<span class="badge ' + sType + '" style="font-size:10px">' + sType + '</span>' +
                  '<span style="font-size:13px;font-weight:600">' + sName + '</span>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">' +
                  '<div>' +
                    '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:4px">Camera (snapshot)</div>' +
                    '<select class="form-select ha-sensor-cam" data-sensor-eid="' + eid + '" style="font-size:12px">' +
                      '<option value="">-- None --</option>' +
                      availCams.map(c => '<option value="' + c.entity_id + '"' + (haCfg.home_alone_camera === c.entity_id ? ' selected' : '') + '>' + (c.name || c.entity_id) + '</option>').join('') +
                    '</select>' +
                  '</div>' +
                  '<div>' +
                    '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:4px">TTS-højtaler</div>' +
                    '<select class="form-select ha-sensor-speaker" data-sensor-eid="' + eid + '" style="font-size:12px">' +
                      '<option value="">-- None --</option>' +
                      availSpeakers.map(sp => '<option value="' + sp.entity_id + '"' + (haCfg.home_alone_tts_speaker === sp.entity_id ? ' selected' : '') + '>' + (sp.name || sp.entity_id) + '</option>').join('') +
                    '</select>' +
                  '</div>' +
                '</div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
                  '<div>' +
                    '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:4px">Action 1 text</div>' +
                    '<input type="text" class="form-input ha-sensor-action1" data-sensor-eid="' + eid + '"' +
                      ' style="font-size:12px" placeholder="Where are you going?"' +
                      ' value="' + (haCfg.home_alone_action_1 || '') + '">' +
                  '</div>' +
                  '<div>' +
                    '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:4px">Action 2 text</div>' +
                    '<input type="text" class="form-input ha-sensor-action2" data-sensor-eid="' + eid + '"' +
                      ' style="font-size:12px" placeholder="Luk venligst døren."' +
                      ' value="' + (haCfg.home_alone_action_2 || '') + '">' +
                  '</div>' +
                '</div>' +
              '</div>';
            }).join('') +
          '</div>'
        ) : '') +

        '<div class="dialog-footer">' +
          '<button class="btn-dialog cancel" data-action="close-dialog">Annuller</button>' +
          '<button class="btn-dialog save" data-action="save-zone">Gem zone</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  async _saveZone() {
    const root = this.shadowRoot;
    const name = root.querySelector('#zone-name')?.value?.trim();
    const type = root.querySelector('#zone-type')?.value || 'entry';
    const armModes = Array.from(root.querySelectorAll('.zone-mode-cb:checked')).map(cb => cb.value);
    const sensors = Array.from(root.querySelectorAll('.zone-sensor-cb:checked')).map(cb => cb.value);

    if (!name) { this._toast('Indtast et zonenavn.', 'warning'); return; }
    if (armModes.length === 0) { this._toast('Vælg mindst én tilkoblingstilstand.', 'warning'); return; }

    const temp = this._tempConfig || {};
    const zoneId = temp._zoneId || ('zone_' + Date.now());

    // Collect Home Alone per-sensor config from dialog inputs (only if home_alone mode is active)
    const homeAloneSensorConfig = {};
    if (armModes.includes('home_alone')) {
      const root2 = this.shadowRoot;
      root2.querySelectorAll('.ha-sensor-cam').forEach(el => {
        const eid = el.dataset.sensorEid;
        if (!homeAloneSensorConfig[eid]) homeAloneSensorConfig[eid] = {};
        homeAloneSensorConfig[eid].home_alone_camera = el.value || null;
      });
      root2.querySelectorAll('.ha-sensor-speaker').forEach(el => {
        const eid = el.dataset.sensorEid;
        if (!homeAloneSensorConfig[eid]) homeAloneSensorConfig[eid] = {};
        homeAloneSensorConfig[eid].home_alone_tts_speaker = el.value || null;
      });
      root2.querySelectorAll('.ha-sensor-action1').forEach(el => {
        const eid = el.dataset.sensorEid;
        if (!homeAloneSensorConfig[eid]) homeAloneSensorConfig[eid] = {};
        homeAloneSensorConfig[eid].home_alone_action_1 = el.value.trim() || null;
      });
      root2.querySelectorAll('.ha-sensor-action2').forEach(el => {
        const eid = el.dataset.sensorEid;
        if (!homeAloneSensorConfig[eid]) homeAloneSensorConfig[eid] = {};
        homeAloneSensorConfig[eid].home_alone_action_2 = el.value.trim() || null;
      });
    }

    const config = {
      name,
      type,
      enabled: temp.enabled !== false,
      arm_modes: armModes,
      sensors,
      home_alone_sensor_config: homeAloneSensorConfig,
    };

    const result = await this._callWS('save_zone', { zone_id: zoneId, config });
    this._zonesRenderCache = null;
    if (result && result.success !== false) {
      // v1.4.3: Persist per-sensor auto_bypass_modes via bulk save_sensors.
      // Only sends sensors that were actually shown in this dialog (sensors
      // currently assigned to the zone) -- merging with existing config so
      // we don't accidentally clobber other sensors' settings.
      try {
        const root3 = this.shadowRoot;
        const bypassByEid = {};
        root3.querySelectorAll('.sensor-bypass-cb').forEach(cb => {
          const eid = cb.dataset.sensorEid;
          const mode = cb.dataset.mode;
          if (!bypassByEid[eid]) bypassByEid[eid] = [];
          if (cb.checked) bypassByEid[eid].push(mode);
        });
        if (Object.keys(bypassByEid).length > 0) {
          // Build full sensors map: keep all existing fields, only override
          // auto_bypass_modes for sensors that appeared in this dialog.
          const allSensors = this._data.sensors || [];
          const merged = {};
          for (const s of allSensors) {
            merged[s.entity_id] = {
              enabled: !!s.enabled,
              sensor_type: s.sensor_type,
              entry_delay: s.entry_delay !== undefined ? s.entry_delay : null,
              auto_bypass: !!s.auto_bypass,
              auto_bypass_modes: Array.isArray(s.auto_bypass_modes) ? s.auto_bypass_modes : [],
              arm_on_close: !!s.arm_on_close,
            };
            if (s.env_unmarked) merged[s.entity_id].env_unmarked = true;
            if (s.is_environmental) merged[s.entity_id].is_environmental = true;
          }
          for (const [eid, modes] of Object.entries(bypassByEid)) {
            if (!merged[eid]) merged[eid] = { enabled: true, sensor_type: 'contact' };
            merged[eid].auto_bypass_modes = modes;
          }
          await this._callWS('save_sensors', { sensors: merged });
        }
      } catch (err) {
        console.warn('[secure-me] Could not persist auto_bypass_modes:', err);
      }

      this._showDialog = null;
      this._tempConfig = null;
      this._toast((temp._zoneId ? 'Zone opdateret.' : 'Zone oprettet.'), 'success');
      await this._loadData();
    } else {
      this._toast('Kunne ikke gemme zone: ' + (result?.error || 'Ukendt fejl'), 'error');
    }
  }

  _editZone(zoneId) {
    const zones = this._data.zones || {};
    const z = zones[zoneId];
    if (!z) return;
    this._tempConfig = {
      _zoneId: zoneId,
      name: z.name || '',
      type: z.type || 'entry',
      arm_modes: z.arm_modes || z.modes || ['away'],
      sensors: z.sensors || [],
      enabled: z.enabled !== false,
      home_alone_sensor_config: z.home_alone_sensor_config || {},
    };
    this._showDialog = 'zone';
    // Pre-load cameras and media_players for Home Alone config dropdowns
    if (!this._availableEntities.camera) this._loadEntitiesByDomain('camera');
    if (!this._availableEntities.media_player) this._loadEntitiesByDomain('media_player');
    this._render();
  }

  async _deleteZone(zoneId) {
    if (!await this._confirm('Denne zone og alle dens sensorer vil blive fjernet.', 'Slet zone?')) return;
    await this._callWS('delete_zone', { zone_id: zoneId });
    this._toast('Zone slettet', 'success');
    this._zonesRenderCache = null;
    await this._loadData();
  }

  // ===
  // TAB: USERS
  // ===
  _renderUsers() {
    const users = this._data.users || {};

    return `
      <div class="section-header">
        <h3 class="section-title">Users & Codes</h3>
        <button class="sm-btn primary sm" data-action="add-user">
          ${icon("plus")} Add User
        </button>
      </div>

      ${Object.entries(users).map(([id, u]) => `
        <div class="sm-card" style="padding:16px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div style="display:flex;align-items:center;gap:12px">
              <div class="user-avatar" style="background:${u.admin ? "var(--sm-accent-dim)" : "var(--sm-blue-dim)"};
                   color:${u.admin ? "var(--sm-accent)" : "var(--sm-blue)"}">
                ${(u.name || "?")[0].toUpperCase()}
              </div>
              <div>
                <div style="font-size:14px;font-weight:600">
                  ${u.name || id}
                  ${u.admin ? '<span class="badge accent" style="margin-left:8px">Admin</span>' : ""}
                </div>
                <div style="font-size:12px;color:var(--sm-text-secondary)">
                  Code: &#8226;&#8226;&#8226;&#8226;
                </div>
                ${u.person_entity ? `
                  <div style="font-size:11px;color:var(--sm-blue);margin-top:4px">
                    Tracker: <span style="font-family:'DM Mono',monospace">${u.person_entity.replace("person.","")}</span>
                  </div>` : ""}
                <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:5px">
                  ${u.notify_service ? `<span class="badge" style="background:var(--sm-blue-dim);color:var(--sm-blue);font-size:10px">${u.notify_service.replace('notify.','')}</span>` : '<span class="badge" style="opacity:0.4;font-size:10px">Ingen push-tjeneste</span>'}
                  ${u.receive_critical !== false ? '<span class="badge" style="background:var(--sm-red-dim);color:var(--sm-red);font-size:10px">Kritisk</span>' : ''}
                  ${u.tts_quiet_start != null && u.tts_quiet_end != null ? `<span class="badge" style="background:var(--sm-purple-dim);color:var(--sm-purple);font-size:10px">Quiet ${u.tts_quiet_start}-${u.tts_quiet_end}h</span>` : ''}
                </div>
              </div>
            </div>
            <div style="display:flex;gap:6px">
              <button class="sm-btn default sm" data-edit-user="${id}">${icon("settings")} Rediger</button>
              <button class="sm-btn ghost sm" data-delete-user="${id}">${icon("trash")}</button>
            </div>
          </div>
          ${u.nfc_tag ? `
            <div class="nfc-tag">
              <span style="color:var(--sm-purple)">${icon("nfc")}</span>
              <span class="nfc-tag-id">${u.nfc_tag}</span>
              <span style="font-size:11px;color:var(--sm-text-secondary);margin-left:auto">NFC Tag</span>
            </div>
          ` : ""}
          ${u.person_entity ? `
            <div style="margin-top:8px;padding:8px 12px;border-radius:8px;background:var(--sm-blue-dim);
                        border:1px solid rgba(10,132,255,0.15);display:flex;align-items:center;gap:8px">
              <span style="color:var(--sm-blue);font-size:13px">Person-tracker tilknyttet</span>
              <span style="font-size:11px;color:var(--sm-text-secondary);font-family:'DM Mono',monospace;margin-left:auto">${u.person_entity}</span>
            </div>
          ` : ""}
        </div>
      `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">Ingen brugere oprettet endnu. Klik "Tilføj bruger" for at starte.</div>'}

      <div class="info-card info">
        <span style="color:var(--sm-blue)">${icon("nfc")}</span>
        <div style="flex:1">
          <div class="info-title" style="color:var(--sm-blue)">Importér NFC-tags</div>
          <div class="info-text">Importér eksisterende NFC-tags fra Home Assistant</div>
        </div>
        <button class="sm-btn default sm" data-action="import-nfc">Importér</button>
      </div>

    `;
  }

  _renderUserDialog() {
    const temp = this._tempConfig || {};
    const isEdit = !!temp._userId;
    const title = isEdit ? 'Edit User' : 'Add User';
    const services = this._availableServices || [];

    // Notification settings with defaults
    const ns = temp.notification_settings || {};
    const notifyService   = ns.notify_service   ?? '';
    const recvCritical    = ns.receive_critical  !== false;
    const recvAlerts      = ns.receive_alerts    !== false;
    const recvOwnActions  = ns.receive_own_actions !== false;
    const quietStart      = ns.tts_quiet_start   ?? '';
    const quietEnd        = ns.tts_quiet_end      ?? '';

    const checkRow = (id, label, checked, hint) =>
      '<label style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:8px 12px;' +
      'border-radius:8px;background:rgba(255,255,255,0.03);font-size:14px;margin-bottom:4px">' +
        '<input type="checkbox" id="' + id + '"' + (checked ? ' checked' : '') + '>' +
        '<span style="flex:1">' + label + '</span>' +
        '<span style="font-size:11px;color:var(--sm-text-tertiary)">' + hint + '</span>' +
      '</label>';

    return '<div class="config-dialog-overlay">' +
      '<div class="config-dialog" style="max-width:520px">' +
        '<div class="dialog-header">' +
          icon('user') +
          '<div class="dialog-title">' + title + '</div>' +
          '<button class="dialog-close" data-action="close-dialog">' + icon("close") + '</button>' +
        '</div>' +

        // Name
        '<div class="form-group">' +
          '<label class="form-label">Brugernavn</label>' +
          '<input type="text" class="form-input" id="user-name" placeholder="f.eks. Flemming, Lucas" value="' + (temp.name || '') + '">' +
        '</div>' +

        // Code
        '<div class="form-group">' +
          '<label class="form-label">' + (isEdit ? 'New Access Code (leave blank to keep)' : 'Access Code (4-6 digits)') + '</label>' +
          '<input type="password" class="form-input" id="user-code" placeholder="' + (isEdit ? 'Leave blank to keep current' : 'e.g. 1234') + '" maxlength="6" pattern="[0-9]*" inputmode="numeric" value="">' +
        '</div>' +
        '<div class="form-group">' +
          '<label class="form-label">' + (isEdit ? 'Confirm New Code' : 'Confirm Code') + '</label>' +
          '<input type="password" class="form-input" id="user-code-confirm" placeholder="' + (isEdit ? 'Leave blank to keep current' : 'Repeat code') + '" maxlength="6" pattern="[0-9]*" inputmode="numeric" value="">' +
        '</div>' +

        // Admin
        '<div class="form-group">' +
          checkRow('user-admin', 'Administrator', temp.admin, 'Full access') +
        '</div>' +

        // Person tracker
        '<div class="form-group">' +
          '<label class="form-label">Link Person Tracker (optional)</label>' +
          '<select class="form-select" id="user-person-entity">' +
            '<option value="">-- None --</option>' +
            (this._availablePersons || []).map(p =>
              '<option value="' + p.entity_id + '"' + (temp.person_entity === p.entity_id ? ' selected' : '') + '>' +
                p.name + ' (' + p.entity_id + ')' +
              '</option>'
            ).join('') +
          '</select>' +
        '</div>' +

        // ── Notification Settings ──
        '<div style="border-top:1px solid var(--sm-border);margin:12px 0 8px;padding-top:12px">' +
          '<div style="font-size:13px;font-weight:600;color:var(--sm-text-secondary);margin-bottom:10px">' +
            icon('bell') + ' Notification Settings' +
          '</div>' +

          '<div class="form-group">' +
            '<label class="form-label">Push-notifikationstjeneste</label>' +
            '<select class="form-select" id="user-notify-service">' +
              '<option value="">-- None (use notification default) --</option>' +
              services.map(s =>
                '<option value="' + s + '"' + (notifyService === s ? ' selected' : '') + '>' + s + '</option>'
              ).join('') +
            '</select>' +
            '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:4px">' +
              'Personal notify service, e.g. notify.mobile_app_flemming' +
            '</div>' +
          '</div>' +

          checkRow('user-recv-critical',   'Receive critical alerts',    recvCritical,   'Triggered / smoke / water / entry delay') +
          checkRow('user-recv-alerts',      'Receive system alerts',      recvAlerts,     'Low battery, arm failures') +
          checkRow('user-recv-own-actions', 'Receive own arm/disarm',     recvOwnActions, 'Confirmation when you arm or disarm') +

          // TTS quiet hours
          '<div style="margin-top:10px">' +
            '<label class="form-label">TTS Quiet Hours (optional)</label>' +
            '<div style="display:flex;align-items:center;gap:8px">' +
              '<input type="number" class="form-input" id="user-tts-quiet-start" min="0" max="23" placeholder="22" ' +
                'value="' + quietStart + '" style="width:70px;text-align:center">' +
              '<span style="color:var(--sm-text-tertiary)">to</span>' +
              '<input type="number" class="form-input" id="user-tts-quiet-end" min="0" max="23" placeholder="7" ' +
                'value="' + quietEnd + '" style="width:70px;text-align:center">' +
              '<span style="font-size:11px;color:var(--sm-text-tertiary)">hour (0-23). TTS silent during this period.</span>' +
            '</div>' +
          '</div>' +
        '</div>' +

        '<div class="dialog-footer">' +
          '<button class="btn-dialog cancel" data-action="close-dialog">Annuller</button>' +
          '<button class="btn-dialog save" data-action="save-user">' + (isEdit ? 'Gem ændringer' : 'Gem bruger') + '</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  async _saveUser() {
    const root = this.shadowRoot;
    const name        = root.querySelector('#user-name')?.value?.trim();
    const code        = root.querySelector('#user-code')?.value?.trim();
    const codeConfirm = root.querySelector('#user-code-confirm')?.value?.trim();
    const admin       = root.querySelector('#user-admin')?.checked || false;
    const personEntity = root.querySelector('#user-person-entity')?.value || null;
    const isEdit      = !!this._tempConfig?._userId;
    const userId      = this._tempConfig?._userId || '';

    // Notification settings
    const notifyService  = root.querySelector('#user-notify-service')?.value || '';
    const recvCritical   = root.querySelector('#user-recv-critical')?.checked !== false;
    const recvAlerts     = root.querySelector('#user-recv-alerts')?.checked !== false;
    const recvOwnActions = root.querySelector('#user-recv-own-actions')?.checked !== false;
    const quietStartRaw  = root.querySelector('#user-tts-quiet-start')?.value;
    const quietEndRaw    = root.querySelector('#user-tts-quiet-end')?.value;
    const ttsQuietStart  = quietStartRaw !== '' && quietStartRaw !== null ? parseInt(quietStartRaw) : null;
    const ttsQuietEnd    = quietEndRaw   !== '' && quietEndRaw   !== null ? parseInt(quietEndRaw)   : null;

    if (!name) { this._toast('Indtast et brugernavn.', 'warning'); return; }

    const notificationSettings = {
      notify_service:    notifyService,
      receive_critical:  recvCritical,
      receive_alerts:    recvAlerts,
      receive_own_actions: recvOwnActions,
      tts_quiet_start:   ttsQuietStart,
      tts_quiet_end:     ttsQuietEnd,
    };

    if (isEdit) {
      if (code) {
        if (code.length < 4) { this._toast('Koden skal være mindst 4 cifre.', 'warning'); return; }
        if (code !== codeConfirm) { this._toast('Koderne matcher ikke.', 'warning'); return; }
        if (!/^[0-9]+$/.test(code)) { this._toast('Koden må kun bestå af tal.', 'warning'); return; }
      }
      const existing = this._data.users[userId] || {};
      const config = {
        ...existing,
        name,
        admin,
        person_entity: personEntity || null,
        ...notificationSettings,
      };
      if (code) config.code = code;

      const result = await this._callWS('save_user', { user_id: userId, config });
      if (result && result.success !== false) {
        this._showDialog = null;
        this._tempConfig = null;
        await this._loadData();
        this._toast('Bruger opdateret', 'success');
      } else {
        this._toast('Kunne ikke opdatere bruger: ' + (result?.error || 'Ukendt fejl'), 'error');
      }
    } else {
      if (!code || code.length < 4) { this._toast('Koden skal være mindst 4 cifre.', 'warning'); return; }
      if (code !== codeConfirm) { this._toast('Koderne matcher ikke.', 'warning'); return; }
      if (!/^[0-9]+$/.test(code)) { this._toast('Koden må kun bestå af tal.', 'warning'); return; }

      const config = {
        name,
        code,
        admin,
        nfc_tag: null,
        person_entity: personEntity || null,
        ...notificationSettings,
      };
      const result = await this._callWS('save_user', { user_id: '', config });
      if (result && result.success !== false) {
        this._showDialog = null;
        this._tempConfig = null;
        await this._loadData();
        this._toast('Bruger gemt!', 'success');
      } else {
        this._toast('Kunne ikke gemme bruger: ' + (result?.error || 'Ukendt fejl'), 'error');
      }
    }
  }

  async _deleteUser(userId) {
    if (!await this._confirm('Denne bruger vil blive fjernet permanent.', 'Slet bruger?')) return;
    await this._callWS('delete_user', { user_id: userId });
    this._toast('Bruger slettet', 'success');
    await this._loadData();
  }

  // ===
  // TAB: MODULES
  // ===
  _renderModules() {
    const cacheKey = JSON.stringify({ m: this._data.modules, h: this._data.health?.modules });
    if (this._modulesRenderKey === cacheKey && this._modulesRenderCache) return this._modulesRenderCache;
    const modules = this._data.modules || {};
    const enabledCount = Object.values(modules).filter(m => m.enabled).length;

    const html = `
      <div class="section-header">
        <h3 class="section-title">Moduler</h3>
        <span class="badge accent">${enabledCount} aktive</span>
      </div>

      ${Object.entries(MODULE_DEFS).map(([key, def]) => {
        const mod = modules[key] || { enabled: false };
        const expanded = this._expandedModule === key && mod.enabled;

        // v0.7.0: Module health badge from health data
        const health = this._data.health?.modules?.[key];
        const healthBadge = mod.enabled && health ? (() => {
          const s = health.status || 'unknown';
          const labels = { ok:'OK', healthy:'OK', pass:'OK', warn:'Warning', warning:'Warning', error:'Error', degraded:'Degraded', unknown:'Unknown' };
          const cls = s === 'ok' || s === 'healthy' || s === 'pass' ? 'ok'
                    : s === 'warn' || s === 'warning' ? 'warn'
                    : s === 'error' ? 'error'
                    : s === 'degraded' ? 'degraded' : 'unknown';
          const ico = cls === 'ok' ? icon('ok') : cls === 'warn' ? icon('warn') : icon('fail');
          return `<span class="module-health-badge ${cls}">${ico} ${labels[s] || s}</span>`;
        })() : '';

        return `
          <div class="sm-card" style="padding:0;overflow:hidden;
               border-color:${mod.enabled ? def.color + "33" : "var(--sm-border)"}">
            <div class="module-header ${mod.enabled ? "" : "disabled"}">
              <div class="module-icon ${mod.enabled ? "" : "disabled-icon"}"
                   data-module-expand="${key}"
                   style="background:${mod.enabled ? def.color + "22" : "rgba(255,255,255,0.05)"};
                   color:${mod.enabled ? def.color : "var(--sm-text-tertiary)"}">
                ${icon(def.icon)}
              </div>
              <div class="module-name-area" data-module-expand="${key}"
                   style="cursor:${mod.enabled ? 'pointer' : 'default'}">
                <div style="font-size:14px;font-weight:600">${def.name}</div>
                <div style="font-size:12px;color:var(--sm-text-secondary);display:flex;align-items:center;gap:6px">
                  ${def.desc}
                  ${healthBadge}
                </div>
              </div>
              ${mod.enabled ? `
                <button class="sm-btn ghost sm" data-module-expand="${key}"
                        style="margin-right:8px;padding:4px 10px;font-size:11px;opacity:0.7">
                  ${icon('settings')}
                </button>` : ''}
              <button class="sm-toggle ${mod.enabled ? "on" : ""}"
                      data-module-toggle="${key}">
                <div class="dot"></div>
              </button>
            </div>
            <!-- Module config opens as dialog via data-module-expand click -->
          </div>
        `;
      }).join("")}
    `;
    this._modulesRenderKey   = cacheKey;
    this._modulesRenderCache = html;
    return html;
  }

  _renderModuleConfig(moduleKey) {
    const moduleDef = MODULE_DEFS[moduleKey];
    const moduleData = this._data.modules[moduleKey] || {};
    
    // Camera module gets GUI config dialog
    if (moduleKey === 'camera') {
      const cameraCount = moduleData.cameras?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">
            ${moduleDef.name} Configuration
          </div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">
            Configure cameras with POE control and recording settings
          </div>
          
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div>
                <div style="font-size:13px;font-weight:600">Kameraer konfigureret</div>
                <div style="font-size:12px;color:var(--sm-text-secondary)">${cameraCount} camera${cameraCount !== 1 ? 's' : ''}</div>
              </div>
            </div>
            ${cameraCount > 0 ? `
              <div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
                ${moduleData.cameras.map(cam => `
                  <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                    ${icon("chevron")}
                    <span style="font-size:12px">${cam.entity_id || cam}</span>
                    ${cam.poe_port ? `<span style="font-size:11px;color:var(--sm-text-tertiary)">POE: ${cam.poe_port}</span>` : ''}
                  </div>
                `).join('')}
              </div>
            ` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen kameraer konfigureret endnu</div>'}
          </div>
          
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-camera-config">
              ${icon("settings")} Configure Cameras
            </button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">
              Close
            </button>
          </div>
        </div>
      `;
    }
    
    // Lock module gets GUI config dialog
    if (moduleKey === 'lock') {
      const lockCount = moduleData.locks?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">
            ${moduleDef.name} Configuration
          </div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">
            Configure smart locks with automatic lock/unlock
          </div>
          
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div>
                <div style="font-size:13px;font-weight:600">Låse konfigureret</div>
                <div style="font-size:12px;color:var(--sm-text-secondary)">${lockCount} lock${lockCount !== 1 ? 's' : ''}</div>
              </div>
            </div>
            ${lockCount > 0 ? `
              <div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
                ${moduleData.locks.map(lock => `
                  <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                    ${icon("chevron")}
                    <span style="font-size:12px">${lock.entity_id}</span>
                  </div>
                `).join('')}
              </div>
            ` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen låse konfigureret endnu</div>'}
          </div>
          
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-lock-config">
              ${icon("settings")} Configure Locks
            </button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">
              Close
            </button>
          </div>
        </div>
      `;
    }
    
        // Climate module gets GUI config dialog
    if (moduleKey === 'climate') {
      const thermostatCount = moduleData.thermostats?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Konfigurér termostater til energibesparelse</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Termostater konfigureret</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${thermostatCount} thermostat${thermostatCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${thermostatCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.thermostats.map(t => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${t.entity_id}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen termostater konfigureret endnu</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-climate-config">${icon("settings")} Konfigurér termostater</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Luk</button>
          </div>
        </div>`;
    }
    
    // Siren module
    if (moduleKey === 'siren') {
      const sirenCount = moduleData.sirens?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Konfigurér alarmsirener og mønstre</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Sirener konfigureret</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${sirenCount} siren${sirenCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${sirenCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.sirens.map(s => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${s.entity_id}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen sirener konfigureret endnu</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-siren-config">${icon("settings")} Konfigurér sirener</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Luk</button>
          </div>
        </div>`;
    }
    
    // Lights module
    if (moduleKey === 'lights') {
      const lightCount = moduleData.entities?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Konfigurér lysautomatisering og effekter</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Lys konfigureret</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${lightCount} light${lightCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${lightCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.entities.slice(0, 5).map(e => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${e}</span></div>`).join('')}
              ${lightCount > 5 ? `<div style="text-align:center;padding:6px;color:var(--sm-text-secondary);font-size:11px">+${lightCount - 5} more...</div>` : ''}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen lys konfigureret endnu</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-lights-config">${icon("settings")} Konfigurér lys</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Luk</button>
          </div>
        </div>`;
    }
    
    // TTS module
    if (moduleKey === 'tts') {
      const speakerCount = moduleData.entities?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Konfigurér talebeskeder</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Højtalere konfigureret</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${speakerCount} speaker${speakerCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${speakerCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.entities.map(e => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${e}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">Ingen højtalere konfigureret endnu</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-tts-config">${icon("settings")} Konfigurér TTS</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Luk</button>
          </div>
        </div>`;
    }
    
        // Other modules still use JSON for now
    const configJson = JSON.stringify(moduleData, null, 2);
    return `
      <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
        <div style="font-size:14px;font-weight:600;margin-bottom:8px">
          ${moduleDef.name} Configuration
        </div>
        <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">
          Edit configuration below (JSON format):
        </div>
        
        <textarea id="module-config-${moduleKey}" 
                  style="width:100%;min-height:200px;padding:12px;background:var(--sm-surface);
                         border:1px solid var(--sm-border);border-radius:8px;color:var(--sm-text);
                         font-family:'DM Mono',monospace;font-size:12px;resize:vertical">${configJson}</textarea>
        
        <div style="margin-top:16px;display:flex;gap:8px">
          <button class="sm-btn primary" data-save-module-config="${moduleKey}">
            Save Changes
          </button>
          <button class="sm-btn default" data-cancel-module="${moduleKey}">
            Cancel
          </button>
        </div>
        
        <div style="margin-top:16px;padding:12px;background:var(--sm-blue-dim);border-radius:8px;font-size:11px">
          <strong>Example configuration:</strong>
          <details style="margin-top:8px">
            <summary style="cursor:pointer;font-weight:600">Show example for ${moduleDef.name}</summary>
            <pre style="margin-top:8px;padding:8px;background:rgba(0,0,0,0.3);border-radius:4px;overflow-x:auto;font-size:10px">${this._getModuleExample(moduleKey)}</pre>
          </details>
        </div>
      </div>
    `;
  }

  _getModuleExample(moduleKey) {
    const examples = {
      camera: `{
  "enabled": true,
  "poe_switches": [
    "switch.vision_port_1_poe",
    "switch.vision_port_5_poe"
  ],
  "cameras": [
    "camera.hallway_cam_high",
    "camera.g3_flex_high"
  ],
  "poe_delay": 120,
  "auto_record": false
}`,
      lock: `{
  "enabled": true,
  "locks": ["lock.front_door"],
  "retry_attempts": 3
}`,
      lights: `{
  "enabled": true,
  "lights": ["light.living_room"],
  "brightness": 100
}`,
      climate: `{
  "enabled": true,
  "climates": ["climate.living_room"],
  "away_temperature": 15
}`,
      siren: `{
  "enabled": true,
  "sirens": ["siren.alarm"]
}`,
      tts: `{
  "enabled": true,
  "media_players": ["media_player.living_room"],
  "language": "da"
}`
    };
    return examples[moduleKey] || "{}";
  }


  // ===
// ============================================================
// FLOORPLAN PATCH — erstat alt mellem linje 2102 og ~2665
// ============================================================

  // TAB: FLOORPLAN (v1.6.0 — room-based SVG editor)
  // ===
  // Three display modes:
  //   1. Empty      — no image -> show upload prompt
  //   2. View mode  — image uploaded, rooms drawn -> PNG only visible
  //   3. Edit mode  — draw rooms, assign sensors, rename
  //   4. Live mode  — Home Alone active -> rooms glow on sensor activity
  //
  // Room data shape (stored via save_floorplan_markers for backwards compat):
  //   rooms: {
  //     "room_1": {
  //       name: "Køkken",
  //       color: "#7c3aed",          // accent color for this room
  //       points: [[x_pct,y_pct],...], // polygon vertices, % of canvas
  //       sensors: ["binary_sensor.koekken_motion_occupancy"],
  //     }
  //   }

  async _loadFloorplan() {
    const fp = await this._callWS("get_floorplan");
    if (fp) {
      this._data.floorplan = {
        image_url: fp.image_url || null,
        width:     fp.width  || 0,
        height:    fp.height || 0,
        rooms:     fp.rooms  || fp.markers || {},  // backwards compat
        openings:  fp.openings || [],
        markers:   fp.markers || {},  // sensor pin positions for live-view
      };
    }
    this._floorplanLoaded = true;
    this._render();
  }

  // ─── Room helpers ─────────────────────────────────────────────────────────

  _fpRoomColor(idx) {
    const palette = [
      "#7c3aed","#3b82f6","#06b6d4","#10b981",
      "#f59e0b","#ef4444","#8b5cf6","#ec4899",
    ];
    return palette[idx % palette.length];
  }

  _fpNewRoomId() {
    return "room_" + Date.now();
  }

  _fpSensorsInRoom(roomId) {
    const rooms = this._data.floorplan?.rooms || {};
    return (rooms[roomId]?.sensors || []);
  }

  _fpAvailableSensors() {
    const allAssigned = new Set();
    for (const r of Object.values(this._data.floorplan?.rooms || {})) {
      (r.sensors || []).forEach(s => allAssigned.add(s));
    }
    return (this._data.sensors || []).filter(s => {
      if (s.is_environmental) return false;
      const dc = s.device_class || "";
      return ["motion","occupancy","door","window","opening","garage_door","vibration","presence"].includes(dc);
    });
  }

  _fpRoomIsActive(room) {
    // Returns true when any assigned sensor is "on"
    return (room.sensors || []).some(eid => this._sensorIsActive(eid));
  }

  _fpUpdateLiveState() {
    // Targeted DOM patch for Home Alone live-view updates -- avoids the full
    // innerHTML teardown/rebuild that _queueRender() would otherwise do.
    //
    // Why this matters: rebuilding the whole SVG on every sensor tick used to
    // restart the CSS glow animation on every currently-active room (even ones
    // whose own sensor didn't change), pop door/window markers in and out of
    // existence instead of fading them, and re-parse a large HTML string for
    // a change that's really just "toggle one attribute on one element".
    //
    // Returns true if the patch was applied, false if the canvas isn't in the
    // DOM yet (caller should fall back to a full _queueRender() in that case).
    const canvas = this.shadowRoot?.querySelector('[data-fp-canvas]');
    if (!canvas) return false;
    const svg = canvas.querySelector('[data-fp-svg]');
    if (!svg) return false;

    const fp = this._data.floorplan;
    if (!fp) return false;

    // Rooms: toggle glow class + opacity only when the active-state actually
    // flips, so an already-glowing room's animation is never interrupted.
    for (const [rid, room] of Object.entries(fp.rooms || {})) {
      const poly = svg.querySelector(`[data-fp-room="${rid}"]`);
      if (!poly) continue;
      const isActive = this._fpRoomIsActive(room);
      const wasActive = poly.classList.contains('fp-room-active');
      if (isActive !== wasActive) {
        poly.classList.toggle('fp-room-active', isActive);
        poly.setAttribute('fill-opacity', isActive ? '0.35' : '0');
        poly.setAttribute('stroke-opacity', isActive ? '0.8' : '0');
      }
      const labelEl = canvas.querySelector(`[data-fp-label="${rid}"]`);
      if (labelEl) labelEl.style.opacity = isActive ? '1' : '0';
    }

    // Openings: fade in/out via opacity instead of adding/removing from the DOM.
    (fp.openings || []).forEach((op, oi) => {
      const group = svg.querySelector(`[data-fp-opening-group="${oi}"]`);
      if (!group) return;
      const eid = op.entity_id || null;
      const isOpen = eid ? this._hass?.states?.[eid]?.state === "on" : false;
      group.style.opacity = isOpen ? '1' : '0';
    });

    // Sensor pins: only regenerate the ones whose active-state changed --
    // one small <g> each, not the whole SVG.
    for (const [eid, m] of Object.entries(fp.markers || {})) {
      const pin = svg.querySelector(`[data-fp-pin="${eid}"]`);
      if (!pin) continue;
      const isActive = this._sensorIsActive(eid);
      const wasActive = pin.dataset.fpPinActive === "1";
      if (isActive !== wasActive) {
        pin.dataset.fpPinActive = isActive ? "1" : "0";
        pin.innerHTML = this._fpRenderSensorPinInner(eid, m);
      }
    }

    return true;
  }

  _fpPointsToSvgPolygon(points, w, h) {
    // points are [x_pct, y_pct] — convert to px for SVG viewBox
    return points.map(([x,y]) => `${(x/100*w).toFixed(1)},${(y/100*h).toFixed(1)}`).join(" ");
  }

  // ─── Main render ──────────────────────────────────────────────────────────

  _renderFloorplan() {
    if (!this._floorplanLoaded) {
      return `
        <div class="section-header"><h3 class="section-title">Etageplan</h3></div>
        <div class="sm-card" style="padding:32px;text-align:center;color:var(--sm-text-secondary)">
          Indlæser etageplan...
        </div>
      `;
    }

    const fp       = this._data.floorplan || { image_url: null, rooms: {} };
    const hasImage = !!fp.image_url;
    const rooms    = fp.rooms || {};
    const roomCount = Object.keys(rooms).length;
    const liveMode = this._isHomeAloneLiveActive();
    const editMode = this._floorplanEditMode && !liveMode;

    return `
      <div class="section-header">
        <h3 class="section-title">Etageplan</h3>
        ${liveMode
          ? `<span class="badge" style="background:var(--sm-green-dim);color:var(--sm-green)">Alene-tilstand live</span>`
          : editMode
            ? `<span class="badge" style="background:var(--sm-warning-dim);color:var(--sm-warning)">Redigeringstilstand</span>`
            : hasImage && roomCount > 0
              ? `<span class="badge accent">${roomCount} rum</span>`
              : ""
        }
      </div>

      ${hasImage ? this._renderFloorplanCanvas(fp, liveMode, editMode) : (!liveMode ? this._renderFloorplanEmpty() : "")}

      <!-- Hidden file input -->
      <input type="file" accept="image/png" style="display:none" data-fp-file-input>
    `;
  }

  _renderFloorplanEmpty() {
    return `
      <div class="sm-card" style="padding:48px 24px;text-align:center;
           border:2px dashed var(--sm-border);background:rgba(255,255,255,0.02)">
        <div style="color:var(--sm-text-tertiary);margin-bottom:16px">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
            <line x1="8" y1="2" x2="8" y2="18"/>
            <line x1="16" y1="6" x2="16" y2="22"/>
          </svg>
        </div>
        <div style="font-size:15px;font-weight:600;margin-bottom:6px">Ingen planløsning uploadet</div>
        <div style="font-size:13px;color:var(--sm-text-secondary);margin-bottom:20px">
          Upload et PNG-billede af din bolig (maks. 4 MB)
        </div>
        <button class="sm-btn primary" data-fp-upload ${this._floorplanUploading ? "disabled" : ""}>
          ${icon("upload")} ${this._floorplanUploading ? "Uploader..." : "Upload PNG"}
        </button>
      </div>
    `;
  }

  _fpRenderSensorPinInner(eid, m) {
    // Shared by the cold SVG render and the targeted live-update path so both
    // produce identical markup for a pin's interior (everything except the
    // wrapping <g>, which owns the stable id used for direct DOM patching).
    const x = parseFloat(m.x_pct);
    const y = parseFloat(m.y_pct);
    if (isNaN(x) || isNaN(y)) return "";
    const VW = 1000;
    const fp = this._data.floorplan || {};
    const aspectRatio = fp.width && fp.height ? (fp.height / fp.width) : 0.6;
    const VH = Math.round(VW * aspectRatio);
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
            pointer-events="none" style="user-select:none">${label}</text>` : ""}
    `;
  }

  _renderFloorplanCanvas(fp, liveMode, editMode) {
    const rooms  = fp.rooms || {};
    const cacheBust = fp.image_url + (fp.image_url.includes("?") ? "&" : "?") + "v=" + (this._floorplanCacheBust || 0);
    const aspectRatio = fp.width && fp.height ? (fp.height / fp.width) : 0.6;

    // SVG viewBox dimensions (virtual px — aspect-ratio preserved)
    const VW = 1000;
    const VH = Math.round(VW * aspectRatio);

    // Build SVG room polygons
    const roomEntries = Object.entries(rooms);
    const svgRooms = roomEntries.map(([rid, room], idx) => {
      const pts = room.points || [];
      if (pts.length < 3) return "";

      const polyPts  = this._fpPointsToSvgPolygon(pts, VW, VH);
      const color    = room.color || this._fpRoomColor(idx);
      const isActive = liveMode && this._fpRoomIsActive(room);
      const isSelected = editMode && this._floorplanSelectedRoom === rid;

      // Live mode: glow fill when active, invisible when not
      // Edit mode: always show semi-transparent with border
      // View mode: invisible (opacity 0)
      let fillOpacity, strokeOpacity, cls = "";
      if (liveMode) {
        fillOpacity   = isActive ? 0.35 : 0;
        strokeOpacity = isActive ? 0.8  : 0;
        if (isActive) cls = "fp-room-active";
      } else if (editMode) {
        fillOpacity   = isSelected ? 0.28 : 0.14;
        strokeOpacity = 1;
      } else {
        // View mode — completely invisible
        fillOpacity   = 0;
        strokeOpacity = 0;
      }

      // Room label (only in edit mode)
      const cx = pts.reduce((s,[x])=>s+x,0)/pts.length;
      const cy = pts.reduce((s,[,y])=>s+y,0)/pts.length;
      const label = editMode ? `
        <text x="${(cx/100*VW).toFixed(1)}" y="${(cy/100*VH).toFixed(1)}"
              text-anchor="middle" dominant-baseline="middle"
              font-family="DM Sans,sans-serif" font-size="28" font-weight="600"
              fill="${color}" opacity="${isSelected ? 1 : 0.7}"
              pointer-events="none" style="user-select:none">
          ${room.name || "Rum"}
        </text>` : "";

      // In-progress drawing preview handles
      const handles = (editMode && isSelected) ? pts.map(([x,y], pi) => `
        <circle cx="${(x/100*VW).toFixed(1)}" cy="${(y/100*VH).toFixed(1)}"
                r="8" fill="${color}" stroke="white" stroke-width="2"
                class="fp-handle" data-fp-handle="${rid}-${pi}"
                style="cursor:move;pointer-events:all"/>
      `).join("") : "";

      return `
        <polygon points="${polyPts}"
                 fill="${color}" fill-opacity="${fillOpacity}"
                 stroke="${color}" stroke-opacity="${strokeOpacity}"
                 stroke-width="${isSelected ? 2.5 : 1.5}" stroke-linejoin="round"
                 class="fp-room ${cls}" data-fp-room="${rid}"
                 style="cursor:${editMode ? 'pointer' : 'default'};pointer-events:${editMode ? 'all' : 'none'}"/>
        ${label}
        ${handles}
      `;
    }).join("");

    // Build SVG opening markers (doors/windows)
    const openings = fp.openings || [];
    const svgOpenings = openings.map((op, oi) => {
      if (!op.points || op.points.length < 2) return "";
      const [x1, y1] = op.points[0];
      const [x2, y2] = op.points[1];
      const sx1 = (x1/100*VW).toFixed(1), sy1 = (y1/100*VH).toFixed(1);
      const sx2 = (x2/100*VW).toFixed(1), sy2 = (y2/100*VH).toFixed(1);
      const mx  = ((x1+x2)/2/100*VW).toFixed(1);
      const my  = ((y1+y2)/2/100*VH).toFixed(1);
      const color = op.type === "window" ? "#fbbf24" : "#e2e8f0";
      const label = op.label || (op.type === "window" ? "Vindue" : "Dor");
      // In live mode: rendered always, but faded via opacity when the sensor
      // reports closed (or no sensor assigned) -- this lets it fade smoothly
      // instead of popping in/out of the DOM on every state change.
      // In edit/view mode: always fully visible.
      const isEditVisible = editMode || liveMode;
      if (!isEditVisible) return "";
      let liveOpacity = 1;
      if (liveMode) {
        const eid    = op.entity_id || null;
        const isOpen = eid ? this._hass?.states?.[eid]?.state === "on" : false;
        liveOpacity = isOpen ? 1 : 0;
      }
      const isSelOp = editMode && this._floorplanSelectedOpening === oi;

      // Retnings-bue for dør (SVG arc fra startpunkt til midtpunkt)
      const lineLenVW = Math.sqrt((parseFloat(sx2)-parseFloat(sx1))**2 + (parseFloat(sy2)-parseFloat(sy1))**2);
      const arcR = (lineLenVW * 0.5).toFixed(1);
      const arcPath = op.type !== "window"
        ? `<path d="M ${sx1} ${sy1} A ${arcR} ${arcR} 0 0 1 ${mx} ${my}"
               fill="none" stroke="${color}" stroke-width="1.5" stroke-dasharray="4,3"
               opacity="${isSelOp ? 0.9 : 0.45}" pointer-events="none"/>`
        : "";

      return `
        <g class="fp-opening-group" data-fp-opening-group="${oi}" style="opacity:${liveMode ? liveOpacity : 1}">
        ${isSelOp ? `
          <line x1="${sx1}" y1="${sy1}" x2="${sx2}" y2="${sy2}"
                stroke="white" stroke-width="12" stroke-linecap="round"
                opacity="0.3" pointer-events="none"/>
        ` : ""}
        <line x1="${sx1}" y1="${sy1}" x2="${sx2}" y2="${sy2}"
              stroke="${color}" stroke-width="${isSelOp ? 7 : 6}" stroke-linecap="round"
              opacity="0.9" pointer-events="${editMode ? 'all' : 'none'}"
              data-fp-opening="${oi}" style="cursor:${editMode ? 'pointer' : 'default'}"/>
        ${arcPath}
        <circle cx="${sx1}" cy="${sy1}" r="5" fill="${color}" opacity="0.7" pointer-events="none"/>
        <circle cx="${sx2}" cy="${sy2}" r="5" fill="${color}" opacity="0.7" pointer-events="none"/>
        ${editMode ? `
          <text x="${mx}" y="${(parseFloat(my)-10).toFixed(1)}"
                text-anchor="middle" font-family="DM Sans,sans-serif"
                font-size="18" fill="${color}" opacity="${isSelOp ? 1 : 0.9}"
                pointer-events="none" style="user-select:none">${label}</text>
        ` : ""}
        </g>
      `;
    }).join("");

    // Build SVG sensor pins (live mode: show active/inactive; edit mode: show all)
    const markerEntries = Object.entries(fp.markers || {});
    const svgSensorPins = (liveMode && markerEntries.length > 0) ? markerEntries.map(([eid, m]) => {
      const inner = this._fpRenderSensorPinInner(eid, m);
      if (!inner) return "";
      const isActive = this._sensorIsActive(eid);
      return `<g class="fp-pin" data-fp-pin="${eid}" data-fp-pin-active="${isActive ? 1 : 0}">${inner}</g>`;
    }).join("") : "";

    // In-progress drawing preview
    const drawing = this._floorplanDrawing;
    let previewSvg = "";
    if (editMode && drawing && drawing.points.length > 0) {
      const pts = drawing.points;
      const color = "#7c3aed";
      if (drawing.tool === "polygon") {
        const lines = pts.map(([x,y]) => `${(x/100*VW).toFixed(1)},${(y/100*VH).toFixed(1)}`).join(" ");
        const dots  = pts.map(([x,y]) => `
          <circle cx="${(x/100*VW).toFixed(1)}" cy="${(y/100*VH).toFixed(1)}"
                  r="6" fill="${color}" stroke="white" stroke-width="2" pointer-events="none"/>
        `).join("");
        const mousePreview = drawing.mouse ? `
          <line x1="${(pts[pts.length-1][0]/100*VW).toFixed(1)}" y1="${(pts[pts.length-1][1]/100*VH).toFixed(1)}"
                x2="${(drawing.mouse[0]/100*VW).toFixed(1)}" y2="${(drawing.mouse[1]/100*VH).toFixed(1)}"
                stroke="${color}" stroke-width="1.5" stroke-dasharray="6,4" pointer-events="none" opacity="0.7"/>
        ` : "";
        previewSvg = `
          <polyline points="${lines}" fill="none"
                    stroke="${color}" stroke-width="2" stroke-dasharray="6,4"
                    pointer-events="none"/>
          ${dots}
          ${mousePreview}
        `;
      } else if (drawing.tool === "rect" && pts.length === 1 && drawing.mouse) {
        const [x1,y1] = pts[0];
        const [x2,y2] = drawing.mouse;
        const rx = Math.min(x1,x2)/100*VW, ry = Math.min(y1,y2)/100*VH;
        const rw = Math.abs(x2-x1)/100*VW, rh = Math.abs(y2-y1)/100*VH;
        previewSvg = `
          <rect x="${rx.toFixed(1)}" y="${ry.toFixed(1)}"
                width="${rw.toFixed(1)}" height="${rh.toFixed(1)}"
                fill="${color}" fill-opacity="0.15"
                stroke="${color}" stroke-width="2" stroke-dasharray="6,4"
                pointer-events="none"/>
        `;
      } else if (drawing.tool === "opening" && pts.length === 1 && drawing.mouse) {
        const [x1,y1] = pts[0];
        const [x2,y2] = drawing.mouse;
        previewSvg = `
          <line x1="${(x1/100*VW).toFixed(1)}" y1="${(y1/100*VH).toFixed(1)}"
                x2="${(x2/100*VW).toFixed(1)}" y2="${(y2/100*VH).toFixed(1)}"
                stroke="#e2e8f0" stroke-width="6" stroke-linecap="round"
                stroke-dasharray="8,4" opacity="0.8" pointer-events="none"/>
        `;
      }
    }

    // Toolbar (edit mode only)
    const toolbar = editMode ? `
      <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center">
        <div style="display:flex;gap:4px;background:var(--sm-bg3);padding:4px;border-radius:10px">
          <button class="sm-btn ${this._floorplanDrawTool==='rect'?'primary':'ghost'} sm"
                  data-fp-tool="rect" title="Tegn rektangel [R]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
            </svg> Rektangel
          </button>
          <button class="sm-btn ${this._floorplanDrawTool==='polygon'?'primary':'ghost'} sm"
                  data-fp-tool="polygon" title="Tegn polygon [P] (dobbeltklik afslutter)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polygon points="12 2 22 20 2 20"/>
            </svg> Polygon
          </button>
          <button class="sm-btn ${this._floorplanDrawTool==='opening'?'primary':'ghost'} sm"
                  data-fp-tool="opening" title="Marker dor eller vindue [O] (traek en linje)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <rect x="2" y="10" width="20" height="4" rx="1"/>
              <line x1="9" y1="10" x2="9" y2="14"/>
              <line x1="15" y1="10" x2="15" y2="14"/>
            </svg> Dor/Vindue
          </button>
        </div>
        ${this._floorplanSelectedRoom ? `
          <button class="sm-btn ghost sm" data-fp-delete-room style="color:var(--sm-danger)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
            </svg> Slet rum
          </button>
        ` : ""}
        <div style="flex:1"></div>
        ${this._floorplanDrawing ? `
          <button class="sm-btn ghost sm" data-fp-cancel-draw>Annuller</button>
        ` : ""}
        <button class="sm-btn ghost" data-fp-upload ${this._floorplanUploading ? "disabled" : ""}>
          ${icon("upload")} Erstat billede
        </button>
        <button class="sm-btn primary" data-fp-exit-edit>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg> Færdig
        </button>
      </div>
    ` : "";

    // Bottom bar (view mode)
    const viewBar = (!editMode && !liveMode) ? `
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
        <button class="sm-btn primary sm" data-fp-enter-edit>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg> Rediger planløsning
        </button>
        <button class="sm-btn ghost sm" data-fp-upload ${this._floorplanUploading ? "disabled" : ""}>
          ${icon("upload")} Erstat billede
        </button>
        <button class="sm-btn ghost sm" data-fp-delete style="color:var(--sm-danger)">
          ${icon("trash")} Slet
        </button>
      </div>
    ` : "";

    // Room inspector panel (edit mode, room selected)
    const selectedRoom = editMode && this._floorplanSelectedRoom
      ? (rooms[this._floorplanSelectedRoom] || null)
      : null;
    // Opening inspector (edit mode, opening selected)
    const selOpIdx = this._floorplanSelectedOpening;
    const selectedOpening = (editMode && selOpIdx !== null)
      ? ((fp.openings || [])[selOpIdx] || null)
      : null;
    const openingInspector = selectedOpening
      ? this._renderOpeningInspector(selOpIdx, selectedOpening)
      : "";
    const inspectorPanel = selectedRoom
      ? this._renderRoomInspector(this._floorplanSelectedRoom, selectedRoom)
      : openingInspector;

    // Edit mode hint
    const editHint = (editMode && !this._floorplanSelectedRoom && !this._floorplanDrawing) ? `
      <div class="sm-card" style="padding:10px 14px;margin-bottom:10px;
           background:rgba(124,58,237,0.07);border-color:var(--sm-accent);
           font-size:13px;color:var(--sm-text-secondary)">
        <strong style="color:var(--sm-accent)">Tegnetips:</strong>
        Vælg et tegneværktøj og klik på kortet for at tegne et rum.
        <br><span style="font-size:11px;color:var(--sm-text-tertiary)">
          R = Rektangel &nbsp;&bull;&nbsp; P = Polygon &nbsp;&bull;&nbsp; O = Dør/Vindue
          &nbsp;&bull;&nbsp; Delete = Slet valgt &nbsp;&bull;&nbsp; Ctrl+Z = Fortryd &nbsp;&bull;&nbsp; Esc = Annuller
        </span>
        Klik på et eksisterende rum for at redigere det.
        ${this._floorplanDrawTool === 'polygon' ? ' Dobbeltklik for at afslutte polygonen.' : ''}
        ${this._floorplanDrawTool === 'opening' ? ' Traek en linje for at markere en dor eller et vindue. Klik paa markeringen for at slette den.' : ''}
      </div>
    ` : "";

    return `
      ${toolbar}
      ${editHint}
      <div class="sm-card" style="padding:0;overflow:hidden;position:relative">
        <div style="position:relative;width:100%;padding-bottom:${(aspectRatio*100).toFixed(2)}%;
                    background:#111;user-select:none;-webkit-user-select:none;touch-action:none"
             data-fp-canvas>

          <!-- PNG background — always visible -->
          <img src="${cacheBust}" alt="Etageplan" draggable="false"
               style="position:absolute;inset:0;width:100%;height:100%;
                      object-fit:contain;pointer-events:none;-webkit-user-drag:none">

          <!-- SVG overlay — rooms drawn on top of PNG -->
          <svg viewBox="0 0 ${VW} ${VH}"
               style="position:absolute;inset:0;width:100%;height:100%;
                      pointer-events:${editMode ? 'all' : 'none'}"
               data-fp-svg>
            <defs>
              <filter id="fp-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="8" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            ${svgRooms}
            ${svgOpenings}
            ${svgSensorPins}
            ${previewSvg}
          </svg>

          <!-- Live room labels overlay -->
          ${liveMode ? `
            <div style="position:absolute;inset:0;pointer-events:none">
              ${roomEntries.map(([rid, room], idx) => {
                const pts = room.points || [];
                if (pts.length < 3) return "";
                const isActive = this._fpRoomIsActive(room);
                const cx = pts.reduce((s,[x])=>s+x,0)/pts.length;
                const cy = pts.reduce((s,[,y])=>s+y,0)/pts.length;
                const color = room.color || this._fpRoomColor(idx);
                return `
                  <div data-fp-label="${rid}"
                       style="position:absolute;left:${cx}%;top:${cy}%;
                              transform:translate(-50%,-50%);
                              background:${color}cc;
                              color:#fff;font-size:11px;font-weight:700;
                              padding:3px 8px;border-radius:6px;
                              white-space:nowrap;pointer-events:none;
                              box-shadow:0 2px 8px rgba(0,0,0,0.5);
                              transition:opacity 0.4s ease;
                              opacity:${isActive ? 1 : 0}">
                    ${room.name || "Rum"}
                  </div>
                `;
              }).join("")}
            </div>
          ` : ""}
        </div>
      </div>

      <div data-fp-inspector>${inspectorPanel}</div>
      ${viewBar}
    `;
  }

  _renderRoomInspector(roomId, room) {
    const allSensors = this._fpAvailableSensors();
    const assigned   = room.sensors || [];
    const unassigned = allSensors.filter(s => !assigned.includes(s.entity_id));

    return `
      <div class="sm-card" style="margin-top:10px;border-color:var(--sm-accent)">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
          <div style="flex:1">
            <input type="text" class="form-input" data-fp-room-name
                   value="${room.name || ""}"
                   placeholder="Rummets navn (fx Køkken)"
                   style="font-size:14px;font-weight:600">
          </div>
          <input type="color" data-fp-room-color value="${room.color || '#7c3aed'}"
                 title="Vælg farve"
                 style="width:36px;height:36px;border:none;border-radius:8px;
                        cursor:pointer;background:none;padding:0">
        </div>

        <div style="font-size:12px;font-weight:600;color:var(--sm-text-tertiary);
                    text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">
          Sensorer tilknyttet dette rum
        </div>

        ${assigned.length === 0 ? `
          <div style="font-size:13px;color:var(--sm-text-tertiary);font-style:italic;margin-bottom:10px">
            Ingen sensorer tilknyttet endnu
          </div>
        ` : `
          <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:10px">
            ${assigned.map(eid => {
              const s = (this._data.sensors||[]).find(x=>x.entity_id===eid);
              return `
                <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;
                            background:var(--sm-bg3);border-radius:8px;font-size:13px">
                  <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                    ${s ? s.name : eid}
                  </span>
                  <span style="font-size:11px;color:var(--sm-text-tertiary);font-family:monospace;
                               overflow:hidden;text-overflow:ellipsis;max-width:140px">${eid}</span>
                  <button class="sm-btn ghost sm" data-fp-remove-sensor="${eid}"
                          style="padding:2px 6px;color:var(--sm-danger);flex-shrink:0">&times;</button>
                </div>
              `;
            }).join("")}
          </div>
        `}

        ${unassigned.length > 0 ? `
          <div data-fp-sensor-picker
               data-fp-sensor-data="${encodeURIComponent(JSON.stringify(unassigned.map(s=>({eid:s.entity_id,name:s.name,dc:s.device_class||''}))))}">
            <input type="text" class="form-input" data-fp-sensor-search
                   placeholder="+ Tilfoej sensor til rum..."
                   autocomplete="off"
                   style="width:100%;padding:8px 12px;font-size:13px;cursor:pointer;box-sizing:border-box">
          </div>
        ` : `
          <div style="font-size:12px;color:var(--sm-text-tertiary);font-style:italic">
            Alle tilgaengelige sensorer er tildelt.
          </div>
        `}
      </div>
    `;
  }

  _renderOpeningInspector(idx, op) {
    const color = op.type === "window" ? "#fbbf24" : "#e2e8f0";
    // Available door/window sensors from the sensor list.
    // _data.sensors may be empty if load failed -- show a helpful message
    // rather than a silently empty <select>.
    const allSensors = this._data.sensors || [];
    const openingSensors = allSensors.filter(s => {
      const dc = s.device_class || "";
      return ["door","window","opening","garage_door"].includes(dc);
    });
    const currentEid = op.entity_id || "";
    const sensorsEmpty = allSensors.length === 0;
    const noOpeningSensors = !sensorsEmpty && openingSensors.length === 0;
    const sensorOptions = [
      '<option value="">-- Ingen sensor --</option>',
      ...openingSensors.map(s =>
        `<option value="${s.entity_id}"${s.entity_id === currentEid ? " selected" : ""}>${s.name} (${s.entity_id})</option>`
      ),
      // Keep current value even if not in list (e.g. sensor removed from HA)
      ...(!openingSensors.find(s => s.entity_id === currentEid) && currentEid
        ? [`<option value="${currentEid}" selected>${currentEid}</option>`]
        : []),
    ].join("");

    return `
      <div class="sm-card" style="margin-top:10px;border-color:${color}">
        <div style="font-size:12px;font-weight:600;color:var(--sm-text-tertiary);
                    text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px">
          Markering: ${op.type === "window" ? "Vindue" : "Dor"}
        </div>
        <div style="display:flex;gap:8px;margin-bottom:10px">
          <button class="sm-btn ${op.type !== "window" ? "primary" : "ghost"} sm"
                  data-fp-opening-type="${idx}" data-fp-opening-val="door">
            Dor
          </button>
          <button class="sm-btn ${op.type === "window" ? "primary" : "ghost"} sm"
                  data-fp-opening-type="${idx}" data-fp-opening-val="window">
            Vindue
          </button>
          <div style="flex:1"></div>
          <button class="sm-btn ghost sm" data-fp-opening-delete="${idx}"
                  style="color:var(--sm-danger)">
            ${icon("trash")} Slet
          </button>
        </div>
        <div style="margin-bottom:8px">
          <div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:4px;font-weight:600">
            Sensor (vises live ved aabning)
          </div>
          ${sensorsEmpty ? `
            <div style="font-size:12px;color:var(--sm-warning,#f59e0b);padding:8px 10px;
                        background:rgba(245,158,11,0.1);border-radius:8px;margin-bottom:4px">
              Sensorer ikke indlaedt endnu.
              <button class="sm-btn ghost sm" data-fp-reload-sensors
                      style="margin-left:8px;padding:2px 8px;font-size:11px">
                Genindlaes
              </button>
            </div>
          ` : noOpeningSensors ? `
            <div style="font-size:12px;color:var(--sm-text-tertiary);padding:6px 0;font-style:italic">
              Ingen dor/vindue-sensorer fundet i Home Assistant.
            </div>
          ` : ``}
          <select class="sm-input" style="width:100%;font-size:12px"
                  data-fp-opening-entity="${idx}">
            ${sensorOptions}
          </select>
        </div>
        <div style="font-size:12px;color:var(--sm-text-tertiary)">
          Klik paa markeringen paa kortet for at aendre type eller slette den.
        </div>
      </div>
    `;
  }

  // ─── Floorplan inspector in-place update ─────────────────────────────────

  // Opdaterer kun inspector-panelet in-place (sensor liste + dropdown) uden
  // at genopbygge hele main-content. Dette er kritisk for at undga at
  // browser-events (change, click) afbrydes af DOM-destruktion.
  _fpAttachSensorPicker(container) {
    const picker = container.querySelector("[data-fp-sensor-picker]");
    if (!picker) return;
    if (picker._smPickerAttached) return;
    picker._smPickerAttached = true;

    const searchInput = picker.querySelector("[data-fp-sensor-search]");
    if (!searchInput) return;

    let sensors = [];
    try {
      sensors = JSON.parse(decodeURIComponent(picker.dataset.fpSensorData || "[]"));
    } catch (_) { return; }

    const OLD_LIST_ID = "sm-fp-sensor-flyout";
    const existing = this.shadowRoot.getElementById(OLD_LIST_ID);
    if (existing) { if (existing._smCleanup) existing._smCleanup(); existing.remove(); }

    const flyout = document.createElement("div");
    flyout.id = OLD_LIST_ID;
    flyout.style.cssText = [
      "position:fixed","z-index:99999","background:#1a1a2e",
      "border:1px solid #4a4a6a","border-radius:10px","max-height:260px",
      "overflow-y:auto","overflow-x:hidden",
      "box-shadow:0 8px 32px rgba(0,0,0,0.9)","display:none","min-width:260px",
    ].join(";");

    flyout.innerHTML = sensors.map(s => `
      <div data-sm-eid="${s.eid}"
           style="padding:10px 14px;font-size:13px;cursor:pointer;
                  display:flex;flex-direction:column;gap:2px;
                  border-bottom:1px solid #2a2a4a">
        <span style="color:#e8e8f0;font-weight:500;white-space:nowrap;
                     overflow:hidden;text-overflow:ellipsis">${s.name}</span>
        <span style="color:#8888aa;font-size:11px;font-family:monospace;
                     white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${s.eid}</span>
      </div>
    `).join("");

    this.shadowRoot.appendChild(flyout);

    const positionFlyout = () => {
      if (!searchInput.isConnected) return;
      const rect = searchInput.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const spaceAbove = rect.top - 8;
      const flyH = Math.min(260, sensors.length * 60 + 8);
      flyout.style.left  = rect.left + "px";
      flyout.style.width = rect.width + "px";
      if (spaceBelow >= flyH || spaceBelow >= spaceAbove) {
        flyout.style.top = (rect.bottom + 4) + "px"; flyout.style.bottom = "auto";
      } else {
        flyout.style.bottom = (window.innerHeight - rect.top + 4) + "px"; flyout.style.top = "auto";
      }
    };

    const filterFlyout = (q) => {
      const lq = q.toLowerCase();
      flyout.querySelectorAll("[data-sm-eid]").forEach(opt => {
        opt.style.display = opt.textContent.toLowerCase().includes(lq) ? "" : "none";
      });
    };

    const showFlyout = () => {
      positionFlyout(); flyout.style.display = "block"; filterFlyout(searchInput.value);
    };
    const hideFlyout = () => {
      flyout.style.display = "none"; this._fpActiveFlyout = null;
    };

    this._fpActiveFlyout = flyout;

    // pointerdown med capture:true + stopImmediatePropagation:
    // korer FOER onDocPointer og blokerer det -- flyout lukkes ikke ved klik paa option.
    // preventDefault() forhindrer blur paa searchInput.
    const selectOption = (eid) => {
      if (!eid) return;
      const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
      if (r) {
        if (!r.sensors) r.sensors = [];
        if (!r.sensors.includes(eid)) { r.sensors.push(eid); this._fpSaveRooms(); }
      }
      searchInput.value = "";
      hideFlyout();
      this._fpUpdateInspector();
    };

    flyout.addEventListener("pointerdown", e => {
      e.preventDefault();
      e.stopImmediatePropagation();
      const opt = e.target.closest("[data-sm-eid]");
      if (opt?.dataset?.smEid) selectOption(opt.dataset.smEid);
    }, { capture: true });

    flyout.addEventListener("touchend", e => {
      e.preventDefault(); e.stopImmediatePropagation();
      const touch = e.changedTouches[0];
      const el = this.shadowRoot.elementFromPoint
        ? this.shadowRoot.elementFromPoint(touch.clientX, touch.clientY)
        : document.elementFromPoint(touch.clientX, touch.clientY);
      const opt = el?.closest("[data-sm-eid]");
      if (opt?.dataset?.smEid) selectOption(opt.dataset.smEid);
    }, { capture: true });

    flyout.addEventListener("pointermove", e => {
      const opt = e.target.closest("[data-sm-eid]");
      flyout.querySelectorAll("[data-sm-eid]").forEach(o => {
        o.style.background = o === opt ? "#2a2a4a" : "";
      });
    });

    searchInput.addEventListener("focus", showFlyout);
    searchInput.addEventListener("click", showFlyout);
    searchInput.addEventListener("input", e => { showFlyout(); filterFlyout(e.target.value); });

    // Ingen capture -- korer EFTER flyouts capture handler.
    // stopImmediatePropagation() paa flyout forhindrer at denne ser klik paa options.
    const onDocPointer = e => {
      const path = e.composedPath ? e.composedPath() : [];
      if (path.includes(flyout) || path.includes(searchInput)) return;
      hideFlyout();
    };
    document.addEventListener("pointerdown", onDocPointer);

    const panelScroll = this.shadowRoot.getElementById("shell-main");
    const onPanelScroll = () => { if (flyout.style.display === "block") positionFlyout(); };
    if (panelScroll) panelScroll.addEventListener("scroll", onPanelScroll, { passive: true });

    flyout._smCleanup = () => {
      document.removeEventListener("pointerdown", onDocPointer);
      if (panelScroll) panelScroll.removeEventListener("scroll", onPanelScroll);
    };
  }
  _fpUpdateInspector() {
    // Fjern aktiv flyout foer inspector rebuildes saa den ikke flyder rundt
    if (this._fpActiveFlyout) {
      if (this._fpActiveFlyout._smCleanup) this._fpActiveFlyout._smCleanup();
      this._fpActiveFlyout.remove();
      this._fpActiveFlyout = null;
    }
    if (!this._floorplanSelectedRoom) return;
    const root = this.shadowRoot;
    const room = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
    if (!room) return;

    const container = root.querySelector("[data-fp-inspector]");
    if (!container) {
      // Inspector-containeren findes ikke i DOM -- fald tilbage til fuld render
      this._render();
      return;
    }

    container.innerHTML = this._renderRoomInspector(this._floorplanSelectedRoom, room);

    // Genophaeng listeners for den nye inspector-DOM
    this._fpAttachSensorPicker(container);

    container.querySelectorAll("[data-fp-remove-sensor]").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        const eid = btn.dataset.fpRemoveSensor;
        const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
        if (r?.sensors) {
          r.sensors = r.sensors.filter(s => s !== eid);
          this._fpUpdateInspector();
          this._fpSaveRooms();
        }
      });
    });

    const nameInput = container.querySelector("[data-fp-room-name]");
    if (nameInput) {
      nameInput.addEventListener("input", e => {
        const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
        if (r) { r.name = e.target.value; this._fpSaveRoomsDebounced(); }
      });
    }

    const colorInput = container.querySelector("[data-fp-room-color]");
    if (colorInput) {
      colorInput.addEventListener("input", e => {
        const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
        if (r) { r.color = e.target.value; this._fpSaveRoomsDebounced(); this._render(); }
      });
    }
  }

  // ─── Floorplan helper methods ─────────────────────────────────────────────

  _isHomeAloneLiveActive() {
    return this._alarmState === 'armed_home_alone';
  }

  _sensorIsActive(entityId) {
    const st = this._hass?.states?.[entityId];
    return st ? st.state === 'on' : false;
  }

  _sensorFriendlyName(entityId) {
    const sensor = (this._data.sensors || []).find(s => s.entity_id === entityId);
    return sensor ? sensor.name : entityId;
  }

  // ─── Canvas events ────────────────────────────────────────────────────────

  _attachFloorplanListeners() {
    const root     = this.shadowRoot;
    const liveMode = this._isHomeAloneLiveActive();
    const editMode = this._floorplanEditMode && !liveMode;

    // Upload
    root.querySelectorAll("[data-fp-upload]").forEach(btn => {
      btn.addEventListener("click", () => {
        root.querySelector("[data-fp-file-input]")?.click();
      });
    });

    const fileInput = root.querySelector("[data-fp-file-input]");
    if (fileInput) {
      fileInput.addEventListener("change", e => {
        const file = e.target.files?.[0];
        if (file) this._fpUploadImage(file);
        e.target.value = "";
      });
    }

    // Delete floorplan
    root.querySelectorAll("[data-fp-delete]").forEach(btn => {
      btn.addEventListener("click", () => this._fpDeleteFloorplan());
    });

    // Enter / exit edit mode
    root.querySelectorAll("[data-fp-enter-edit]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._fpUndoStack = [];
        this._floorplanEditMode    = true;
        this._floorplanSelectedRoom = null;
        this._floorplanDrawing      = null;
        this._fpAttachKeyboard();
        this._render();
      });
    });
    root.querySelectorAll("[data-fp-exit-edit]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._floorplanEditMode    = false;
        this._floorplanSelectedRoom = null;
        this._floorplanDrawing      = null;
        this._fpDetachKeyboard();
        this._render();
      });
    });

    // Cancel in-progress draw
    root.querySelectorAll("[data-fp-cancel-draw]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._floorplanDrawing = null;
        this._render();
      });
    });

    // Tool selector
    root.querySelectorAll("[data-fp-tool]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._floorplanDrawTool = btn.dataset.fpTool;
        this._floorplanDrawing  = null;
        this._floorplanSelectedRoom = null;
        this._render();
      });
    });

    // Delete selected room
    root.querySelectorAll("[data-fp-delete-room]").forEach(btn => {
      btn.addEventListener("click", () => {
        if (!this._floorplanSelectedRoom) return;
        this._fpSnapshotForUndo();
        delete this._data.floorplan.rooms[this._floorplanSelectedRoom];
        this._floorplanSelectedRoom = null;
        this._render();
        this._fpSaveRooms();
      });
    });

    if (editMode) {
      // Room inspector: name
      const nameInput = root.querySelector("[data-fp-room-name]");
      if (nameInput) {
        nameInput.addEventListener("input", e => {
          const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
          if (r) { r.name = e.target.value; this._fpSaveRoomsDebounced(); }
        });
      }

      // Room inspector: color
      const colorInput = root.querySelector("[data-fp-room-color]");
      if (colorInput) {
        colorInput.addEventListener("input", e => {
          const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
          if (r) { r.color = e.target.value; this._fpSaveRoomsDebounced(); this._render(); }
        });
      }

      // Room inspector: add sensor via custom picker
      // _fpAttachSensorPicker bruger mousedown (ikke change/click) saa listen
      // ikke lukker sig selv foer vaelget er registreret.
      const inspectorContainer = root.querySelector("[data-fp-inspector]");
      if (inspectorContainer) {
        this._fpAttachSensorPicker(inspectorContainer);
      }

      // Room inspector: remove sensor
      root.querySelectorAll("[data-fp-remove-sensor]").forEach(btn => {
        btn.addEventListener("click", e => {
          e.stopPropagation();
          const eid = btn.dataset.fpRemoveSensor;
          const r = this._data.floorplan?.rooms?.[this._floorplanSelectedRoom];
          if (r?.sensors) {
            r.sensors = r.sensors.filter(s => s !== eid);
            this._fpUpdateInspector();
            this._fpSaveRooms();
          }
        });
      });
    }

    // Opening inspector: type-skift (dor/vindue)
    root.querySelectorAll("[data-fp-opening-type]").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        const oi  = parseInt(btn.dataset.fpOpeningType, 10);
        const val = btn.dataset.fpOpeningVal;
        const fp  = this._data.floorplan;
        if (!isNaN(oi) && fp?.openings?.[oi]) {
          fp.openings[oi].type  = val;
          fp.openings[oi].label = val === "window" ? "Vindue" : "Dor";
          this._render();
          this._fpSaveRooms();
        }
      });
    });

    // Opening inspector: tilknyt sensor
    root.querySelectorAll("[data-fp-opening-entity]").forEach(sel => {
      sel.addEventListener("change", e => {
        const oi  = parseInt(sel.dataset.fpOpeningEntity, 10);
        const fp  = this._data.floorplan;
        if (!isNaN(oi) && fp?.openings?.[oi]) {
          fp.openings[oi].entity_id = e.target.value || null;
          this._fpSaveRooms();
        }
      });
    });

    // Opening inspector: slet
    root.querySelectorAll("[data-fp-opening-delete]").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        const oi = parseInt(btn.dataset.fpOpeningDelete, 10);
        const fp = this._data.floorplan;
        if (!isNaN(oi) && fp?.openings) {
          this._fpSnapshotForUndo();
          fp.openings.splice(oi, 1);
          this._floorplanSelectedOpening = null;
          this._render();
          this._fpSaveRooms();
        }
      });
    });

    // Reload sensors button (shown when _data.sensors is empty)
    root.querySelectorAll("[data-fp-reload-sensors]").forEach(btn => {
      btn.addEventListener("click", async e => {
        e.stopPropagation();
        btn.disabled = true;
        btn.textContent = "...";
        await this._loadData();
        this._render();
      });
    });

    // Undo button
    root.querySelectorAll("[data-fp-undo]").forEach(btn => {
      btn.addEventListener("click", e => { e.stopPropagation(); this._fpUndo(); });
    });

    // Canvas events
    const canvas = root.querySelector("[data-fp-canvas]");
    if (canvas && editMode) this._fpAttachCanvasEvents(canvas);
  }

  _fpAttachCanvasEvents(canvas) {
    const svg = canvas.querySelector("[data-fp-svg]");

    // Utility: convert client coords to SVG % coords
    const toSvgPct = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect();
      return [
        Math.max(0, Math.min(100, (clientX - rect.left) / rect.width  * 100)),
        Math.max(0, Math.min(100, (clientY - rect.top)  / rect.height * 100)),
      ];
    };

    // ── Handle drag (move polygon vertex) ────────────────────────────────
    let handleDrag = null;
    svg.addEventListener("pointerdown", e => {
      const handleEl = e.target.closest(".fp-handle");
      if (!handleEl) return;
      e.stopPropagation();
      const [rid, piStr] = handleEl.dataset.fpHandle.split("-");
      handleDrag = { rid, pi: parseInt(piStr), pointerId: e.pointerId };
      try { svg.setPointerCapture(e.pointerId); } catch (_) {}
    }, { capture: true });

    svg.addEventListener("pointermove", e => {
      if (!handleDrag || e.pointerId !== handleDrag.pointerId) return;
      const [x, y] = toSvgPct(e.clientX, e.clientY);
      const r = this._data.floorplan?.rooms?.[handleDrag.rid];
      if (r?.points?.[handleDrag.pi]) {
        r.points[handleDrag.pi] = [x, y];
        // Live-update the handle and polygon in DOM
        this._fpLivePatchPolygon(svg, handleDrag.rid, r);
      }
    });

    svg.addEventListener("pointerup", e => {
      if (!handleDrag || e.pointerId !== handleDrag.pointerId) return;
      try { svg.releasePointerCapture(e.pointerId); } catch (_) {}
      handleDrag = null;
      this._fpSaveRoomsDebounced();
    });

    // ── Click on canvas ───────────────────────────────────────────────────
    canvas.addEventListener("click", e => {
      if (handleDrag) return; // was a handle drag
      const [x, y] = toSvgPct(e.clientX, e.clientY);

      // Did user click an existing opening marker (select it)?
      const openingEl = e.target.closest("[data-fp-opening]");
      if (openingEl && !this._floorplanDrawing) {
        const oi = parseInt(openingEl.dataset.fpOpening, 10);
        if (!isNaN(oi)) {
          this._floorplanSelectedOpening = (this._floorplanSelectedOpening === oi) ? null : oi;
          this._floorplanSelectedRoom = null;
          this._render();
        }
        return;
      }

      // Did user click an existing room?
      const roomEl = e.target.closest("[data-fp-room]");
      if (roomEl && !this._floorplanDrawing) {
        this._floorplanSelectedRoom = roomEl.dataset.fpRoom;
        this._render();
        return;
      }

      // Click outside any room in drawing mode
      if (!this._floorplanDrawing) {
        // Start a new draw
        this._floorplanSelectedRoom = null;
        if (this._floorplanDrawTool === "rect") {
          this._floorplanDrawing = { tool: "rect", points: [[x, y]], mouse: [x, y] };
        } else if (this._floorplanDrawTool === "opening") {
          // Opening tool: start a line (mousedown start, mouseup end)
          // We store the start point here; mouseup finalises it.
          this._floorplanDrawing = { tool: "opening", points: [[x, y]], mouse: [x, y] };
          this._render();
          return;
        } else {
          this._floorplanDrawing = { tool: "polygon", points: [[x, y]], mouse: [x, y] };
        }
        this._render();
        return;
      }

      // Continuing polygon draw
      if (this._floorplanDrawing.tool === "polygon") {
        this._floorplanDrawing.points.push([x, y]);
        this._floorplanDrawing.mouse = [x, y];
        this._render();
      }
    });

    // ── Double-click: finish polygon or rect ──────────────────────────────
    canvas.addEventListener("dblclick", e => {
      if (!this._floorplanDrawing) return;
      e.preventDefault();
      const [x, y] = toSvgPct(e.clientX, e.clientY);

      if (this._floorplanDrawing.tool === "polygon") {
        const pts = this._floorplanDrawing.points;
        if (pts.length >= 3) {
          this._fpFinaliseRoom(pts);
        } else {
          this._floorplanDrawing = null;
          this._render();
        }
      }
    });

    // ── Rect: mousemove for live preview ──────────────────────────────────
    // Pointer events til preview + finalise (touch + mouse)
    let drawPointerId = null;
    canvas.addEventListener("pointerdown", e => {
      if (e.target.closest(".fp-handle")) return;
      if (!this._floorplanDrawing) return;
      if (this._floorplanDrawing.tool !== "opening" && this._floorplanDrawing.tool !== "rect") return;
      drawPointerId = e.pointerId;
      try { canvas.setPointerCapture(e.pointerId); } catch (_) {}
    });
    canvas.addEventListener("pointermove", e => {
      if (!this._floorplanDrawing) return;
      const [x, y] = toSvgPct(e.clientX, e.clientY);
      this._floorplanDrawing.mouse = [x, y];
      this._fpLivePreview(svg, x, y);
    });
    canvas.addEventListener("pointerup", e => {
      if (!this._floorplanDrawing) return;
      if (drawPointerId !== null && e.pointerId !== drawPointerId) return;
      try { canvas.releasePointerCapture(e.pointerId); } catch (_) {}
      drawPointerId = null;
      const [x, y] = toSvgPct(e.clientX, e.clientY);
      if (this._floorplanDrawing.tool === "opening") {
        if (this._floorplanDrawing.points.length !== 1) return;
        const [x1, y1] = this._floorplanDrawing.points[0];
        const dist = Math.sqrt((x-x1)**2 + (y-y1)**2);
        if (dist < 1.5) { this._floorplanDrawing = null; this._render(); return; }
        this._fpFinaliseOpening([x1, y1], [x, y]); return;
      }
      if (this._floorplanDrawing.tool !== "rect") return;
      if (this._floorplanDrawing.points.length !== 1) return;
      const [x1, y1] = this._floorplanDrawing.points[0];
      const w = Math.abs(x - x1), h = Math.abs(y - y1);
      if (w < 1 || h < 1) return;
      const x0 = Math.min(x, x1), y0 = Math.min(y, y1);
      const x2 = Math.max(x, x1), y2 = Math.max(y, y1);
      this._fpFinaliseRoom([[x0,y0],[x2,y0],[x2,y2],[x0,y2]]);
    });
    canvas.addEventListener("mousemove", e => {
      if (!this._floorplanDrawing) return;
      const [x, y] = toSvgPct(e.clientX, e.clientY);
      this._floorplanDrawing.mouse = [x, y];
      this._fpLivePreview(svg, x, y);
    });

    // Click on empty area outside a room/opening deselects
    canvas.addEventListener("click", e => {
      if (this._floorplanDrawing) return;
      if (e.target.closest("[data-fp-room]")) return;
      if (e.target.closest("[data-fp-opening]")) return;
      if (this._floorplanSelectedRoom || this._floorplanSelectedOpening !== null) {
        this._floorplanSelectedRoom = null;
        this._floorplanSelectedOpening = null;
        this._render();
      }
    });
  }

  _fpFinaliseRoom(points) {
    if (!this._data.floorplan) return;
    if (!this._data.floorplan.rooms) this._data.floorplan.rooms = {};
    this._fpSnapshotForUndo();
    const rooms  = this._data.floorplan.rooms;
    const idx    = Object.keys(rooms).length;
    const rid    = this._fpNewRoomId();
    rooms[rid] = {
      name:    "Rum " + (idx + 1),
      color:   this._fpRoomColor(idx),
      points,
      sensors: [],
    };
    this._floorplanDrawing      = null;
    this._floorplanSelectedRoom = rid;
    this._render();
    this._fpSaveRooms();
  }

  _fpFinaliseOpening(p1, p2) {
    if (!this._data.floorplan) return;
    if (!this._data.floorplan.openings) this._data.floorplan.openings = [];
    this._fpSnapshotForUndo();
    this._data.floorplan.openings.push({
      type: "door",   // default — bruger kan skifte via inspector
      label: "Dor",
      points: [p1, p2],
    });
    this._floorplanDrawing = null;
    this._floorplanSelectedOpening = null;
    this._render();
    this._fpSaveRooms();
  }

  _fpLivePatchPolygon(svg, rid, room) {
    const VW = 1000;
    const fp  = this._data.floorplan;
    const VH  = Math.round(VW * (fp.width && fp.height ? fp.height / fp.width : 0.6));
    const polyEl = svg.querySelector(`[data-fp-room="${rid}"]`);
    if (!polyEl) return;
    polyEl.setAttribute("points", this._fpPointsToSvgPolygon(room.points, VW, VH));
    // Update handle positions
    room.points.forEach(([x,y], pi) => {
      const h = svg.querySelector(`[data-fp-handle="${rid}-${pi}"]`);
      if (h) {
        h.setAttribute("cx", (x/100*VW).toFixed(1));
        h.setAttribute("cy", (y/100*VH).toFixed(1));
      }
    });
    // Update label
    const cx = room.points.reduce((s,[x])=>s+x,0)/room.points.length;
    const cy = room.points.reduce((s,[,y])=>s+y,0)/room.points.length;
    const label = svg.querySelector(`[data-fp-label="${rid}"]`);
    if (label) {
      label.setAttribute("x", (cx/100*VW).toFixed(1));
      label.setAttribute("y", (cy/100*VH).toFixed(1));
    }
  }

  _fpLivePreview(svg, mx, my) {
    // Update dashed preview line/rect without full re-render
    const drawing = this._floorplanDrawing;
    if (!drawing) return;
    const fp = this._data.floorplan;
    const VW = 1000;
    const VH = Math.round(VW * (fp.width && fp.height ? fp.height / fp.width : 0.6));

    if (drawing.tool === "polygon") {
      const pts = drawing.points;
      const lastPt = pts[pts.length - 1];
      let previewLine = svg.querySelector(".fp-preview-line");
      if (!previewLine) {
        previewLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
        previewLine.classList.add("fp-preview-line");
        previewLine.setAttribute("stroke", "#7c3aed");
        previewLine.setAttribute("stroke-width", "1.5");
        previewLine.setAttribute("stroke-dasharray", "6,4");
        previewLine.setAttribute("opacity", "0.7");
        previewLine.setAttribute("pointer-events", "none");
        svg.appendChild(previewLine);
      }
      previewLine.setAttribute("x1", (lastPt[0]/100*VW).toFixed(1));
      previewLine.setAttribute("y1", (lastPt[1]/100*VH).toFixed(1));
      previewLine.setAttribute("x2", (mx/100*VW).toFixed(1));
      previewLine.setAttribute("y2", (my/100*VH).toFixed(1));
    } else if (drawing.tool === "rect" && drawing.points.length === 1) {
      const [x1, y1] = drawing.points[0];
      const rx = Math.min(x1, mx)/100*VW, ry = Math.min(y1, my)/100*VH;
      const rw = Math.abs(mx - x1)/100*VW, rh = Math.abs(my - y1)/100*VH;
      let previewRect = svg.querySelector(".fp-preview-rect");
      if (!previewRect) {
        previewRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        previewRect.classList.add("fp-preview-rect");
        previewRect.setAttribute("fill", "#7c3aed");
        previewRect.setAttribute("fill-opacity", "0.12");
        previewRect.setAttribute("stroke", "#7c3aed");
        previewRect.setAttribute("stroke-width", "2");
        previewRect.setAttribute("stroke-dasharray", "6,4");
        previewRect.setAttribute("pointer-events", "none");
        svg.appendChild(previewRect);
      }
      previewRect.setAttribute("x", rx.toFixed(1));
      previewRect.setAttribute("y", ry.toFixed(1));
      previewRect.setAttribute("width", rw.toFixed(1));
      previewRect.setAttribute("height", rh.toFixed(1));
    }
  }

  // ─── WS persistence ───────────────────────────────────────────────────────

  async _fpSaveRooms() {
    const rooms    = this._data.floorplan?.rooms    || {};
    const openings = this._data.floorplan?.openings || [];
    const result   = await this._callWS("save_floorplan_markers", { rooms, openings });
    if (!result?.success) {
      this._toast("Kunne ikke gemme rum: " + (result?.error || "ukendt fejl"), "error");
      await this._loadFloorplan();
    }
  }

  _fpSaveRoomsDebounced() {
    clearTimeout(this._fpSaveDebounce);
    this._fpSaveDebounce = setTimeout(() => this._fpSaveRooms(), 800);
  }

  async _fpUploadImage(file) {
    if (this._floorplanUploading) return;
    const MAX = 4 * 1024 * 1024;
    if (file.size > MAX) {
      this._toast(`Billedet er ${(file.size/1024/1024).toFixed(1)} MB — maks er 4 MB.`, "error");
      return;
    }
    if (file.type && file.type !== "image/png") {
      this._toast("Kun PNG-billeder er understøttet.", "error");
      return;
    }
    this._floorplanUploading = true;
    this._render();
    try {
      const base64 = await this._fileToBase64(file);
      const result = await this._callWS("save_floorplan_image", { image_base64: base64 });
      if (result?.success) {
        this._floorplanCacheBust = Date.now();
        await this._loadFloorplan();
        this._toast("Planløsning uploadet.", "success");
      } else {
        this._toast("Upload fejlede: " + (result?.error || "ukendt fejl"), "error");
      }
    } catch (err) {
      this._toast("Upload fejlede: " + err.message, "error");
    } finally {
      this._floorplanUploading = false;
      this._render();
    }
  }

  _fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result || "";
        const comma  = result.indexOf(",");
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = () => reject(new Error("Kunne ikke læse filen"));
      reader.readAsDataURL(file);
    });
  }

  async _fpDeleteFloorplan() {
    const ok = window.confirm("Slet planløsning og alle rum?");
    if (!ok) return;
    const result = await this._callWS("delete_floorplan");
    if (result?.success) {
      this._data.floorplan    = { image_url: null, width: 0, height: 0, rooms: {} };
      this._floorplanEditMode = false;
      this._floorplanSelectedRoom = null;
      this._floorplanDrawing  = null;
      this._render();
    }
  }

  // ===
  // TAB: AUTOMATIONS & NOTIFICATIONS
  // ===
  _renderAutomations() {
    const aCacheKey = JSON.stringify({
      n: this._data.notifications, a: this._data.automations, sec: this._autoSection
    });
    if (this._automationsRenderKey === aCacheKey && this._automationsRenderCache) return this._automationsRenderCache;
    const section = this._autoSection;
    const notifications = this._data.notifications || {};
    const automations = this._data.automations || {};

    const __ahtml = `
      <div class="segment-control">
        <button class="segment-btn ${section === "notifications" ? "active" : ""}"
                data-auto-section="notifications">Notifikationer</button>
        <button class="segment-btn ${section === "automations" ? "active" : ""}"
                data-auto-section="automations">Automatiseringer</button>
      </div>

      ${section === "notifications" ? `
        ` + (() => {
          const SYSTEM_TRIGGERS = ['armed','disarmed','triggered','arming','pending','low_battery','smoke','water_leak'];
          const systemNotifs = Object.entries(notifications).filter(([,n]) => SYSTEM_TRIGGERS.includes(n.trigger));
          const customNotifs = Object.entries(notifications).filter(([,n]) => !SYSTEM_TRIGGERS.includes(n.trigger));

          const notifCardInner = (id, n, buttons) => `
            <div class="sm-card" style="padding:12px 14px;display:flex;align-items:center;gap:8px">
              <div style="flex:1;min-width:0">
                <div style="font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${n.name || 'Notification'}</div>
                <div style="display:flex;gap:4px;margin-top:3px;flex-wrap:wrap">
                  ${(n.channels||['push']).includes('push') ? '<span class="badge" style="background:var(--sm-blue-dim);color:var(--sm-blue);font-size:10px;padding:1px 5px">Push</span>' : ''}
                  ${(n.channels||[]).includes('tts') ? '<span class="badge" style="background:var(--sm-purple-dim);color:var(--sm-purple);font-size:10px;padding:1px 5px">TTS</span>' : ''}
                  <span class="badge entry" style="font-size:10px;padding:1px 5px">${n.trigger || ''}</span>
                </div>
              </div>
              <div style="display:flex;gap:3px;flex-shrink:0">${buttons}</div>
            </div>`;

          const systemNotifCard = ([id, n]) => notifCardInner(id, n,
            `<button class="sm-btn default sm" data-test-notif="${id}" title="Test" style="padding:3px 7px">${icon('play')}</button>`);

          const customNotifCard = ([id, n]) => notifCardInner(id, n,
            `<button class="sm-btn default sm" data-test-notif="${id}" title="Test" style="padding:3px 7px">${icon('play')}</button>
             <button class="sm-btn ghost sm" data-edit-notif="${id}" title="Edit" style="padding:3px 7px">${icon('edit')}</button>
             <button class="sm-btn ghost sm" data-delete-notif="${id}" title="Slet" style="padding:3px 7px">${icon('trash')}</button>`);

          return `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div>
              <h3 class="section-title" style="margin:0">Systemnotifikationer</h3>
              <div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:2px">Altid aktiv — dirigeres per bruger. Test sendes kun til admin-brugere.</div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:16px">
            ${systemNotifs.map(systemNotifCard).join('') || '<div style="grid-column:1/-1;text-align:center;color:var(--sm-text-tertiary);font-size:12px;padding:12px">Ingen systemnotifikationer endnu.</div>'}
          </div>

          <div style="border-top:1px solid var(--sm-border);margin:16px 0 12px"></div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div>
              <h3 class="section-title" style="margin:0">Brugerdefinerede notifikationer</h3>
              <div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:2px">Brugerdefinerede alarmer og automatiseringer</div>
            </div>
            <button class="sm-btn primary sm" data-action="add-notification">${icon('plus')} Add</button>
          </div>
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px">
            ${customNotifs.map(customNotifCard).join('') || '<div style="grid-column:1/-1;text-align:center;color:var(--sm-text-tertiary);font-size:12px;padding:12px">Ingen brugerdefinerede notifikationer. Klik Tilføj for at oprette en.</div>'}
          </div>`;
        })() + `
      ` : `
        <div class="section-header">
          <h3 class="section-title">Automatiseringer</h3>
          <button class="sm-btn primary sm" data-action="add-automation">
            ${icon("plus")} Tilføj automatisering
          </button>
        </div>
        ${Object.entries(automations).map(([id, a]) => `
          <div class="sm-card" style="padding:16px;opacity:${a.enabled ? 1 : 0.5}">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-size:14px;font-weight:600">${a.name || "Automatisering"}</div>
                <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:4px">
                  Udløser: <span class="badge entry">${a.trigger || "?"}</span>
                </div>
              </div>
              <button class="sm-toggle ${a.enabled ? "on" : ""}"
                      data-auto-toggle="${id}">
                <div class="dot"></div>
              </button>
            </div>
            <div class="notif-actions">
              <button class="sm-btn default sm" data-test-auto="${id}">
                ${icon("play")} Test
              </button>
              <button class="sm-btn ghost sm" data-delete-auto="${id}">
                ${icon("trash")}
              </button>
            </div>
          </div>
        `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">Ingen automatiseringer oprettet endnu.</div>'}

        <div class="info-card info">
          
          <div style="flex:1">
            <div class="info-title" style="color:var(--sm-blue)">Blueprints</div>
            <div class="info-text">Brug færdige blueprints til alarmlys, sirenstyring og mere</div>
          </div>
          <button class="sm-btn default sm">Gennemse</button>
        </div>
      `}
    `;
    this._automationsRenderKey   = aCacheKey;
    this._automationsRenderCache = __ahtml;
    return __ahtml;
  }

  // ===
  // ===
  // TAB: SPECIAL FEATURES
  // ===
  _renderSpecialFeatures() {
    if (this._data.autoActions === null) {
      return `<div style="padding:40px;text-align:center;color:var(--sm-text-secondary);font-size:13px">Indlæser...</div>`;
    }

    const aa = this._data.autoActions || {};
    const fp = this._data.fakePresenceV2 || {};

    const fpActive       = fp.active        || false;
    const fpBlockAlarm   = fp.block_alarm   !== undefined ? fp.block_alarm   : true;
    const fpBlockLocks   = fp.block_locks   !== undefined ? fp.block_locks   : false;
    const fpBlockCameras = fp.block_cameras !== undefined ? fp.block_cameras : false;

    const aaLockEnabled   = aa.auto_lock_enabled   !== undefined ? aa.auto_lock_enabled   : true;
    const aaLockDelay     = aa.auto_lock_delay      !== undefined ? aa.auto_lock_delay      : 120;
    const aaAlarmEnabled  = aa.auto_alarm_enabled  !== undefined ? aa.auto_alarm_enabled  : true;
    const aaAlarmDelay    = aa.auto_alarm_delay     !== undefined ? aa.auto_alarm_delay     : 300;
    const aaCamEnabled    = aa.auto_camera_enabled !== undefined ? aa.auto_camera_enabled : true;
    const aaCamDelay      = aa.auto_camera_delay   !== undefined ? aa.auto_camera_delay   : 0;
    const aaArrivalDelay  = aa.arrival_confirmation_delay !== undefined ? aa.arrival_confirmation_delay : 60;
    const aaNotifyAll     = aa.notify_all_users || false;

    const delayLabel = (s) => s >= 60 ? `${Math.round(s/60)} min` : `${s}s`;

    return `
      <div class="section-header">
        <h2>Specialfunktioner</h2>
        <p>Tilstedeværelsesbaseret automatisering og Fake Presence-konfiguration.</p>
      </div>

      <!-- AUTO ACTIONS -->
      <div class="sm-card" style="padding:20px;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
          <div style="width:38px;height:38px;border-radius:10px;background:var(--sm-accent-dim);
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            ${icon("shield")}
          </div>
          <div style="flex:1">
            <div style="font-size:15px;font-weight:600">Auto-handlinger</div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              Automatic actions when all persons leave home
            </div>
          </div>
        </div>

        <!-- LOCKS -->
        <div style="padding:14px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:${aaLockEnabled ? '12px' : '0'}">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("lock")}
              <span style="font-size:13px;font-weight:600">Lås døre</span>
            </div>
            <button class="sm-toggle ${aaLockEnabled ? 'on' : ''}" data-aa-toggle="auto_lock_enabled">
              <div class="dot"></div>
            </button>
          </div>
          ${aaLockEnabled ? `
            <div style="display:flex;align-items:center;gap:8px">
              <label style="font-size:12px;color:var(--sm-text-secondary);white-space:nowrap">Delay: ${delayLabel(aaLockDelay)}</label>
              <input type="range" min="0" max="900" step="30" value="${aaLockDelay}"
                     data-aa-range="auto_lock_delay"
                     style="flex:1;accent-color:var(--sm-accent)">
            </div>
          ` : ''}
        </div>

        <!-- ALARM -->
        <div style="padding:14px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:${aaAlarmEnabled ? '12px' : '0'}">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("shield")}
              <span style="font-size:13px;font-weight:600">Arm alarm (away)</span>
            </div>
            <button class="sm-toggle ${aaAlarmEnabled ? 'on' : ''}" data-aa-toggle="auto_alarm_enabled">
              <div class="dot"></div>
            </button>
          </div>
          ${aaAlarmEnabled ? `
            <div style="display:flex;align-items:center;gap:8px">
              <label style="font-size:12px;color:var(--sm-text-secondary);white-space:nowrap">Delay: ${delayLabel(aaAlarmDelay)}</label>
              <input type="range" min="0" max="1800" step="30" value="${aaAlarmDelay}"
                     data-aa-range="auto_alarm_delay"
                     style="flex:1;accent-color:var(--sm-accent)">
            </div>
          ` : ''}
        </div>

        <!-- CAMERAS -->
        <div style="padding:14px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:${aaCamEnabled ? '12px' : '0'}">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("camera")}
              <span style="font-size:13px;font-weight:600">Aktivér kameraer</span>
            </div>
            <button class="sm-toggle ${aaCamEnabled ? 'on' : ''}" data-aa-toggle="auto_camera_enabled">
              <div class="dot"></div>
            </button>
          </div>
          ${aaCamEnabled ? `
            <div style="display:flex;align-items:center;gap:8px">
              <label style="font-size:12px;color:var(--sm-text-secondary);white-space:nowrap">Delay: ${delayLabel(aaCamDelay)}</label>
              <input type="range" min="0" max="300" step="10" value="${aaCamDelay}"
                     data-aa-range="auto_camera_delay"
                     style="flex:1;accent-color:var(--sm-accent)">
            </div>
          ` : ''}
        </div>

        <!-- ARRIVAL CONFIRMATION -->
        <div style="padding:14px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
            ${icon("user")}
            <span style="font-size:13px;font-weight:600">Bekræftelse ved ankomst</span>
            <span style="font-size:11px;color:var(--sm-text-tertiary);margin-left:auto">${delayLabel(aaArrivalDelay)}</span>
          </div>
          <div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:8px">
            Wait this long after a person arrives before cancelling pending actions. Prevents GPS flicker from resetting timers.
          </div>
          <input type="range" min="0" max="300" step="15" value="${aaArrivalDelay}"
                 data-aa-range="arrival_confirmation_delay"
                 style="width:100%;accent-color:var(--sm-accent)">
        </div>

        <!-- NOTIFICATION TARGET -->
        <div style="padding:14px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:16px">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div>
              <div style="font-size:13px;font-weight:600">Giv besked til alle brugere</div>
              <div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:2px">
                ON = all users &nbsp;&bull;&nbsp; OFF = admins only
              </div>
            </div>
            <button class="sm-toggle ${aaNotifyAll ? 'on' : ''}" data-aa-toggle="notify_all_users">
              <div class="dot"></div>
            </button>
          </div>
        </div>

        <button class="sm-btn primary" data-action="save-auto-actions">Gem auto-handlinger</button>
      </div>

      <!-- FAKE PRESENCE v2 -->
      <div class="sm-card" style="padding:20px;margin-bottom:16px;border-color:${fpActive ? 'var(--sm-warning)' : 'var(--sm-border)'}">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:${fpActive ? '16px' : '0'}">
          <div style="width:38px;height:38px;border-radius:10px;
                      background:${fpActive ? 'var(--sm-warning-dim)' : 'rgba(255,255,255,0.06)'};
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                 stroke="${fpActive ? 'var(--sm-warning)' : 'var(--sm-text-tertiary)'}"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div style="flex:1">
            <div style="font-size:15px;font-weight:600;color:${fpActive ? 'var(--sm-warning)' : 'var(--sm-text)'}">
              Fake Presence
            </div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              ${fpActive ? 'Active &mdash; selected auto actions are blocked' : 'Simulates presence to block selected automatic actions'}
            </div>
          </div>
          <button class="sm-toggle ${fpActive ? 'on' : ''}" data-fp-toggle="active">
            <div class="dot"></div>
          </button>
        </div>

        ${fpActive ? `
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:12px">
            Choose which automatic actions Fake Presence blocks:
          </div>

          <!-- BLOCK ALARM -->
          <div style="display:flex;align-items:center;justify-content:space-between;
                      padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("shield")}
              <div>
                <div style="font-size:13px;font-weight:500">Blokér tilkobling af alarm</div>
                <div style="font-size:11px;color:var(--sm-text-tertiary)">Alarmen tilkobles ikke automatisk</div>
              </div>
            </div>
            <button class="sm-toggle ${fpBlockAlarm ? 'on' : ''}" data-fp-toggle="block_alarm">
              <div class="dot"></div>
            </button>
          </div>

          <!-- BLOCK LOCKS -->
          <div style="display:flex;align-items:center;justify-content:space-between;
                      padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("lock")}
              <div>
                <div style="font-size:13px;font-weight:500">Blokér auto-lås</div>
                <div style="font-size:11px;color:var(--sm-text-tertiary)">Døre låses ikke automatisk</div>
              </div>
            </div>
            <button class="sm-toggle ${fpBlockLocks ? 'on' : ''}" data-fp-toggle="block_locks">
              <div class="dot"></div>
            </button>
          </div>

          <!-- BLOCK CAMERAS -->
          <div style="display:flex;align-items:center;justify-content:space-between;
                      padding:12px;background:rgba(0,0,0,0.2);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:8px">
              ${icon("camera")}
              <div>
                <div style="font-size:13px;font-weight:500">Blokér kameraaktivering</div>
                <div style="font-size:11px;color:var(--sm-text-tertiary)">Kameraer aktiveres ikke automatisk</div>
              </div>
            </div>
            <button class="sm-toggle ${fpBlockCameras ? 'on' : ''}" data-fp-toggle="block_cameras">
              <div class="dot"></div>
            </button>
          </div>

          <div style="padding:10px 12px;border-radius:8px;background:var(--sm-warning-dim);
                      border:1px solid rgba(255,159,10,0.2);font-size:12px;color:var(--sm-warning);margin-bottom:16px">
            Fake Presence is ON. Remember to turn it off when you leave for real.
          </div>

          <button class="sm-btn primary" data-action="save-fake-presence-v2">Gem Fake Presence</button>
        ` : ''}
      </div>
    `;
  }

  // ===
  // PLACEHOLDER TAB
  // ===
  _renderFuture() {
    return `
      <div class="section-header">
        <h3 class="section-title">Future & Advanced</h3>
        <span class="badge" style="background:var(--sm-purple-dim);color:var(--sm-purple)">Roadmap</span>
      </div>

      <!-- Home Alone Mode roadmap card -->
      <div class="sm-card" style="padding:16px;margin-bottom:16px;border-color:var(--sm-purple);opacity:0.85">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
          <div style="width:38px;height:38px;border-radius:10px;background:var(--sm-purple-dim);
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--sm-purple)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;color:var(--sm-purple)">Alene-tilstand</div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              Dedicated arm mode for when children are home alone
            </div>
          </div>
          <span class="badge" style="background:var(--sm-purple-dim);color:var(--sm-purple)">v1.4.3</span>
        </div>
        <div style="font-size:12px;color:var(--sm-text-secondary);line-height:1.6;padding:10px 12px;
                    background:rgba(0,0,0,0.2);border-radius:8px">
          A full alarm mode alongside Away, Home, Night and Vacation.
          Cameras activate on arm. Door sensors send push notifications with a camera snapshot
          and action buttons (e.g. &ldquo;Where are you going?&rdquo;).
          Motion sensors show live movement across rooms &mdash; visual only, no alarm trigger.
          TTS speaker per door configurable for closest-room voice feedback.
        </div>
      </div>

      <!-- Fake Presence roadmap note -->
      <div class="sm-card" style="padding:16px;margin-bottom:16px;opacity:0.7">
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,0.06);
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--sm-text-tertiary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600">Fake Presence</div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              Toggle available under the Sensors tab
            </div>
          </div>
        </div>
      </div>

      <div class="sm-card" style="padding:20px;text-align:center;opacity:0.6">
        <div style="font-size:13px;color:var(--sm-text-secondary);margin-bottom:8px">Kommer snart</div>
        <div style="font-size:12px;color:var(--sm-text-tertiary)">
          Pet immunity &bull; AI person detection &bull; House map with live motion &bull; Cloud sync &bull; Voice control
        </div>
      </div>
    `;
  }

  _renderPlaceholder(iconName, title, desc, colorName, badgeText) {
    return `
      <div class="placeholder">
        <div class="placeholder-icon" style="background:var(--sm-${colorName}-dim);color:var(--sm-${colorName})">${icon(iconName)}</div>
        <h3>${title}</h3>
        <p>${desc}</p>
        <span class="badge ${colorName === "warning" ? "entry" : "actions"}">${badgeText}</span>
      </div>
    `;
    this._automationsRenderKey = aCacheKey; this._automationsRenderCache = __ahtml; return __ahtml;
  }

  // ===
  // TAB: TESTING
  // ===
  _renderArmHistory(events) {
    if (!events || events.length === 0) return "";
    const STATE_LABELS = {
      disarmed: "Deaktiveret", armed_away: "Tilkoblet Borte", armed_home: "Tilkoblet Hjemme",
      armed_night: "Tilkoblet Nat", armed_vacation: "Tilkoblet Ferie",
      armed_home_alone: "Alene", triggered: "Udløst",
      arming: "Tilkobler", pending: "Afventer",
    };
    return `
      <div class="section-header" style="margin-top:16px">
        <h3 class="section-title">Seneste hændelser</h3>
      </div>
      <div class="sm-card" style="padding:0;overflow:hidden">
        ${events.map((ev, i) => {
          const ts = new Date((ev.ts || 0) * 1000);
          const timeStr = ts.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})
            + " " + ts.toLocaleDateString([], {day:"2-digit",month:"2-digit"});
          const stateLabel = STATE_LABELS[ev.state] || ev.state;
          const stateColor = ev.state === "triggered" ? "var(--sm-danger)"
            : ev.state === "disarmed" ? "var(--sm-text-secondary)"
            : "var(--sm-accent)";
          return `<div style="display:flex;align-items:center;justify-content:space-between;
                      padding:10px 16px;${i > 0 ? "border-top:1px solid var(--sm-border)" : ""}">
            <div style="display:flex;align-items:center;gap:10px">
              <span style="width:8px;height:8px;border-radius:50%;flex-shrink:0;
                           background:${stateColor}"></span>
              <span style="font-size:13px;font-weight:600;color:${stateColor}">${stateLabel}</span>
              ${ev.by ? `<span style="font-size:11px;color:var(--sm-text-tertiary)">by ${ev.by}</span>` : ""}
            </div>
            <span style="font-size:11px;color:var(--sm-text-tertiary)">${timeStr}</span>
          </div>`;
        }).join("")}
      </div>
    `;
  }

  _renderTesting() {
    const health  = this._data.health || {};
    const results = this._data.testResults || [];
    const lastResult = results[0] || null;
    const score   = health.health_score ?? 100;
    const modules = health.modules || {};
    const batteries = health.batteries || [];
    const isRunning = this._testRunning || false;

    const scoreColor = score >= 90 ? "var(--sm-accent)" :
                       score >= 70 ? "var(--sm-warning)" : "var(--sm-danger)";

    // Weighted: modules with problems dominate the label over raw score
    const problemModules = Object.entries(modules)
      .filter(([,m]) => m.enabled && m.status !== "ok")
      .map(([id]) => id);
    const weightedLabel = problemModules.length > 0
      ? `${problemModules.length} modul${problemModules.length > 1 ? "er" : ""} med problemer`
      : score >= 90 ? "Alle systemer sunde"
      : score >= 70 ? "Mindre problemer fundet" : "Kritiske problemer fundet";

    // Test level definitions shown as descriptions on hover/below button
    const TEST_LEVELS = [
      {
        key: "quick",
        label: "Hurtig test",
        desc: "Kun entitets-tilgængelighed. Ingen enheder aktiveres. Sikker at køre når som helst.",
        checks: ["Entitets-tilgængelighed for alle moduler", "Markerer ikke-konfigurerede (aktiverede men tomme) moduler"],
        notChecked: ["Enhedsrespons", "Batteriniveauer", "Sensorsignal"],
        color: "var(--sm-accent)",
        btnClass: "sm-btn primary",
      },
      {
        key: "standard",
        label: "Standard test",
        desc: "Fuld modulverifikation. Enheder aktiveres kortvarigt (låsecyklus, TTS, sirenebip).",
        checks: ["Alt i Hurtig", "Lås: lås op/lås-cyklus", "Sirene: 2s testlyd", "TTS: testbesked", "Lys: kort blink", "Batteriniveauer (informativt)"],
        notChecked: ["Sensorsignalkvalitet"],
        color: "var(--sm-blue)",
        btnClass: "sm-btn default",
      },
      {
        key: "full",
        label: "Fuld test",
        desc: "Komplet systemtjek inklusive al sensorsignalkvalitet.",
        checks: ["Alt i Standard", "Online-tjek af alle konfigurerede sensorer", "Zoneintegritet"],
        notChecked: [],
        color: "var(--sm-purple)",
        btnClass: "sm-btn",
      },
    ];

    return `
      <!-- ── System Health ─────────────────────────────────────────── -->
      <div class="section-header">
        <h3 class="section-title">Systemhelbred</h3>
        <span class="badge accent">${score}%</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        <div style="padding:16px 20px">
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px">
            <div style="width:56px;height:56px;border-radius:50%;flex-shrink:0;
                 border:4px solid ${scoreColor};
                 display:flex;align-items:center;justify-content:center;
                 font-size:20px;font-weight:700;color:${scoreColor}">
              ${score}
            </div>
            <div>
              <div style="font-size:15px;font-weight:600">
                ${weightedLabel}
              </div>
              <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
                ${health.available_entities || 0}/${health.total_entities || 0} entities available
                &middot; ${health.low_battery_count || 0} low batteries
              </div>
              ${health.armed_by ? `<div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:3px">Armed by: ${health.armed_by}</div>` : ""}
              ${health.triggered_by ? `<div style="font-size:11px;color:var(--sm-danger);margin-top:3px">Last triggered by: ${this._hass?.states?.[health.triggered_by]?.attributes?.friendly_name || health.triggered_by}</div>` : ""}
              ${(health.open_sensors || []).length > 0 ? `<div style="font-size:11px;color:var(--sm-warning);margin-top:3px">Open: ${(health.open_sensors||[]).map(e=>this._hass?.states?.[e]?.attributes?.friendly_name||e.split(".").pop().replace(/_/g," ")).join(", ")}</div>` : ""}
            </div>
          </div>

          <!-- Module Status Grid -->
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:6px">
            ${Object.entries(modules).map(([id, m]) => {
              const color = !m.enabled ? "var(--sm-text-tertiary)" :
                            m.status === "ok" ? "var(--sm-accent)" : "var(--sm-danger)";
              const statusIcon = !m.enabled ? icon("circle") :
                                 m.status === "ok" ? icon("check") : icon("fail");
              return `
                <div style="padding:8px 10px;background:rgba(255,255,255,0.04);
                     border-radius:8px;border:1px solid ${color}22;
                     display:flex;align-items:center;gap:8px">
                  <span style="color:${color};font-size:13px">${statusIcon}</span>
                  <div>
                    <div style="font-size:12px;font-weight:600;text-transform:capitalize">${id}</div>
                    <div style="font-size:10px;color:var(--sm-text-secondary)">
                      ${!m.enabled ? "deaktiveret" : m.total === 0 ? "ikke konfigureret" : m.available + "/" + m.total + " ok"}
                    </div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      </div>

      <!-- ── Arm History ─────────────────────────────────────────── -->
      ${this._renderArmHistory(health.arm_history || [])}

      <!-- ── Run Tests ─────────────────────────────────────────────── -->
      <div class="section-header" style="margin-top:20px">
        <h3 class="section-title">Kør tests</h3>
        ${isRunning ? '<span class="badge entry">Kører...</span>' : ""}
      </div>

      <div class="sm-card" style="padding:14px">
        <!-- Three test level buttons -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px">
          ${TEST_LEVELS.map(t => `
            <button class="${t.btnClass}" data-run-test="${t.key}"
                    ${isRunning ? "disabled" : ""}
                    style="padding:12px 8px;flex-direction:column;gap:4px;
                    display:flex;align-items:center;justify-content:center;
                    ${t.key === "full" ? "background:var(--sm-purple-dim);color:var(--sm-purple);border:1px solid var(--sm-purple)44" : ""}">
              <span style="font-size:13px;font-weight:600">${t.label}</span>
              <span style="font-size:10px;opacity:0.7;text-align:center;line-height:1.3">${t.desc}</span>
            </button>
          `).join("")}
        </div>

        <!-- Test descriptions accordion -->
        <div style="border-top:1px solid var(--sm-border);padding-top:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none"
               data-action="toggle-test-desc">
            <span style="font-size:12px;color:var(--sm-text-secondary)">What does each test check?</span>
            <span style="font-size:11px;color:var(--sm-text-tertiary)">${this._testDescExpanded ? "Skjul" : "Vis"}</span>
          </div>
          ${this._testDescExpanded ? `
            <div style="margin-top:10px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px">
              ${TEST_LEVELS.map(t => `
                <div style="padding:10px;background:rgba(255,255,255,0.03);border-radius:8px;
                     border-left:3px solid ${t.color}">
                  <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:${t.color}">${t.label}</div>
                  ${t.checks.map(c => `
                    <div style="font-size:11px;color:var(--sm-text-secondary);margin-bottom:3px;
                         display:flex;gap:4px;align-items:flex-start">
                      <span style="color:var(--sm-accent);flex-shrink:0">${icon("check")}</span>${c}
                    </div>
                  `).join("")}
                  ${t.notChecked.length > 0 ? t.notChecked.map(c => `
                    <div style="font-size:11px;color:var(--sm-text-tertiary);margin-bottom:3px;
                         display:flex;gap:4px;align-items:flex-start">
                      <span style="flex-shrink:0;opacity:0.4">${icon("circle")}</span>${c}
                    </div>
                  `).join("") : ""}
                </div>
              `).join("")}
            </div>
          ` : ""}
        </div>

      </div>

      <!-- ── Scheduled Tests ───────────────────────────────────────── -->
      ` + this._renderScheduledTests() + `

      <!-- Row 1: Last Test Run | Test History -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px">

        <!-- Last Test Run -->
        <div style="display:flex;flex-direction:column">
          <div class="section-header">
            <h3 class="section-title">Seneste testkørsel</h3>
            ${lastResult ? `<span class="badge ${
              lastResult.overall === "pass" ? "accent" :
              lastResult.overall === "warning" ? "entry" : "perimeter"
            }">${lastResult.overall.toUpperCase()}</span>` : ""}
          </div>
          <div style="flex:1">
            ${lastResult ? this._renderTestResult(lastResult) : `
              <div class="sm-card" style="text-align:center;padding:28px;color:var(--sm-text-tertiary)">
                No tests run yet.
              </div>
            `}
          </div>
        </div>

        <!-- Test History -->
        <div style="display:flex;flex-direction:column">
          <div class="section-header">
            <h3 class="section-title">Testhistorik</h3>
            ${results.length > 1 ? `<span class="badge actions">${results.length} results</span>` : ""}
          </div>
          ${results.length > 1 ? (() => {
            const renderRow = (r, i) => {
              const col = r.overall === "pass" ? "var(--sm-accent)" :
                          r.overall === "warning" ? "var(--sm-warning)" : "var(--sm-danger)";
              const ic  = r.overall === "pass" ? icon("ok") :
                          r.overall === "warning" ? icon("warn") : icon("fail");
              const passed = r.summary ? r.summary.passed || 0 : 0;
              const total  = r.summary ? (r.summary.passed||0)+(r.summary.failed||0)+(r.summary.warned||0) : 0;
              return `
                <div style="padding:10px 16px;display:flex;align-items:center;gap:10px;
                     ${i > 0 ? "border-top:1px solid var(--sm-border)" : ""}">
                  <span style="color:${col};font-size:14px">${ic}</span>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:600">${{quick:"Hurtig",standard:"Standard",full:"Fuld",lights:"Lys",sensor:"Sensor",module:"Modul"}[r.test_type] || r.test_type} test</div>
                    <div style="font-size:11px;color:var(--sm-text-secondary)">${r.timestamp}</div>
                  </div>
                  <div style="text-align:right;flex-shrink:0">
                    <div style="font-size:12px;font-weight:600;color:${col}">${r.overall.toUpperCase()}</div>
                    <div style="font-size:11px;color:var(--sm-text-secondary)">
                      ${passed}/${total} bestået &middot; ${r.duration_seconds}s
                      ${r.summary?.failed ? ` &middot; <span style="color:var(--sm-danger)">${r.summary.failed} fejlede</span>` : ""}
                    </div>
                  </div>
                </div>`;
            };
            const recent = results.slice(0, 3);
            const older  = results.slice(3, 50);
            return `
              <div class="sm-card" style="padding:0;overflow:hidden;flex:1">
                ${recent.map((r, i) => renderRow(r, i)).join("")}
                ${older.length > 0 ? `
                  <div class="collapsible-header ${this._testHistoryExpanded ? 'expanded' : ''}"
                       data-action="toggle-test-history"
                       style="padding:8px 16px;margin:0;border-top:1px solid var(--sm-border);background:rgba(255,255,255,0.02);">
                    <span style="font-size:12px;color:var(--sm-text-secondary)">
                      ${this._testHistoryExpanded ? 'Hide older results' : `Show ${older.length} older result${older.length > 1 ? 's' : ''}`}
                    </span>
                    <span class="chevron">${icon("chevron")}</span>
                  </div>
                  <div class="collapsible-body ${this._testHistoryExpanded ? 'expanded' : ''}">
                    ${older.map((r, i) => renderRow(r, i + recent.length)).join("")}
                  </div>
                ` : ''}
              </div>`;
          })() : `
            <div class="sm-card" style="text-align:center;padding:28px;color:var(--sm-text-tertiary);font-size:13px">Ingen historik endnu.</div>
          `}
        </div>

      </div>

      <!-- Row 2: Sensor Status | Battery Overview -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;align-items:start">
        <div style="display:flex;flex-direction:column">${this._renderSensorStatus()}</div>
        <div style="display:flex;flex-direction:column">${this._renderBatteryOverview(batteries)}</div>
      </div>
    `;
  }

  _renderScheduledTests() {
    const scheduled = this._data.scheduledTests || {};
    const entries = Object.entries(scheduled);
    const WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
    const TEST_LABELS = { quick: 'Quick', standard: 'Standard', full: 'Full' };

    const schedCard = ([id, s]) => {
      const sched = s.schedule || {};
      const mode = sched.mode || 'weekly';
      const timeStr = String(sched.hour ?? 8).padStart(2,'0') + ':' + String(sched.minute ?? 0).padStart(2,'0');
      const testLabel = TEST_LABELS[s.test_type] || s.test_type;
      const resultColor = !s.last_result ? 'var(--sm-text-tertiary)' :
        s.last_result === 'pass' ? 'var(--sm-accent)' :
        s.last_result === 'warning' ? 'var(--sm-warning)' : 'var(--sm-danger)';
      let schedDesc = '';
      if (mode === 'daily') schedDesc = 'Every day';
      else if (mode === 'weekly') schedDesc = 'Every ' + (WEEKDAYS[sched.weekday ?? 6] || 'Sunday');
      else if (mode === 'interval') schedDesc = 'Every ' + (sched.interval_weeks || 2) + ' weeks (Sunday)';

      return `
        <div class="sm-card" style="padding:10px 14px;display:flex;align-items:center;gap:10px;opacity:${s.enabled !== false ? 1 : 0.5}">
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
              <span style="font-size:13px;font-weight:600">${s.name || 'Scheduled Test'}</span>
              <span class="badge" style="background:var(--sm-blue-dim);color:var(--sm-blue);font-size:10px">${testLabel}</span>
              ${s.notify_on_fail !== false ? '<span class="badge" style="background:var(--sm-warning-dim);color:var(--sm-warning);font-size:10px">Giv besked ved fejl</span>' : ''}
              ${s.enabled === false ? '<span class="badge" style="opacity:0.5;font-size:10px">Deaktiveret</span>' : ''}
            </div>
            <div style="font-size:11px;color:var(--sm-text-secondary);margin-top:3px">
              ${schedDesc} at ${timeStr}
              ${s.last_run ? ` &middot; Last: <span style="color:${resultColor};font-weight:600">${(s.last_result || '?').toUpperCase()}</span> (${s.last_run.slice(0,16)})` : ''}
            </div>
          </div>
          <div style="display:flex;gap:4px;flex-shrink:0">
            <button class="sm-btn default sm" data-run-sched="${id}" title="Kør nu" style="padding:4px 8px">${icon('play')}</button>
            <button class="sm-btn ghost sm" data-edit-sched="${id}" title="Edit" style="padding:4px 8px">${icon('edit')}</button>
            <button class="sm-btn ghost sm" data-delete-sched="${id}" title="Slet" style="padding:4px 8px">${icon('trash')}</button>
          </div>
        </div>`;
    };

    return `
      <div class="section-header" style="margin-top:20px">
        <h3 class="section-title">Planlagte tests</h3>
        <button class="sm-btn primary sm" data-action="add-sched-test">${icon('plus')} Add</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px">
        ${entries.length > 0
          ? entries.map(schedCard).join('')
          : '<div class="sm-card" style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:13px">Ingen planlagte tests. Klik Tilføj for at oprette en.</div>'
        }
      </div>
    `;
  }

  _renderSchedDialog() {
    const t = this._schedTemp || {};
    const sched = t.schedule || {};
    const isEdit = !!t._id;
    const WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog" style="max-width:460px">
          <div class="dialog-header">
            ${icon('clock')}
            <div class="dialog-title">${isEdit ? 'Rediger planlagt test' : 'Tilføj planlagt test'}</div>
            <button class="dialog-close" data-action="close-sched-dialog">${icon('close')}</button>
          </div>

          <div class="form-group">
            <label class="form-label">Navn</label>
            <input type="text" class="form-input" id="sched-name"
              placeholder="f.eks. Ugentligt søndagstjek" value="${t.name || ''}">
          </div>

          <div class="form-group">
            <label class="form-label">Testtype</label>
            <select class="form-select" id="sched-test-type">
              <option value="quick"    ${(t.test_type || 'quick') === 'quick'    ? 'selected' : ''}>Hurtig - kun entitets-tilgængelighed</option>
              <option value="standard" ${t.test_type === 'standard' ? 'selected' : ''}>Standard - fuld modulverifikation</option>
              <option value="full"     ${t.test_type === 'full'     ? 'selected' : ''}>Fuld - inkl. sensorsignal</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Tidsplan</label>
            <select class="form-select" id="sched-mode" onchange="this.getRootNode().host._onSchedModeChange(this.value)">
              <option value="weekly"   ${(sched.mode || 'weekly') === 'weekly'   ? 'selected' : ''}>Ugentlig - bestemt ugedag</option>
              <option value="interval" ${sched.mode === 'interval' ? 'selected' : ''}>Hver N. uge - altid søndag</option>
              <option value="daily"    ${sched.mode === 'daily'    ? 'selected' : ''}>Dagligt</option>
            </select>
          </div>

          <div id="sched-weekly-opts" style="${(sched.mode || 'weekly') === 'weekly' ? '' : 'display:none'}">
            <div class="form-group">
              <label class="form-label">Hverdag</label>
              <select class="form-select" id="sched-weekday">
                ${WEEKDAYS.map((d, i) => '<option value="' + i + '"' + ((sched.weekday ?? 6) === i ? ' selected' : '') + '>' + d + '</option>').join('')}
              </select>
            </div>
          </div>

          <div id="sched-interval-opts" style="${sched.mode === 'interval' ? '' : 'display:none'}">
            <div class="form-group">
              <label class="form-label">Interval</label>
              <select class="form-select" id="sched-interval-weeks">
                <option value="2" ${(sched.interval_weeks || 2) === 2 ? 'selected' : ''}>Every 2 weeks</option>
                <option value="3" ${sched.interval_weeks === 3 ? 'selected' : ''}>Every 3 weeks</option>
                <option value="4" ${sched.interval_weeks === 4 ? 'selected' : ''}>Every 4 weeks (monthly)</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Tidspunkt på dagen</label>
            <div style="display:flex;align-items:center;gap:8px">
              <input type="number" class="form-input" id="sched-hour"
                min="0" max="23" value="${sched.hour ?? 8}" style="width:70px;text-align:center">
              <span style="color:var(--sm-text-secondary)">:</span>
              <input type="number" class="form-input" id="sched-minute"
                min="0" max="59" step="5" value="${sched.minute ?? 0}" style="width:70px;text-align:center">
              <span style="font-size:11px;color:var(--sm-text-tertiary)">hour : minute (24h)</span>
            </div>
          </div>

          <div class="form-group">
            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.04);font-size:14px">
              <input type="checkbox" id="sched-notify-fail" ${t.notify_on_fail !== false ? 'checked' : ''}>
              <span style="flex:1">Giv besked til admins ved fejl</span>
              <span style="font-size:11px;color:var(--sm-text-tertiary)">Push til admin-brugere</span>
            </label>
          </div>

          <div class="form-group">
            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.04);font-size:14px">
              <input type="checkbox" id="sched-enabled" ${t.enabled !== false ? 'checked' : ''}>
              <span style="flex:1">Aktiveret</span>
            </label>
          </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="close-sched-dialog">Annuller</button>
            <button class="btn-dialog save" data-action="save-sched-test">
              ${isEdit ? 'Save Changes' : 'Add Schedule'}
            </button>
          </div>
        </div>
      </div>`;
  }

  _onSchedModeChange(mode) {
    const root = this.shadowRoot;
    const weekly   = root.querySelector('#sched-weekly-opts');
    const interval = root.querySelector('#sched-interval-opts');
    if (weekly)   weekly.style.display   = mode === 'weekly'   ? '' : 'none';
    if (interval) interval.style.display = mode === 'interval' ? '' : 'none';
  }

  async _saveSchedTest() {
    const root = this.shadowRoot;
    const name        = root.querySelector('#sched-name')?.value?.trim();
    const testType    = root.querySelector('#sched-test-type')?.value || 'quick';
    const mode        = root.querySelector('#sched-mode')?.value || 'weekly';
    const weekday     = parseInt(root.querySelector('#sched-weekday')?.value ?? 6);
    const intervalWks = parseInt(root.querySelector('#sched-interval-weeks')?.value ?? 2);
    const hour        = parseInt(root.querySelector('#sched-hour')?.value ?? 8);
    const minute      = parseInt(root.querySelector('#sched-minute')?.value ?? 0);
    const notifyFail  = root.querySelector('#sched-notify-fail')?.checked !== false;
    const enabled     = root.querySelector('#sched-enabled')?.checked !== false;
    const isEdit      = !!this._schedTemp?._id;
    const testId      = this._schedTemp?._id || '';

    if (!name) { this._toast('Indtast et navn.', 'warning'); return; }

    const schedule = { mode, hour, minute };
    if (mode === 'weekly')   schedule.weekday        = weekday;
    if (mode === 'interval') schedule.interval_weeks = intervalWks;

    const config = {
      name, test_type: testType, schedule,
      notify_on_fail: notifyFail, enabled,
      last_run:    this._schedTemp?.last_run    || null,
      last_result: this._schedTemp?.last_result || null,
    };

    const result = await this._callWS('save_scheduled_test', { test_id: testId, config });
    this._schedSaving = false;
    if (result?.success) {
      this._showDialog = null;
      this._schedTemp  = null;
      await this._loadTestingData();
      this._render();
      this._toast(isEdit ? 'Tidsplan opdateret' : 'Tidsplan tilføjet', 'success');
    } else {
      if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = isEdit ? 'Save Changes' : 'Add Schedule'; }
      this._toast('Kunne ikke gemme tidsplan — tjek HA-logs', 'error');
    }
  }



  _renderTestResult(result) {
    const mods    = result.modules  || {};
    const bats    = result.batteries || {};
    const sensors = result.sensors  || {};
    const summary = result.summary  || {};

    const overallColor = result.overall === "pass"    ? "var(--sm-accent)" :
                         result.overall === "warning" ? "var(--sm-warning)" : "var(--sm-danger)";
    const overallBg    = result.overall === "pass"    ? "var(--sm-accent-dim)" :
                         result.overall === "warning" ? "var(--sm-warning-dim)" : "var(--sm-danger-dim)";
    const overallIcon  = result.overall === "pass"    ? icon("ok") :
                         result.overall === "warning" ? icon("warn") : icon("fail");

    return `
      <div class="sm-card" style="padding:0;overflow:hidden">

        <!-- Header bar -->
        <div style="padding:14px 18px;background:${overallBg};display:flex;align-items:center;gap:12px">
          <span style="font-size:22px;color:${overallColor}">${overallIcon}</span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;text-transform:capitalize">
              ${result.test_type} Test &mdash;
              <span style="color:${overallColor}">${result.overall.toUpperCase()}</span>
            </div>
            <div style="font-size:11px;opacity:0.75;margin-top:2px">
              ${result.timestamp} &middot; ${result.duration_seconds}s &middot;
              <span style="color:var(--sm-accent)">${summary.passed || 0} bestået</span>
              ${summary.failed  ? ` &middot; <span style="color:var(--sm-danger)">${summary.failed} fejlede</span>` : ""}
              ${summary.warned  ? ` &middot; <span style="color:var(--sm-warning)">${summary.warned} advarsler</span>` : ""}
              ${summary.skipped ? ` &middot; ${summary.skipped} sprunget over` : ""}
            </div>
          </div>
        </div>

        <!-- Module results -->
        <div style="padding:8px 14px">
          <div style="font-size:10px;font-weight:600;color:var(--sm-text-tertiary);
               text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px">Moduler</div>
          ${Object.entries(mods).map(([id, m]) => {
            const color = m.status === "pass"    ? "var(--sm-accent)" :
                          m.status === "skipped" ? "var(--sm-text-tertiary)" :
                          m.status === "warning" ? "var(--sm-warning)" :
                          m.status === "fail"    ? "var(--sm-danger)" : "var(--sm-danger)";
            const label = m.status === "pass"    ? "PASS" :
                          m.status === "skipped" ? "SKIP" :
                          m.status === "warning" ? "WARN" :
                          m.status === "fail"    ? "FAIL" : "ERR";

            // Build reason string — informative and actionable
            let reason = "";
            if (m.status === "warning" && m.reason === "no_entities") {
              reason = "Ikke konfigureret — tilføj entiteter i modulindstillinger";
            } else if (m.status === "skipped" && m.reason === "disabled") {
              reason = "Modul deaktiveret";
            } else if (m.status === "skipped" && m.reason === "not selected") {
              reason = "Ikke valgt i denne test";
            } else if (m.status === "fail" && m.unavailable && m.unavailable.length > 0) {
              reason = "Utilgængelig: " + m.unavailable.slice(0, 2).join(", ") +
                       (m.unavailable.length > 2 ? " +" + (m.unavailable.length-2) + " flere" : "");
            } else if (m.test_result?.message) {
              reason = m.test_result.message;
            } else if (m.message) {
              reason = m.message;
            }

            return `
              <div style="display:flex;align-items:flex-start;gap:10px;padding:7px 0;
                   border-bottom:1px solid var(--sm-border)22">
                <span style="color:${color};font-weight:700;font-size:10px;
                     min-width:36px;padding-top:2px">${label}</span>
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px">
                    <span style="font-size:13px;font-weight:500">${MODULE_DEFS[id]?.name || id}</span>
                    ${m.entities_total != null && m.entities_total > 0 ? `
                      <span style="font-size:11px;color:var(--sm-text-secondary)">
                        ${m.entities_available}/${m.entities_total} entities
                      </span>
                    ` : ""}
                  </div>
                  ${reason ? `
                    <div style="font-size:11px;color:${m.status === "fail" ? "var(--sm-danger)" : "var(--sm-text-secondary)"};
                         margin-top:2px;line-height:1.4">${reason}</div>
                  ` : ""}
                  ${m.test_result?.details && m.status === "fail" ? `
                    <div style="margin-top:4px;padding:6px 8px;background:rgba(255,255,255,0.03);
                         border-radius:6px;border-left:2px solid var(--sm-danger)">
                      ${Object.entries(m.test_result.details).slice(0,3).map(([k,v]) =>
                        typeof v === "string" || typeof v === "number" ? `
                          <div style="font-size:10px;color:var(--sm-text-tertiary);font-family:'DM Mono',monospace">
                            ${k}: ${v}
                          </div>` : ""
                      ).join("")}
                    </div>
                  ` : ""}
                </div>
              </div>
            `;
          }).join("")}

          <!-- Sensor summary (Full test) -->
          ${sensors.total > 0 ? `
            <div style="display:flex;align-items:center;gap:10px;padding:7px 0;
                 border-bottom:1px solid var(--sm-border)22">
              <span style="color:${sensors.offline > 0 ? "var(--sm-danger)" : "var(--sm-accent)"};
                   font-weight:700;font-size:10px;min-width:36px">
                ${sensors.offline > 0 ? "FAIL" : "PASS"}
              </span>
              <div style="flex:1">
                <span style="font-size:13px;font-weight:500">Sensorer</span>
                <span style="font-size:11px;color:var(--sm-text-secondary);margin-left:8px">
                  ${sensors.online}/${sensors.total} online
                </span>
                ${sensors.offline > 0 ? `
                  <div style="font-size:11px;color:var(--sm-danger);margin-top:2px">
                    ${sensors.offline} sensor${sensors.offline > 1 ? "s" : ""} offline — check device connection
                  </div>
                ` : ""}
              </div>
            </div>
          ` : ""}

          <!-- Battery summary -->
          ${bats.total > 0 ? `
            <div style="padding:8px 0;margin-top:2px">
              <div style="font-size:10px;font-weight:600;color:var(--sm-text-tertiary);
                   text-transform:uppercase;letter-spacing:0.06em;margin-bottom:5px">
                Batteries (informational)
              </div>
              <div style="display:flex;gap:14px;font-size:12px;align-items:center">
                <span>${bats.total} tracked</span>
                ${bats.low_count > 0 ? `
                  <span style="color:var(--sm-warning)">${bats.low_count} low</span>
                ` : ""}
                ${bats.critical_count > 0 ? `
                  <span style="color:var(--sm-danger)">${bats.critical_count} critical</span>
                ` : ""}
                ${bats.low_count === 0 && bats.critical_count === 0 ? `
                  <span style="color:var(--sm-accent)">Alt OK</span>
                ` : ""}
                <span style="font-size:10px;color:var(--sm-text-tertiary);margin-left:auto">
                  Does not affect PASS/FAIL
                </span>
              </div>
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }


  _renderSensorStatus() {
    if (!this._hass) return '';

    const configuredSensors = this._data.sensors || [];
    if (configuredSensors.length === 0) {
      return `
        <div class="section-header">
          <h3 class="section-title">Sensorstatus</h3>
        </div>
        <div class="sm-card" style="text-align:center;padding:24px;color:var(--sm-text-tertiary)">
          Ingen sensorer konfigureret.
        </div>
      `;
    }

    const enabledSensors = configuredSensors.filter(s => s.enabled);
    const sensorStatuses = enabledSensors.map(s => {
      const state = this._hass.states[s.entity_id];
      const isOnline = state && state.state !== 'unavailable' && state.state !== 'unknown';
      return {
        entity_id: s.entity_id,
        name: s.name || s.entity_id,
        sensor_type: s.sensor_type,
        online: isOnline,
      };
    });

    const online  = sensorStatuses.filter(s => s.online).length;
    const offline = sensorStatuses.filter(s => !s.online).length;
    const visible = sensorStatuses.slice(0, 7);
    const hidden  = sensorStatuses.slice(7);

    const renderSensorRow = (s, i, border) => `
      <div style="padding:10px 16px;display:flex;align-items:center;gap:12px;
           ${border ? 'border-top:1px solid var(--sm-border)' : ''}">
        <div class="sensor-status-dot ${s.online ? 'online' : 'offline'}"></div>
        <div style="flex:1;min-width:0">
          <div style="font-size:12px;font-weight:500;white-space:nowrap;
               overflow:hidden;text-overflow:ellipsis">${s.name}</div>
          <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:'DM Mono',monospace">${s.entity_id}</div>
        </div>
        <span class="badge ${s.sensor_type}">${s.sensor_type}</span>
        <span style="font-size:11px;font-weight:600;
              color:${s.online ? 'var(--sm-accent)' : 'var(--sm-danger)'};
              min-width:50px;text-align:right">
          ${s.online ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>`;

    return `
      <div class="section-header">
        <h3 class="section-title">Sensorstatus</h3>
        <span class="badge ${offline > 0 ? 'perimeter' : 'accent'}">${online}/${sensorStatuses.length} online</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        ${visible.map((s, i) => renderSensorRow(s, i, i > 0)).join("")}
        ${hidden.length > 0 ? `
          <div style="border-top:1px solid var(--sm-border)">
            <div class="collapsible-header ${this._sensorStatusExpanded ? 'expanded' : ''}"
                 data-action="toggle-sensor-status-hidden"
                 style="padding:12px 16px;margin:0">
              <span style="font-size:12px;color:var(--sm-text-secondary)">
                ${hidden.length} more sensor${hidden.length > 1 ? 's' : ''}
              </span>
              <span class="chevron">${icon("chevron")}</span>
            </div>
            <div class="collapsible-body ${this._sensorStatusExpanded ? 'expanded' : ''}">
              ${hidden.map((s, i) => renderSensorRow(s, i, true)).join("")}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  _renderBatteryOverview(batteries) {
    if (!batteries || batteries.length === 0) {
      return `
        <div class="section-header">
          <h3 class="section-title">Batterioversigt</h3>
        </div>
        <div class="sm-card" style="text-align:center;padding:32px;color:var(--sm-text-tertiary)">
          No battery sensors discovered.
        </div>
      `;
    }

    const sorted = [...batteries].sort((a, b) => {
      if (a.level == null) return 1;
      if (b.level == null) return -1;
      return a.level - b.level;
    });

    // Split into low (<= 50%) and ok (> 50%)
    const lowBatteries = sorted.filter(b => b.level == null || b.level <= 50);
    const okBatteries = sorted.filter(b => b.level != null && b.level > 50);

    const renderBatteryRow = (bat, i, showBorder) => {
      const level = bat.level;
      const color = level == null ? "var(--sm-text-tertiary)" :
                    level < 10 ? "var(--sm-danger)" :
                    level < 20 ? "var(--sm-warning)" : "var(--sm-accent)";
      const barWidth = level != null ? Math.max(level, 3) : 0;
      const statusLabel = level == null ? "N/A" :
                          level < 10 ? "CRITICAL" :
                          level < 20 ? "LOW" :
                          level <= 50 ? "FAIR" : "OK";
      return `
        <div style="padding:10px 16px;display:flex;align-items:center;gap:12px;
             ${showBorder ? "border-top:1px solid var(--sm-border)" : ""}">
          <div style="min-width:48px;text-align:right;font-size:14px;font-weight:600;color:${color}">
            ${level != null ? level + "%" : "&mdash;"}
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-size:12px;font-weight:500;white-space:nowrap;
                 overflow:hidden;text-overflow:ellipsis">${bat.name}</div>
            <div style="margin-top:4px;height:4px;background:rgba(255,255,255,0.08);
                 border-radius:2px;overflow:hidden">
              <div style="height:100%;width:${barWidth}%;background:${color};
                   border-radius:2px;transition:width 0.3s"></div>
            </div>
          </div>
          <span style="font-size:10px;font-weight:600;color:${color};min-width:52px;
               text-align:right">${statusLabel}</span>
        </div>
      `;
    };

    const visibleBat = sorted.slice(0, 8);
    const hiddenBat  = sorted.slice(8);

    return `
      <div class="section-header">
        <h3 class="section-title">Batterioversigt</h3>
        <span class="badge accent">${batteries.length} tracked</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        ${visibleBat.map((bat, i) => renderBatteryRow(bat, i, i > 0)).join("")}
        ${hiddenBat.length > 0 ? `
          <div style="border-top:1px solid var(--sm-border)">
            <div class="collapsible-header ${this._batteryOkExpanded ? 'expanded' : ''}"
                 data-action="toggle-battery-ok"
                 style="padding:12px 16px;margin:0">
              <span style="font-size:12px;color:var(--sm-text-secondary)">
                ${hiddenBat.length} more batteries
              </span>
              <span class="chevron">${icon("chevron")}</span>
            </div>
            <div class="collapsible-body ${this._batteryOkExpanded ? 'expanded' : ''}">
              ${hiddenBat.map((bat, i) => renderBatteryRow(bat, i, true)).join("")}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  _renderBatteryTable(batteries) {
    if (!batteries || batteries.length === 0) {
      return `
        <div class="sm-card" style="text-align:center;padding:32px;color:var(--sm-text-tertiary)">
          No battery sensors discovered. Battery sensors with device_class "battery" will appear here.
        </div>
      `;
    }

    const sorted = [...batteries].sort((a, b) => {
      if (a.level == null) return 1;
      if (b.level == null) return -1;
      return a.level - b.level;
    });

    return `
      <div class="sm-card" style="padding:0;overflow:hidden">
        ${sorted.map((bat, i) => {
          const level = bat.level;
          const color = level == null ? "var(--sm-text-tertiary)" :
                        level < 10 ? "var(--sm-danger)" :
                        level < 20 ? "var(--sm-warning)" : "var(--sm-accent)";
          const barWidth = level != null ? Math.max(level, 3) : 0;
          const statusLabel = level == null ? "N/A" :
                              level < 10 ? "CRITICAL" :
                              level < 20 ? "LOW" : "OK";
          return `
            <div style="padding:10px 16px;display:flex;align-items:center;gap:12px;
                 ${i > 0 ? "border-top:1px solid var(--sm-border)" : ""}">
              <div style="min-width:48px;text-align:right;font-size:14px;font-weight:600;color:${color}">
                ${level != null ? level + "%" : "&mdash;"}
              </div>
              <div style="flex:1;min-width:0">
                <div style="font-size:12px;font-weight:500;white-space:nowrap;
                     overflow:hidden;text-overflow:ellipsis">${bat.name}</div>
                <div style="margin-top:4px;height:4px;background:rgba(255,255,255,0.08);
                     border-radius:2px;overflow:hidden">
                  <div style="height:100%;width:${barWidth}%;background:${color};
                       border-radius:2px;transition:width 0.3s"></div>
                </div>
              </div>
              <span style="font-size:10px;font-weight:600;color:${color};min-width:52px;
                   text-align:right">${statusLabel}</span>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  async _runTest(testType) {
    if (this._testRunning) return;
    this._testRunning = true;
    this._render();

    try {
      const result = await this._callWS("run_test", { test_type: testType });
      if (result) {
        const [health, testResults] = await Promise.all([
          this._callWS("get_health_summary"),
          this._callWS("get_test_results"),
        ]);
        if (health) this._data.health = health;
        if (testResults) this._data.testResults = testResults.results || [];
      }
    } catch (err) {
      console.error("Test failed:", err);
    }

    this._testRunning = false;
    this._testDescExpanded = false;
    this._schedTemp   = null;    // temp config for scheduled test editing
    this._schedSaving  = false;   // prevents double-submit
    this._render();
  }

  async _quickTestSiren() {
    if (this._sirenTestRunning || this._testRunning) return;
    this._sirenTestRunning = true;

    // Update button in-place without re-render (which would close the dialog)
    const btn = this.shadowRoot.querySelector("[data-action='quick-test-siren']");
    if (btn) { btn.disabled = true; btn.textContent = 'Testing...'; }

    try {
      const result = await this._callWS('quick_test_siren');
      if (result?.success) {
        const tested = result.details?.entities_tested?.map(e => e.entity_id).join(', ') || 'done';
        this._toast('Sirenetest OK: ' + tested, 'success');
      } else {
        this._toast('Sirenetest fejlede: ' + (result?.message || 'Ukendt fejl'), 'error');
      }
    } catch (err) {
      this._toast('Fejl ved sirenetest: ' + String(err), 'error');
    }

    this._sirenTestRunning = false;
    if (btn) { btn.disabled = false; btn.innerHTML = icon('siren') + ' Test Sound'; }
  }

  async _quickTestLights() {
    if (this._lightsTestRunning || this._testRunning) return;
    this._lightsTestRunning = true;

    // Update button in-place without re-render (which would close the dialog)
    const btn = this.shadowRoot.querySelector("[data-action='quick-test-lights']");
    if (btn) { btn.disabled = true; btn.textContent = 'Testing...'; }

    try {
      const result = await this._callWS('quick_test_lights');
      if (result?.success) {
        const tested = result.details?.lights_tested?.join(', ') || 'done';
        this._toast('Blinktest OK: ' + tested, 'success');
      } else {
        this._toast('Blinktest fejlede: ' + (result?.message || 'Ukendt fejl'), 'error');
      }
    } catch (err) {
      this._toast('Fejl ved blinktest: ' + String(err), 'error');
    }

    this._lightsTestRunning = false;
    if (btn) { btn.disabled = false; btn.innerHTML = icon('lights') + ' Test Flash'; }
  }

  // ===
  // ===
  // === Entity Loading ===
  async _loadEntitiesByDomain(domain) {
    if (!this._hass) return [];
    
    // Cache entities to avoid repeated filtering
    if (this._availableEntities[domain]) {
      return this._availableEntities[domain];
    }
    
    const entities = Object.values(this._hass.states)
      .filter(entity => entity.entity_id.startsWith(domain + '.'))
      .map(entity => ({
        entity_id: entity.entity_id,
        name: entity.attributes.friendly_name || entity.entity_id,
        state: entity.state
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    
    this._availableEntities[domain] = entities;
    return entities;
  }

  // Load ALL entities for manual search fallback
  async _loadAllEntities() {
    if (this._allEntities) return this._allEntities;
    if (!this._hass) return [];
    this._allEntities = Object.values(this._hass.states)
      .map(e => ({
        entity_id: e.entity_id,
        name: e.attributes.friendly_name || e.entity_id,
        domain: e.entity_id.split('.')[0],
        state: e.state
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    return this._allEntities;
  }

  // === Camera Config Dialog ===
  async _openCameraConfig() {
    // Load available entities
    await this._loadEntitiesByDomain('camera');
    await this._loadEntitiesByDomain('switch');
    
    // Initialize temp config from current module config
    const currentConfig = this._data.modules.camera || {};
    this._tempConfig = {
      cameras: currentConfig.cameras || []
    };
    
    // Ensure at least one camera for new config
    if (this._tempConfig.cameras.length === 0) {
      this._tempConfig.cameras.push({
        id: Date.now(),
        entity_id: '',
        poe_port: '',
        recording_mode: 'continuous'
      });
    } else {
      // Add IDs if missing
      this._tempConfig.cameras = this._tempConfig.cameras.map((cam, idx) => ({
        ...cam,
        id: cam.id || Date.now() + idx
      }));
    }
    
    this._showDialog = 'camera';
    this._render();
  }

  _addCameraRow() {
    this._tempConfig.cameras.push({
      id: Date.now(),
      entity_id: '',
      poe_port: '',
      recording_mode: 'continuous'
    });
    this._render();
  }

  _removeCameraRow(id) {
    this._tempConfig.cameras = this._tempConfig.cameras.filter(c => c.id !== id);
    this._render();
  }

  _updateCameraField(id, field, value) {
    const camera = this._tempConfig.cameras.find(c => c.id === id);
    if (camera) {
      camera[field] = value;
    }
  }

  async _saveCameraConfig() {
    if (this._cameraSaving) return;
    // Validation
    const invalid = this._tempConfig.cameras.filter(c => !c.entity_id);
    if (invalid.length > 0) {
      this._toast('Vælg en kamera-entitet for alle kameraer før du gemmer.', 'warning'); return;
    }
    this._cameraSaving = true;
    
    // Build config
    const config = {
      enabled: true,
      cameras: this._tempConfig.cameras.map(c => ({
        entity_id: c.entity_id,
        poe_port: c.poe_port || null,
        recording_mode: c.recording_mode || 'continuous'
      }))
    };
    
    // Save via WebSocket
    const result = await this._callWS('save_module', {
      module_id: 'camera',
      config: config
    });
    
    if (result && result.success !== false) {
      this._cameraSaving = false;
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      this._toast('Kamerakonfiguration gemt! Aktiv med det samme.', 'success');
    } else {
      this._cameraSaving = false;
      this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error');
    }
  }

  _cancelDialog() {
    this._showDialog = null;
    this._tempConfig = null;
    this._render();
  }

  _renderCameraDialog() {
    const cameras = this._tempConfig?.cameras || [];
    const availableCameras = this._availableEntities.camera || [];
    const availableSwitches = this._availableEntities.switch || [];
    
    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            
            <div class="dialog-title">Konfiguration af kameramodul</div>
            <button class="dialog-close" data-action="close-dialog">${icon("close")}</button>
          </div>
          
          <button class="add-item-btn" data-action="add-camera">
            ${icon("plus")} Add Camera
          </button>
          
          <div class="item-list">
            ${cameras.length === 0 ? 
              '<div style="text-align:center;color:var(--sm-text-secondary);padding:20px;">Ingen kameraer konfigureret. Klik "Tilføj kamera" for at starte.</div>' :
              cameras.map((cam, idx) => this._renderCameraRow(cam, idx)).join('')
            }
          </div>
          
          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">
              Cancel
            </button>
            <button class="btn-dialog save" data-action="save-camera-config">
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    `;
  }

  _renderCameraRow(camera, idx) {
    const availableCameras = this._availableEntities.camera || [];
    const availableSwitches = this._availableEntities.switch || [];
    
    return `
      <div class="item-card">
        <div class="item-header">
          <div class="item-number">Camera ${idx + 1}</div>
          <button class="delete-item-btn" data-action="remove-camera" data-camera-id="${camera.id}">
             Delete
          </button>
        </div>
        
        <div class="form-group">
          <label class="form-label">Kamera-entitet</label>
          <input type="text" 
                 class="entity-search" 
                 placeholder="Søg kameraer..."
                 data-search-target="camera-select-${camera.id}">
          <select class="form-select" 
                  id="camera-select-${camera.id}"
                  data-camera-id="${camera.id}"
                  data-field="entity_id">
            <option value="">-- Vælg kamera --</option>
            ${availableCameras.map(c => `
              <option value="${c.entity_id}" ${c.entity_id === camera.entity_id ? 'selected' : ''}>
                ${c.name} (${c.entity_id})
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            POE Port Switch 
            <span class="optional-hint">(Optional)</span>
          </label>
          <select class="form-select"
                  data-camera-id="${camera.id}"
                  data-field="poe_port">
            <option value="">-- No POE Control --</option>
            ${availableSwitches
              .filter(s => s.entity_id.includes('poe') || s.entity_id.includes('port'))
              .map(s => `
                <option value="${s.entity_id}" ${s.entity_id === camera.poe_port ? 'selected' : ''}>
                  ${s.name} (${s.entity_id})
                </option>
              `).join('')}
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">Optagelsestilstand</label>
          <div class="radio-group">
            <div class="radio-option ${camera.recording_mode === 'disabled' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="disabled">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="disabled"
                     ${camera.recording_mode === 'disabled' ? 'checked' : ''}>
              <label>Deaktiveret</label>
            </div>
            <div class="radio-option ${camera.recording_mode === 'continuous' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="continuous">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="continuous"
                     ${camera.recording_mode === 'continuous' ? 'checked' : ''}>
              <label>Kontinuerlig optagelse</label>
            </div>
            <div class="radio-option ${camera.recording_mode === 'motion' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="motion">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="motion"
                     ${camera.recording_mode === 'motion' ? 'checked' : ''}>
              <label>Bevægelsesudløst</label>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // === Lock Config Dialog ===
  async _openLockConfig() {
    await this._loadEntitiesByDomain('lock');
    await this._loadAllEntities();
    const currentConfig = this._data.modules?.lock || {};
    this._tempConfig = {
      locks: (currentConfig.locks || []).map((l, i) => ({...l, id: l.id || Date.now() + i}))
    };
    if (this._tempConfig.locks.length === 0) {
      this._tempConfig.locks.push({ id: Date.now(), entity_id: '', lock_on_arm: true, unlock_on_disarm: false, retry_attempts: 3, retry_delay: 5 });
    }
    this._lockSearch = '';
    this._showDialog = 'lock';
    this._render();
  }

  _addLockRow() {
    this._tempConfig.locks.push({ id: Date.now(), entity_id: '', lock_on_arm: true, unlock_on_disarm: false, retry_attempts: 3, retry_delay: 5 });
    this._render();
  }

  _removeLockRow(id) {
    this._tempConfig.locks = this._tempConfig.locks.filter(l => l.id !== id);
    this._render();
  }

  _updateLockField(id, field, value) {
    const l = this._tempConfig.locks.find(l => l.id === id);
    if (!l) return;
    if (field === 'lock_on_arm' || field === 'unlock_on_disarm') l[field] = (value === true || value === 'true');
    else if (field === 'retry_attempts' || field === 'retry_delay') l[field] = parseInt(value) || 0;
    else l[field] = value;
  }

  async _saveLockConfig() {
    if (this._lockSaving) return;
    this._lockSaving = true;
    const invalid = this._tempConfig.locks.filter(l => !l.entity_id);
    if (invalid.length > 0) { this._toast('Vælg en entitet for alle låse.', 'warning'); return; }
    const config = { enabled: true, locks: this._tempConfig.locks.map(l => ({ entity_id: l.entity_id, lock_on_arm: l.lock_on_arm, unlock_on_disarm: l.unlock_on_disarm, retry_attempts: l.retry_attempts, retry_delay: l.retry_delay })) };
    const result = await this._callWS('save_module', { module_id: 'lock', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Låsekonfiguration gemt! Aktiv med det samme.', 'success');
    } else { this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error'); }
  }

  _renderLockDialog() {
    const locks = this._tempConfig?.locks || [];
    const domainLocks = this._availableEntities.lock || [];
    const allEntities = this._allEntities || [];
    const search = (this._lockSearch || '').toLowerCase();
    const filtered = search.length > 1
      ? allEntities.filter(e => e.name.toLowerCase().includes(search) || e.entity_id.toLowerCase().includes(search)).slice(0, 20)
      : domainLocks;

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            <div class="dialog-title">Konfiguration af låsemodul</div>
            <button class="dialog-close" data-action="close-dialog">${icon("close")}</button>
          </div>

          <div class="info-card ${domainLocks.length > 0 ? 'success' : 'warning'}">
            ${domainLocks.length > 0
              ? `<span style="color:var(--sm-accent)">${icon("check")}</span><div>Fandt ${domainLocks.length} låse-entitet(er) i Home Assistant</div>`
              : `<span style="color:var(--sm-warning)">${icon("warn")}</span><div>Ingen låse-entiteter fundet. Brug manuel søgning nedenfor for at tilføje en entitet.</div>`
            }
          </div>

          <button class="add-item-btn" data-action="add-lock">
            ${icon("plus")} Add Lock
          </button>

          <div class="item-list" style="display:flex;flex-direction:column;gap:12px;">
          ${locks.map((lock, idx) => `
          <div style="background:rgba(255,255,255,0.05);border:1px solid var(--sm-border,#333);border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;font-size:14px;color:var(--sm-text,#fff);">Lock ${idx + 1}</span>
              <button data-action="remove-lock" data-lock-id="${lock.id}" style="background:rgba(255,69,58,0.15);border:1px solid #ff453a;color:#ff453a;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;">Fjern</button>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:6px;">Entitet</label>
              ${lock.entity_id ? `<div style="padding:8px 12px;background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:6px;font-size:13px;color:#34c759;margin-bottom:6px;"> ${lock.entity_id}</div>` : ''}
              <div style="display:flex;gap:6px;align-items:center;margin-bottom:6px;">
                <input type="text" placeholder="Search entities (type 2+ chars)..." 
                  data-lock-search="${lock.id}"
                  style="flex:1;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;" 
                  value="${search}">
              </div>
              <select data-lock-id="${lock.id}" data-field="entity_id" style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="">-- Vælg entitet --</option>
                ${filtered.map(e => `<option value="${e.entity_id}" ${e.entity_id === lock.entity_id ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('')}
                ${!filtered.find(e => e.entity_id === lock.entity_id) && lock.entity_id ? `<option value="${lock.entity_id}" selected>${lock.entity_id}</option>` : ''}
              </select>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:8px;">Adfærd</label>
              <label style="display:flex;align-items:center;gap:8px;margin-bottom:8px;cursor:pointer;">
                <input type="checkbox" data-lock-id="${lock.id}" data-field="lock_on_arm" ${lock.lock_on_arm ? 'checked' : ''} style="width:16px;height:16px;cursor:pointer;">
                <span style="font-size:13px;color:var(--sm-text,#fff);">Lås når alarmen tilkobles</span>
              </label>
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                <input type="checkbox" data-lock-id="${lock.id}" data-field="unlock_on_disarm" ${lock.unlock_on_disarm ? 'checked' : ''} style="width:16px;height:16px;cursor:pointer;">
                <span style="font-size:13px;color:var(--sm-text,#fff);">Lås op når alarmen frakobles</span>
              </label>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Antal forsøg</label>
                <input type="number" min="0" max="10" data-lock-id="${lock.id}" data-field="retry_attempts" value="${lock.retry_attempts}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Retry delay (sec)</label>
                <input type="number" min="0" max="60" data-lock-id="${lock.id}" data-field="retry_delay" value="${lock.retry_delay}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
            </div>
          </div>`).join('')}
        </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="btn-dialog save" data-action="save-lock-config">Gem konfiguration</button>
          </div>
        </div>
      </div>
    `;
  }

  // === Climate Config Dialog ===
  async _openClimateConfig() {
    await this._loadEntitiesByDomain('climate');
    await this._loadAllEntities();
    const cur = this._data.modules?.climate || {};
    this._tempConfig = {
      thermostats: (cur.thermostats || []).map((t, i) => ({...t, id: t.id || Date.now() + i}))
    };
    if (this._tempConfig.thermostats.length === 0) {
      this._tempConfig.thermostats.push({ id: Date.now(), entity_id: '', arm_mode: 'eco', disarm_mode: 'heat', eco_temp: 18, comfort_temp: 22 });
    }
    this._showDialog = 'climate';
    this._render();
  }

  _addClimateRow() {
    this._tempConfig.thermostats.push({ id: Date.now(), entity_id: '', arm_mode: 'eco', disarm_mode: 'heat', eco_temp: 18, comfort_temp: 22 });
    this._render();
  }

  _removeClimateRow(id) {
    this._tempConfig.thermostats = this._tempConfig.thermostats.filter(t => t.id !== id);
    this._render();
  }

  _updateClimateField(id, field, value) {
    const t = this._tempConfig.thermostats.find(t => t.id === id);
    if (!t) return;
    if (field === 'eco_temp' || field === 'comfort_temp') t[field] = parseFloat(value) || 0;
    else t[field] = value;
  }

  async _saveClimateConfig() {
    if (this._climateSaving) return;
    this._climateSaving = true;
    const invalid = this._tempConfig.thermostats.filter(t => !t.entity_id);
    if (invalid.length > 0) { this._toast('Vælg en entitet for alle termostater.', 'warning'); return; }
    const config = { enabled: true, thermostats: this._tempConfig.thermostats.map(t => ({ entity_id: t.entity_id, arm_mode: t.arm_mode, disarm_mode: t.disarm_mode, eco_temp: t.eco_temp, comfort_temp: t.comfort_temp })) };
    const result = await this._callWS('save_module', { module_id: 'climate', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Klimakonfiguration gemt! Aktiv med det samme.', 'success');
    } else { this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error'); }
  }

  _renderClimateDialog() {
    const thermostats = this._tempConfig?.thermostats || [];
    const domainEntities = this._availableEntities.climate || [];
    const allEntities = this._allEntities || [];

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            <div class="dialog-title">Konfiguration af klimamodul</div>
            <button class="dialog-close" data-action="close-dialog">${icon("close")}</button>
          </div>

          <div class="info-card ${domainEntities.length > 0 ? 'success' : 'warning'}">
            ${domainEntities.length > 0
              ? `<span style="color:var(--sm-accent)">${icon("check")}</span><div>Fandt ${domainEntities.length} klima-entitet(er) i Home Assistant</div>`
              : `<span style="color:var(--sm-warning)">${icon("warn")}</span><div>Ingen klima-entiteter fundet. Brug manuel søgning for at tilføje en entitet.</div>`
            }
          </div>

          <button class="add-item-btn" data-action="add-climate">
            ${icon("plus")} Add Thermostat
          </button>

          <div class="item-list" style="display:flex;flex-direction:column;gap:12px;">
          ${thermostats.map((t, idx) => `
          <div style="background:rgba(255,255,255,0.05);border:1px solid var(--sm-border,#333);border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;font-size:14px;color:var(--sm-text,#fff);">Thermostat ${idx + 1}</span>
              <button data-action="remove-climate" data-climate-id="${t.id}" style="background:rgba(255,69,58,0.15);border:1px solid #ff453a;color:#ff453a;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;">Fjern</button>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:6px;">Entitet</label>
              ${t.entity_id ? `<div style="padding:8px 12px;background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:6px;font-size:13px;color:#34c759;margin-bottom:6px;"> ${t.entity_id}</div>` : ''}
              <input type="text" placeholder="Search entities (type 2+ chars for all, or leave blank for climate only)..."
                data-climate-search="${t.id}"
                style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;margin-bottom:6px;">
              <select data-climate-id="${t.id}" data-field="entity_id" style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="">-- Vælg entitet --</option>
                ${domainEntities.map(e => `<option value="${e.entity_id}" ${e.entity_id === t.entity_id ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('')}
                ${!domainEntities.find(e => e.entity_id === t.entity_id) && t.entity_id ? `<option value="${t.entity_id}" selected>${t.entity_id}</option>` : ''}
              </select>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Når tilkoblet</label>
                <select data-climate-id="${t.id}" data-field="arm_mode" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                  <option value="off" ${t.arm_mode==='off'?'selected':''}>Sluk</option>
                  <option value="eco" ${t.arm_mode==='eco'?'selected':''}>Eco-tilstand</option>
                  <option value="away" ${t.arm_mode==='away'?'selected':''}>Væk-tilstand</option>
                </select>
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Når frakoblet</label>
                <select data-climate-id="${t.id}" data-field="disarm_mode" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                  <option value="heat" ${t.disarm_mode==='heat'?'selected':''}>Varme</option>
                  <option value="cool" ${t.disarm_mode==='cool'?'selected':''}>Køl</option>
                  <option value="auto" ${t.disarm_mode==='auto'?'selected':''}>Auto</option>
                  <option value="restore" ${t.disarm_mode==='restore'?'selected':''}>Gendan forrige</option>
                </select>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Eco Temp (</label>
                <input type="number" min="10" max="30" step="0.5" data-climate-id="${t.id}" data-field="eco_temp" value="${t.eco_temp}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Comfort Temp (</label>
                <input type="number" min="10" max="30" step="0.5" data-climate-id="${t.id}" data-field="comfort_temp" value="${t.comfort_temp}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
            </div>
          </div>`).join('')}
        </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="btn-dialog save" data-action="save-climate-config">Gem konfiguration</button>
          </div>
        </div>
      </div>
    `;
  }

  // === Siren Config Dialog ===
  async _openSirenConfig() {
    await this._loadEntitiesByDomain('siren');
    await this._loadEntitiesByDomain('switch');
    await this._loadEntitiesByDomain('input_boolean');
    
    const currentConfig = this._data.modules.siren || {};
    this._tempConfig = {
      sirens: currentConfig.sirens || []
    };
    
    if (this._tempConfig.sirens.length === 0) {
      this._tempConfig.sirens.push({
        id: Date.now(),
        entity_id: '',
        pattern: 'continuous',
        duration: 300,
        volume: 80
      });
    } else {
      this._tempConfig.sirens = this._tempConfig.sirens.map((s, idx) => ({
        ...s,
        id: s.id || Date.now() + idx
      }));
    }
    
    this._showDialog = 'siren';
    this._render();
  }

  _addSirenRow() {
    this._tempConfig.sirens.push({
      id: Date.now(),
      entity_id: '',
      pattern: 'continuous',
      duration: 300,
      volume: 80
    });
    this._render();
  }

  _removeSirenRow(id) {
    this._tempConfig.sirens = this._tempConfig.sirens.filter(s => s.id !== id);
    this._render();
  }

  _updateSirenField(id, field, value) {
    const siren = this._tempConfig.sirens.find(s => s.id === id);
    if (siren) {
      if (field === 'duration' || field === 'volume') {
        siren[field] = parseInt(value) || 0;
      } else {
        siren[field] = value;
      }
    }
  }

  async _saveSirenConfig() {
    if (this._sirenSaving) return;
    this._sirenSaving = true;
    const invalid = this._tempConfig.sirens.filter(s => !s.entity_id);
    if (invalid.length > 0) {
      this._toast('Vælg en sirene-entitet for alle sirener før du gemmer.', 'warning'); return;
      return;
    }
    
    const config = {
      enabled: true,
      sirens: this._tempConfig.sirens.map(s => ({
        entity_id: s.entity_id,
        pattern: s.pattern,
        duration: s.duration,
        volume: s.volume
      }))
    };
    
    const result = await this._callWS('save_module', {
      module_id: 'siren',
      config: config
    });
    
    if (result && result.success !== false) {
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      this._toast('Sirenekonfiguration gemt! Aktiv med det samme.', 'success');
    } else {
      this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error');
    }
  }

  _renderSirenDialog() {
    const sirens = this._tempConfig?.sirens || [];
    const availableSirens = this._availableEntities.siren || [];
    
    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            
            <div class="dialog-title">Konfiguration af sirenemodul</div>
            <button class="dialog-close" data-action="close-dialog">${icon("close")}</button>
          </div>
          
          <button class="add-item-btn" data-action="add-siren">
            ${icon("plus")} Add Siren
          </button>
          
          <div class="item-list">
            ${sirens.length === 0 ? 
              '<div style="text-align:center;color:var(--sm-text-secondary);padding:20px;">Ingen sirener konfigureret.</div>' :
              sirens.map((s, idx) => this._renderSirenRow(s, idx)).join('')
            }
          </div>
          
          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="sm-btn ghost-outlined" data-action="quick-test-siren"
                    ${this._sirenTestRunning ? 'disabled' : ''}
                    style="font-size:12px;padding:6px 12px;display:flex;align-items:center;gap:5px">
              ${icon("siren")} ${this._sirenTestRunning ? 'Testing...' : 'Test Sound'}
            </button>
            <button class="btn-dialog save" data-action="save-siren-config">Gem konfiguration</button>
          </div>
        </div>
      </div>
    `;
  }

  _renderSirenRow(siren, idx) {
    const availableSirens       = this._availableEntities.siren         || [];
    const availableSwitches     = this._availableEntities.switch        || [];
    const availableInputBooleans = this._availableEntities.input_boolean || [];

    const domainGroups = [
      { label: 'Siren entities',                     entities: availableSirens,        domain: 'siren' },
      { label: 'Switch entities (dumb sirens)',       entities: availableSwitches,      domain: 'switch' },
      { label: 'Input Boolean (virtual triggers)',    entities: availableInputBooleans, domain: 'input_boolean' }
    ];

    const isOnOff = siren.entity_id &&
      (siren.entity_id.startsWith('switch.') || siren.entity_id.startsWith('input_boolean.'));

    const domainColor = siren.entity_id
      ? (siren.entity_id.startsWith('siren.')         ? 'var(--sm-primary)'
       : siren.entity_id.startsWith('input_boolean.') ? 'var(--sm-success)'
       :                                                 'var(--sm-warning)')
      : '';

    const domainLabel = siren.entity_id
      ? (siren.entity_id.startsWith('siren.')         ? 'siren'
       : siren.entity_id.startsWith('input_boolean.') ? 'input_boolean (on/off)'
       :                                                 'switch (on/off)')
      : '';

    return `
      <div class="item-card">
        <div class="item-header">
          <div class="item-number">Siren ${idx + 1}</div>
          <button class="delete-item-btn" data-action="remove-siren" data-siren-id="${siren.id}">Slet</button>
        </div>

        <div class="form-group">
          <label class="form-label">Sirene-entitet</label>
          <input type="text" class="entity-search" placeholder="Search siren, switch or input_boolean..." data-search-target="siren-select-${siren.id}">
          <select class="form-select" id="siren-select-${siren.id}" data-siren-id="${siren.id}" data-field="entity_id">
            <option value="">-- Vælg entitet --</option>
            ${domainGroups.map(group => group.entities.length === 0 ? '' : `
              <optgroup label="${group.label}">
                ${group.entities.map(e => `
                  <option value="${e.entity_id}" ${e.entity_id === siren.entity_id ? 'selected' : ''}>${e.name} (${e.entity_id})</option>
                `).join('')}
              </optgroup>
            `).join('')}
          </select>
          ${siren.entity_id ? `
            <div style="margin-top:6px;font-size:11px;color:var(--sm-text-tertiary)">
              Domain: <span style="font-weight:600;color:${domainColor}">${domainLabel}</span>
            </div>
          ` : ''}
        </div>

        <div class="form-group">
          <label class="form-label">Alarmmønster</label>
          <select class="form-select" data-siren-id="${siren.id}" data-field="pattern">
            <option value="continuous" ${siren.pattern === 'continuous' ? 'selected' : ''}>Kontinuerlig</option>
            <option value="intermittent" ${siren.pattern === 'intermittent' ? 'selected' : ''}>Periodisk</option>
            <option value="rapid" ${siren.pattern === 'rapid' ? 'selected' : ''}>Hurtige bip</option>
          </select>
          ${isOnOff ? `
            <div style="margin-top:4px;font-size:11px;color:var(--sm-text-tertiary)">
              This entity type uses on/off only. Pattern has no effect.
            </div>
          ` : ''}
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="form-group">
            <label class="form-label">Duration (seconds)</label>
            <input type="number" class="form-input" min="10" max="600" step="10" data-siren-id="${siren.id}" data-field="duration" value="${siren.duration}">
          </div>
          <div class="form-group">
            <label class="form-label">Volume (%)</label>
            <input type="number" class="form-input" min="0" max="100" step="5" data-siren-id="${siren.id}" data-field="volume" value="${siren.volume}"
              ${isOnOff ? 'disabled style="opacity:0.4"' : ''}>
          </div>
        </div>
      </div>
    `;
  }



  // === Lights Config Dialog ===
  async _openLightsConfig() {
    await this._loadEntitiesByDomain('light');
    await this._loadAllEntities();
    const cur = this._data.modules?.lights || {};
    this._tempConfig = {
      entities: cur.entities || [],
      steady_entities: cur.steady_entities || [],
      arm_action: cur.arm_action || 'turn_off',
      disarm_action: cur.disarm_action || 'restore',
      trigger_flash: cur.trigger_flash !== false,
      flash_pattern: cur.flash_pattern || 'rapid',
      flash_duration: cur.flash_duration || 30
    };
    this._showDialog = 'lights';
    this._render();
  }

  _addLightEntity(entityId) {
    if (entityId && !this._tempConfig.entities.includes(entityId)) {
      this._tempConfig.entities.push(entityId);
      this._render();
    }
  }

  _removeLightEntity(entityId) {
    this._tempConfig.entities = this._tempConfig.entities.filter(e => e !== entityId);
    this._rebuildDialog();
  }

  _updateLightsField(field, value) {
    if (field === 'trigger_flash') this._tempConfig[field] = (value === true || value === 'true');
    else if (field === 'flash_duration') this._tempConfig[field] = parseInt(value) || 30;
    else this._tempConfig[field] = value;
  }

  async _saveLightsConfig() {
    if (this._lightsSaving) return;
    this._lightsSaving = true;
    if (this._tempConfig.entities.length === 0) { this._toast('Tilføj mindst ét lys-entitet.', 'warning'); return; }
    const config = { enabled: true, entities: this._tempConfig.entities, steady_entities: this._tempConfig.steady_entities || [], arm_action: this._tempConfig.arm_action, disarm_action: this._tempConfig.disarm_action, trigger_flash: this._tempConfig.trigger_flash, flash_pattern: this._tempConfig.flash_pattern, flash_duration: this._tempConfig.flash_duration };
    const result = await this._callWS('save_module', { module_id: 'lights', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Lyskonfiguration gemt! Aktiv med det samme.', 'success');
    } else { this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error'); }
  }

  _renderLightPicker(pickerId, available, accentColor) {
    // Inline multi-select picker: search box + scrollable checkbox list
    const rows = available.slice(0, 80).map(e =>
      `<label data-lp-row style="display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:5px;cursor:pointer;font-size:12px;color:var(--sm-text);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
        <input type="checkbox" data-lp-cb data-entity="${e.entity_id}" style="width:14px;height:14px;cursor:pointer;accent-color:${accentColor};">
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${e.name}</span>
        <span style="font-size:10px;color:var(--sm-text-tertiary);font-family:'DM Mono',monospace;flex-shrink:0">${e.entity_id.split('.')[1]}</span>
      </label>`
    ).join('');
    return `
      <div style="position:relative;margin-top:6px;">
        <input data-lp-search="${pickerId}" type="text" placeholder="Søg lys..." autocomplete="off"
          style="width:100%;padding:7px 10px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px 6px 0 0;color:var(--sm-text,#fff);font-size:12px;box-sizing:border-box;outline:none;">
        <div data-lp-list="${pickerId}"
          style="max-height:160px;overflow-y:auto;background:rgba(28,28,30,0.98);border:1px solid var(--sm-border,#444);border-top:none;border-radius:0 0 6px 6px;padding:2px 0;">
          ${rows || '<span style="display:block;padding:8px 10px;font-size:12px;color:var(--sm-text-tertiary);">Ingen lys tilgængelige</span>'}
        </div>
        <div style="display:flex;justify-content:flex-end;margin-top:5px;">
          <button data-lp-add="${pickerId}" style="padding:5px 14px;background:${accentColor}22;border:1px solid ${accentColor}66;border-radius:6px;color:${accentColor};font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Tilføj valgte</button>
        </div>
      </div>`;
  }

  _renderLightsDialog() {
    const selected = this._tempConfig?.entities || [];
    const steadySelected = this._tempConfig?.steady_entities || [];
    const domainLights = this._availableEntities.light || [];
    const allUsed = [...selected, ...steadySelected];
    const availableForFlash = domainLights.filter(l => !allUsed.includes(l.entity_id));
    const availableForSteady = domainLights.filter(l => !allUsed.includes(l.entity_id));

    const chipStyle = (color) => `display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:${color}26;border:1px solid ${color}66;border-radius:20px;font-size:12px;color:${color}`;
    const sectionBox = `padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--sm-border,#333);border-radius:8px;margin-bottom:14px`;

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            <div class="dialog-title">Konfiguration af lysmodul</div>
            <button class="dialog-close" data-action="close-dialog">${icon("close")}</button>
          </div>

          <!-- ARM / DISARM behaviour -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
            <div>
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Når tilkoblet</label>
              <select data-lights-field="arm_action" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="turn_off" ${this._tempConfig?.arm_action==='turn_off'?'selected':''}>Sluk</option>
                <option value="leave" ${this._tempConfig?.arm_action==='leave'?'selected':''}>Lad være som den er</option>
              </select>
            </div>
            <div>
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Når frakoblet</label>
              <select data-lights-field="disarm_action" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="restore" ${this._tempConfig?.disarm_action==='restore'?'selected':''}>Gendan forrige</option>
                <option value="turn_on" ${this._tempConfig?.disarm_action==='turn_on'?'selected':''}>Tænd</option>
              </select>
            </div>
          </div>

          <!-- SECTION 1: Flash lights -->
          <div style="${sectionBox}">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:13px;font-weight:500;color:var(--sm-text,#fff);">Blink lys ved alarm</span>
                <span style="font-size:11px;color:var(--sm-text-secondary);">(red / blue)</span>
              </div>
              <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                <input type="checkbox" data-lights-field="trigger_flash" ${this._tempConfig?.trigger_flash?'checked':''} style="width:16px;height:16px;cursor:pointer;">
                <span style="font-size:12px;color:var(--sm-text-secondary);">Aktiveret</span>
              </label>
            </div>

            <div style="min-height:36px;padding:6px;background:rgba(255,255,255,0.04);border:1px solid var(--sm-border,#333);border-radius:8px;display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
              ${selected.length === 0
                ? '<span style="color:#666;font-size:12px;padding:4px 6px;">Ingen blinklys valgt</span>'
                : selected.map(eid => {
                    const e = domainLights.find(l => l.entity_id === eid);
                    return `<span style="${chipStyle('#ff9f0a')}">${e?.name || eid}<button data-action="remove-light" data-entity="${eid}" style="background:none;border:none;color:inherit;cursor:pointer;font-size:14px;line-height:1;padding:0;margin-left:4px;" title="Remove">&#x2715;</button></span>`;
                  }).join('')
              }
            </div>
            ${this._renderLightPicker('flash', availableForFlash, '#ff9f0a')}

            ${this._tempConfig?.trigger_flash ? `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Blinkmønster</label>
                <select data-lights-field="flash_pattern" style="width:100%;padding:7px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                  <option value="rapid" ${this._tempConfig?.flash_pattern==='rapid'?'selected':''}>Hurtig</option>
                  <option value="slow" ${this._tempConfig?.flash_pattern==='slow'?'selected':''}>Langsom</option>
                  <option value="intermittent" ${this._tempConfig?.flash_pattern==='intermittent'?'selected':''}>Periodisk</option>
                </select>
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Duration (seconds)</label>
                <input type="number" min="5" max="300" data-lights-field="flash_duration" value="${this._tempConfig?.flash_duration||30}" style="width:100%;padding:7px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
            </div>` : ''}
          </div>

          <!-- SECTION 2: Steady white lights -->
          <div style="${sectionBox}">
            <div style="margin-bottom:10px;">
              <span style="font-size:13px;font-weight:500;color:var(--sm-text,#fff);">Konstant hvidt lys ved alarm</span>
              <div style="font-size:11px;color:var(--sm-text-secondary);margin-top:2px;">Turns on immediately at 100% white brightness. No flashing.</div>
            </div>

            <div style="min-height:36px;padding:6px;background:rgba(255,255,255,0.04);border:1px solid var(--sm-border,#333);border-radius:8px;display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
              ${steadySelected.length === 0
                ? '<span style="color:#666;font-size:12px;padding:4px 6px;">Intet konstant lys valgt</span>'
                : steadySelected.map(eid => {
                    const e = domainLights.find(l => l.entity_id === eid);
                    return `<span style="${chipStyle('#64d2ff')}">${e?.name || eid}<button data-action="remove-steady-light" data-entity="${eid}" style="background:none;border:none;color:inherit;cursor:pointer;font-size:14px;line-height:1;padding:0;margin-left:4px;" title="Remove">&#x2715;</button></span>`;
                  }).join('')
              }
            </div>
            ${this._renderLightPicker('steady', availableForSteady, '#64d2ff')}
          </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="sm-btn ghost-outlined" data-action="quick-test-lights"
                    ${this._lightsTestRunning ? 'disabled' : ''}
                    style="font-size:12px;padding:6px 12px;display:flex;align-items:center;gap:5px">
              ${icon("bulb")} ${this._lightsTestRunning ? 'Testing...' : 'Test Flash'}
            </button>
            <button class="btn-dialog save" data-action="save-lights-config">Gem konfiguration</button>
          </div>
        </div>
      </div>
    `;
  }

  // === TTS Config Dialog ===
  // ─── Notification Dialog ──────────────────────────────────────────────────

  async _openNotificationDialog(editId = null) {
    await this._loadNotifyServices();
    const existing = editId ? this._data.notifications[editId] : null;
    this._tempConfig = {
      _editId: editId,
      name: existing?.name || '',
      trigger: existing?.trigger || 'armed',
      service: existing?.service || (this._availableServices?.[0] || 'notify.notify'),
      message: existing?.message || '',
      channels: existing?.channels || ['push'],
      enabled: existing?.enabled !== false,
      actions: existing?.actions || [],
      tts_speakers: existing?.tts_speakers || [],  // v1.4.3: [] = all speakers
    };
    this._showDialog = 'notification';
    this._render();
  }

  async _loadNotifyServices() {
    if (this._availableServices) return;
    try {
      const result = await this._callWS('get_notify_services', {});
      this._availableServices = result?.services || ['notify.notify'];
    } catch { this._availableServices = ['notify.notify']; }
  }

  async _saveNotificationDialog() {
    if (!this._tempConfig.name) { this._toast('Indtast et notifikationsnavn.', 'warning'); return; }
    if (!this._tempConfig.channels?.length) { this._toast('Vælg mindst én kanal.', 'warning'); return; }

    const notifId = this._tempConfig._editId || Math.random().toString(36).slice(2, 10) + Math.random().toString(36).slice(2, 10);
    const config = {
      name: this._tempConfig.name,
      trigger: this._tempConfig.trigger,
      service: this._tempConfig.service,
      message: this._tempConfig.message,
      channels: this._tempConfig.channels,
      enabled: this._tempConfig.enabled !== false,
      tts_speakers: this._tempConfig.tts_speakers || [],
    };

    const result = await this._callWS('save_notification', { notification_id: notifId, config });
    this._automationsRenderCache = null;
    if (result && result.success !== false) {
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      this._toast('Notifikation gemt!', 'success');
    } else {
      this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error');
    }
  }

  async _deleteNotification(notifId) {
    if (!notifId) return;
    const result = await this._callWS('delete_notification', { notification_id: notifId });
    this._automationsRenderCache = null;
    if (result && result.success !== false) {
      await this._loadData();
      this._toast('Notifikation slettet.', 'success');
    } else {
      this._toast('Kunne ikke slette notifikation.', 'error');
    }
  }

  _renderNotificationDialog() {
    const tc = this._tempConfig || {};
    const services = this._availableServices || ['notify.notify'];
    const channels = tc.channels || ['push'];
    const hasPush = channels.includes('push');
    const hasTTS  = channels.includes('tts');
    const ttsEnabled = this._data.modules?.tts?.enabled;

    const TRIGGERS = [
      { value: 'armed',             label: 'Armed (any mode)' },
      { value: 'disarmed',          label: 'Disarmed' },
      { value: 'triggered',         label: 'Triggered' },
      { value: 'arming',            label: 'Arming (exit delay)' },
      { value: 'pending',           label: 'Pending (entry delay)' },
      { value: 'low_battery',       label: 'Low Battery' },
      { value: 'smoke',             label: 'Smoke detected (critical)' },
      { value: 'water_leak',        label: 'Water leak (critical)' },
      { value: 'home_alone_action', label: 'Home Alone quick message' },
    ];

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog" style="max-width:500px">
          <div class="dialog-header">
            <div class="dialog-title">${tc._editId ? 'Rediger' : 'Tilføj'} notifikation</div>
            <button class="dialog-close" data-action="close-dialog">${icon('close')}</button>
          </div>

          <div class="form-group">
            <label class="form-label">Navn</label>
            <input type="text" class="form-input" id="notif-name"
                   placeholder="f.eks. Push ved tilkobling Borte" value="${tc.name || ''}">
          </div>

          <div class="form-group">
            <label class="form-label">Udløser</label>
            <select class="form-select" id="notif-trigger">
              ${TRIGGERS.map(t => `<option value="${t.value}" ${tc.trigger===t.value?'selected':''}>${t.label}</option>`).join('')}
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Besked</label>
            <input type="text" class="form-input" id="notif-message"
                   placeholder="e.g. Alarm armed by {armed_by}" value="${tc.message || ''}">
            <div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:4px">
              Variables: {state} {armed_by} {disarmed_by} {triggered_by} {sensor_list} {count}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Kanaler</label>
            <div style="display:flex;gap:12px;flex-wrap:wrap">
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px">
                <input type="checkbox" id="notif-ch-push" ${hasPush?'checked':''}>
                ${icon('bell')} Mobile push
              </label>
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px;${!ttsEnabled?'opacity:0.5':''}"
                     title="${!ttsEnabled?'Enable TTS module first':''}">
                <input type="checkbox" id="notif-ch-tts" ${hasTTS?'checked':''} ${!ttsEnabled?'disabled':''}>
                ${icon('speaker')} TTS voice
              </label>
            </div>
            ${!ttsEnabled ? '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:4px">TTS-kanal kræver at TTS-modulet er aktiveret.</div>' : ''}
          </div>

          ${hasTTS && ttsEnabled && this._speakerProfiles?.length > 0 ? `
          <div class="form-group" id="notif-tts-speakers" style="padding:10px;background:rgba(255,255,255,0.03);border:1px solid var(--sm-border);border-radius:8px">
            <label class="form-label" style="font-size:11px;margin-bottom:6px">TTS Speakers (all selected = use all)</label>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              ${(this._speakerProfiles || []).map(p => {
                const selected = !tc.tts_speakers?.length || tc.tts_speakers.includes(p.entity_id);
                return '<label style="display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;background:rgba(255,255,255,0.05);padding:3px 8px;border-radius:6px">' +
                  '<input type="checkbox" class="notif-tts-sp" data-sp-eid="' + p.entity_id + '" ' + (selected ? 'checked' : '') + '>' +
                  (p.name || p.entity_id) + '</label>';
              }).join('')}
            </div>
          </div>
          ` : ''}

          <div class="form-group" id="notif-service-group" style="${!hasPush?'display:none':''}">
            <label class="form-label">Notifikationstjeneste</label>
            <select class="form-select" id="notif-service">
              ${services.map(s => `<option value="${s}" ${tc.service===s?'selected':''}>${s}</option>`).join('')}
            </select>
          </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="btn-dialog save" data-action="save-notification-dialog">Gem</button>
          </div>
        </div>
      </div>
    `;
  }

  async _openTTSConfig() {
    await this._loadEntitiesByDomain('media_player');
    await this._loadEntitiesByDomain('tts');

    const currentConfig = this._data.modules.tts?.config || this._data.modules.tts || {};
    this._tempConfig = {
      entities: currentConfig.entities || [],
      tts_service: currentConfig.tts_service || 'tts.cloud_say',
      language: currentConfig.language || 'da',
      volume: currentConfig.volume !== undefined ? Math.round(currentConfig.volume * 100) : 50,
      custom_messages: (currentConfig.custom_messages || []).map(m => ({...m})),
      // v1.4.3: speaker profiles
      speaker_profiles: (this._speakerProfiles || []).map(p => ({...p})),
    };

    this._showDialog = 'tts';
    const dlgMount = this.shadowRoot?.getElementById('shell-dialog-mount');
    if (dlgMount) dlgMount.dataset.currentDialog = '';
    this._render();
  }

  _addTTSEntity(entityId) {
    if (entityId && !this._tempConfig.entities.includes(entityId)) {
      this._tempConfig.entities.push(entityId);
      this._patchTTSDialog();
    }
  }

  _removeTTSEntity(entityId) {
    this._tempConfig.entities = this._tempConfig.entities.filter(e => e !== entityId);
    this._patchTTSDialog();
  }

  // v1.4.3: Speaker profile methods
  _addSpeakerProfile(entityId) {
    if (!entityId) return;
    const existing = (this._tempConfig.speaker_profiles || []).find(p => p.entity_id === entityId);
    if (existing) return;
    const avail = this._availableEntities.media_player || [];
    const entity = avail.find(e => e.entity_id === entityId);
    this._tempConfig.speaker_profiles = this._tempConfig.speaker_profiles || [];
    this._tempConfig.speaker_profiles.push({
      entity_id: entityId,
      name: entity?.name || entityId,
      volume: 0.5,
      tts_service: 'tts.cloud_say',
      tts_entity: 'tts.home_assistant_cloud',
    });
    this._rebuildDialog();
  }

  _removeSpeakerProfile(entityId) {
    this._tempConfig.speaker_profiles = (this._tempConfig.speaker_profiles || [])
      .filter(p => p.entity_id !== entityId);
    this._rebuildDialog();
  }

  _updateSpeakerProfile(entityId, field, value) {
    const profile = (this._tempConfig.speaker_profiles || []).find(p => p.entity_id === entityId);
    if (!profile) return;
    if (field === 'volume') {
      profile.volume = parseFloat(value) / 100;
    } else {
      profile[field] = value;
    }
    // Update volume label inline without full rebuild
    if (field === 'volume') {
      const dlg = this.shadowRoot?.getElementById('shell-dialog-mount');
      const label = dlg?.querySelector('[data-vol-label="' + entityId + '"]');
      if (label) label.textContent = value + '%';
    }
  }

  _updateCustomMessageSpeakers(msgId, entityId, checked) {
    const msg = this._tempConfig?.custom_messages?.find(m => m.id === msgId);
    if (!msg) return;
    msg.speakers = msg.speakers || [];
    if (checked) {
      if (!msg.speakers.includes(entityId)) msg.speakers.push(entityId);
    } else {
      msg.speakers = msg.speakers.filter(s => s !== entityId);
    }
  }

  _patchTTSDialog() {
    const dialogMount = this.shadowRoot.getElementById('shell-dialog-mount');
    if (!dialogMount) { this._render(); return; }
    const availableMP = this._availableEntities.media_player || [];
    const selectedEntities = this._tempConfig.entities;
    const unselected = availableMP.filter(e => !selectedEntities.includes(e.entity_id));
    const chipsEl = dialogMount.querySelector('[data-tts-chips]');
    if (chipsEl) {
      chipsEl.innerHTML = selectedEntities.length === 0
        ? '<div style="text-align:center;color:var(--sm-text-tertiary);padding:16px;font-size:12px">Ingen højtalere tilføjet — valgfrit hvis du bruger en brugerdefineret TTS-tjeneste</div>'
        : selectedEntities.map(entityId => {
            const entity = availableMP.find(e => e.entity_id === entityId);
            return `<span class="entity-chip">${entity?.name || entityId}<button data-action="remove-tts" data-entity="${entityId}">${icon('close')}</button></span>`;
          }).join('');
      chipsEl.querySelectorAll('[data-action="remove-tts"]').forEach(b => {
        b.addEventListener('click', () => this._removeTTSEntity(b.dataset.entity));
      });
    }
    const addSelect = dialogMount.querySelector('#tts-add-select');
    if (addSelect) {
      addSelect.innerHTML = '<option value="">-- Tilføj højtaler --</option>' +
        unselected.map(e => `<option value="${e.entity_id}">${e.name} (${e.entity_id})</option>`).join('');
    }
  }

  _updateTTSField(field, value) {
    if (field === 'volume') {
      this._tempConfig.volume = parseInt(value) || 0;
    } else if (field === 'tts_service') {
      const customInput = this.shadowRoot.querySelector('#tts-service-custom');
      if (value === 'custom') {
        if (customInput) customInput.style.display = 'block';
      } else {
        if (customInput) customInput.style.display = 'none';
        this._tempConfig.tts_service = value;
      }
    } else {
      this._tempConfig[field] = value;
    }
  }

  _updateTTSCustomService(value) {
    if (value && value.trim()) {
      this._tempConfig.tts_service = value.trim();
    }
  }

  // Custom message CRUD
  _addTTSCustomMessage() {
    const newMsg = {
      id: 'msg_' + Date.now().toString(36),
      name: 'New message',
      type: 'tts',
      trigger: 'triggered',
      message: '',
      media_url: '',
      media_content_type: 'music',
      enabled: true,
    };
    this._tempConfig.custom_messages.push(newMsg);
    this._rebuildDialog();
  }

  _removeTTSCustomMessage(id) {
    this._tempConfig.custom_messages = this._tempConfig.custom_messages.filter(m => m.id !== id);
    this._rebuildDialog();
  }

  _rebuildDialog() {
    // Force dialog rebuild by resetting currentDialog marker,
    // then render (which rebuilds HTML) and attaches fresh listeners.
    const dlg = this.shadowRoot?.getElementById('shell-dialog-mount');
    if (dlg) {
      const scrollTop = dlg.querySelector('.config-dialog')?.scrollTop || 0;
      dlg.dataset.currentDialog = '';
      this._render();
      requestAnimationFrame(() => {
        const d = dlg.querySelector('.config-dialog');
        if (d && scrollTop) d.scrollTop = scrollTop;
      });
    } else {
      this._render();
    }
  }

  _updateTTSCustomMessage(id, field, value) {
    const msg = this._tempConfig.custom_messages.find(m => m.id === id);
    if (msg) {
      msg[field] = value;
      // Re-render only if type changes (shows/hides fields)
      if (field === 'type') this._rebuildDialog();
    }
  }

  async _testTTSMessage(message) {
    if (!message) { this._toast('Indtast en besked at teste.', 'warning'); return; }
    const result = await this._callWS('test_tts', { message });
    if (result && result.success !== false) {
      this._toast('TTS-test sendt!', 'success');
    } else {
      this._toast('TTS-test fejlede: ' + (result?.error || 'TTS-modul ikke aktiveret'), 'error');
    }
  }

  async _saveTTSConfig() {
    const config = {
      enabled: true,
      entities: this._tempConfig.entities,
      tts_service: this._tempConfig.tts_service || 'tts.cloud_say',
      language: this._tempConfig.language || 'da',
      volume: (this._tempConfig.volume || 50) / 100,
      custom_messages: this._tempConfig.custom_messages || [],
    };

    // Save TTS module config and speaker profiles in parallel
    const [result, spResult] = await Promise.all([
      this._callWS('save_module', { module_id: 'tts', config }),
      this._callWS('save_speaker_profiles', { profiles: this._tempConfig.speaker_profiles || [] }),
    ]);

    if (result && result.success !== false) {
      this._speakerProfiles = this._tempConfig.speaker_profiles || [];
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      this._toast('TTS-konfiguration gemt!', 'success');
    } else {
      this._toast('Kunne ikke gemme: ' + (result?.error || 'Ukendt fejl'), 'error');
    }
  }

  _renderTTSDialog() {
    const tc               = this._tempConfig || {};
    const profiles         = tc.speaker_profiles || [];
    const customMessages   = tc.custom_messages || [];
    const availableMP      = this._availableEntities.media_player || [];
    const unselected       = availableMP.filter(e => !profiles.some(p => p.entity_id === e.entity_id));
    const knownServices    = ['tts.cloud_say','tts.google_translate_say','tts.google_say','tts.piper','tts.voice_rss'];
    const isCustomService  = tc.tts_service && !knownServices.includes(tc.tts_service);

    const TRIGGERS = [
      { value: 'armed_away',       label: 'Armed Away' },
      { value: 'armed_home',       label: 'Armed Home' },
      { value: 'armed_night',      label: 'Armed Night' },
      { value: 'armed_vacation',   label: 'Armed Vacation' },
      { value: 'armed_home_alone', label: 'Home Alone' },
      { value: 'disarmed',         label: 'Disarmed' },
      { value: 'triggered',        label: 'Triggered' },
      { value: 'arming',           label: 'Arming (exit delay)' },
      { value: 'pending',          label: 'Pending (entry delay)' },
    ];

    const speakerCheckboxes = (msgId, msgSpeakers) =>
      profiles.length === 0
        ? '<div style="font-size:11px;color:var(--sm-text-tertiary)">Ingen højtalerprofiler konfigureret ovenfor.</div>'
        : '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px">' +
          profiles.map(p => {
            const checked = !msgSpeakers || msgSpeakers.length === 0 || msgSpeakers.includes(p.entity_id);
            return '<label style="display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;background:rgba(255,255,255,0.05);padding:3px 8px;border-radius:6px">' +
              '<input type="checkbox" data-msg-speaker-id="' + msgId + '" data-msg-speaker-eid="' + p.entity_id + '" ' + (checked ? 'checked' : '') + '>' +
              (p.name || p.entity_id) +
              '</label>';
          }).join('') +
          '</div>';

    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog" style="max-width:580px">
          <div class="dialog-header">
            <div class="dialog-title">TTS-modul</div>
            <button class="dialog-close" data-action="close-dialog">${icon('close')}</button>
          </div>

          <!-- GLOBAL SETTINGS -->
          <div class="form-group">
            <label class="form-label">Standard TTS-tjeneste</label>
            <select class="form-select" data-tts-field="tts_service" id="tts-service-select">
              <option value="tts.cloud_say" ${(tc.tts_service||'tts.cloud_say')==='tts.cloud_say'?'selected':''}>tts.cloud_say (Nabu Casa)</option>
              <option value="tts.google_translate_say" ${tc.tts_service==='tts.google_translate_say'?'selected':''}>tts.google_translate_say</option>
              <option value="tts.google_say" ${tc.tts_service==='tts.google_say'?'selected':''}>tts.google_say (Cast)</option>
              <option value="tts.piper" ${tc.tts_service==='tts.piper'?'selected':''}>tts.piper (local)</option>
              <option value="custom" ${isCustomService?'selected':''}>Brugerdefineret...</option>
            </select>
            ${isCustomService ? `<input type="text" class="form-input" id="tts-service-custom" style="margin-top:6px" placeholder="e.g. tts.my_custom_say" value="${tc.tts_service||''}">` : `<input type="text" class="form-input" id="tts-service-custom" style="margin-top:6px;display:none" placeholder="e.g. tts.my_custom_say">`}
          </div>

          <div class="form-group">
            <label class="form-label">Sprog</label>
            <select class="form-select" data-tts-field="language">
              <option value="da" ${(tc.language||'da')==='da'?'selected':''}>Dansk</option>
              <option value="en" ${tc.language==='en'?'selected':''}>Engelsk</option>
              <option value="de" ${tc.language==='de'?'selected':''}>Tysk</option>
              <option value="sv" ${tc.language==='sv'?'selected':''}>Svensk</option>
              <option value="nb" ${tc.language==='nb'?'selected':''}>Norsk</option>
            </select>
          </div>

          <!-- SPEAKER PROFILES -->
          <div class="form-group">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <label class="form-label" style="margin:0">Højtalerprofiler</label>
              <select class="form-select" id="sp-add-select" style="max-width:220px;font-size:12px">
                <option value="">-- Tilføj højtaler --</option>
                ${unselected.map(e => `<option value="${e.entity_id}">${e.name}</option>`).join('')}
              </select>
            </div>

            ${profiles.length === 0
              ? `<div style="text-align:center;color:var(--sm-text-tertiary);padding:16px;border:1px dashed var(--sm-border);border-radius:8px;font-size:12px">
                   No speaker profiles yet. Add a media_player above.
                 </div>`
              : profiles.map(p => {
                  const vol = Math.round((p.volume || 0.5) * 100);
                  const spServices = ['tts.cloud_say','tts.google_translate_say','tts.google_say','tts.piper'];
                  return `<div style="border:1px solid var(--sm-border);border-radius:8px;padding:12px;margin-bottom:8px;background:rgba(255,255,255,0.03)">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                      <div>
                        <input type="text" class="form-input" style="font-size:13px;font-weight:500;width:180px"
                               placeholder="Profilnavn" value="${p.name||''}"
                               data-sp-eid="${p.entity_id}" data-sp-field="name">
                        <div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:2px">${p.entity_id}</div>
                      </div>
                      <button class="sm-btn ghost sm" data-sp-remove="${p.entity_id}">${icon('trash')}</button>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                      <div>
                        <label class="form-label" style="font-size:11px">TTS-tjeneste</label>
                        <select class="form-select" style="font-size:12px"
                                data-sp-eid="${p.entity_id}" data-sp-field="tts_service">
                          ${spServices.map(s => `<option value="${s}" ${p.tts_service===s?'selected':''}>${s}</option>`).join('')}
                        </select>
                      </div>
                      <div>
                        <label class="form-label" style="font-size:11px">Volume: <span data-vol-label="${p.entity_id}">${vol}</span>%</label>
                        <input type="range" class="form-slider" min="0" max="100" step="5"
                               value="${vol}" data-sp-eid="${p.entity_id}" data-sp-field="volume">
                      </div>
                    </div>
                  </div>`;
                }).join('')
            }
          </div>

          <!-- CUSTOM MESSAGES -->
          <div class="form-group">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <label class="form-label" style="margin:0">Brugerdefinerede beskeder</label>
              <button class="sm-btn primary sm" data-action="add-tts-message">${icon('plus')} Add</button>
            </div>

            ${customMessages.length === 0
              ? `<div style="text-align:center;color:var(--sm-text-tertiary);padding:20px;border:1px dashed var(--sm-border);border-radius:8px;font-size:12px">
                   No custom messages yet. Add a message to play when the alarm changes state.
                 </div>`
              : customMessages.map((msg) => {
                  const msgSpeakers = msg.speakers || [];
                  return `<div style="border:1px solid var(--sm-border);border-radius:8px;padding:12px;margin-bottom:8px;background:rgba(255,255,255,0.03)">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                      <input type="text" class="form-input" style="flex:1;margin-right:8px;font-size:13px"
                             placeholder="Beskednavn" value="${msg.name||''}"
                             data-tts-msg-id="${msg.id}" data-tts-msg-field="name">
                      <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin-right:8px;cursor:pointer">
                        <span class="sm-toggle ${msg.enabled?'on':''}" data-tts-msg-toggle="${msg.id}" style="width:32px;height:18px">
                          <div class="dot"></div>
                        </span>
                      </label>
                      <button class="sm-btn ghost sm" data-tts-msg-remove="${msg.id}">${icon('trash')}</button>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
                      <div>
                        <label class="form-label" style="font-size:11px">Udløser</label>
                        <select class="form-select" style="font-size:12px"
                                data-tts-msg-id="${msg.id}" data-tts-msg-field="trigger">
                          ${TRIGGERS.map(t => `<option value="${t.value}" ${msg.trigger===t.value?'selected':''}>${t.label}</option>`).join('')}
                        </select>
                      </div>
                      <div>
                        <label class="form-label" style="font-size:11px">Type</label>
                        <select class="form-select" style="font-size:12px"
                                data-tts-msg-id="${msg.id}" data-tts-msg-field="type">
                          <option value="tts" ${(msg.type||'tts')==='tts'?'selected':''}>TTS (text)</option>
                          <option value="media" ${msg.type==='media'?'selected':''}>Media (MP3/URL)</option>
                        </select>
                      </div>
                    </div>
                    ${(msg.type||'tts')==='tts' ? `
                      <div style="display:flex;gap:6px;margin-bottom:8px">
                        <input type="text" class="form-input" style="flex:1;font-size:12px"
                               placeholder="e.g. Alarmen er aktiveret"
                               value="${msg.message||''}"
                               data-tts-msg-id="${msg.id}" data-tts-msg-field="message">
                        <button class="sm-btn default sm" data-tts-test-msg="${msg.id}" title="Test">${icon('play')}</button>
                      </div>
                    ` : `
                      <div style="margin-bottom:8px">
                        <input type="text" class="form-input" style="font-size:12px;margin-bottom:4px"
                               placeholder="MP3 URL f.eks. /local/alarm.mp3"
                               value="${msg.media_url||''}"
                               data-tts-msg-id="${msg.id}" data-tts-msg-field="media_url">
                      </div>
                    `}
                    <div>
                      <label class="form-label" style="font-size:11px">Speakers (uncheck to exclude)</label>
                      ${speakerCheckboxes(msg.id, msgSpeakers)}
                    </div>
                  </div>`;
                }).join('')
            }
          </div>

          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Annuller</button>
            <button class="btn-dialog save" data-action="save-tts-config">Gem</button>
          </div>
        </div>
      </div>
    `;
  }

  _attachDialogListeners() {
    // Called ONCE per dialog build — never from _attachTabListeners.
    // Prevents listener accumulation on dialog elements.
    const dlg = this.shadowRoot.getElementById('shell-dialog-mount');
    if (!dlg) return;

    const on = (sel, evt, fn) => dlg.querySelectorAll(sel).forEach(el => el.addEventListener(evt, fn));

    // Cancel / close
    on("[data-action='cancel-dialog'], [data-action='close-dialog'], [data-action='close-sched-dialog']",
      "click", () => this._cancelDialog());

    // TTS dialog
    on("[data-action='save-tts-config']",  "click", () => this._saveTTSConfig());
    on("[data-action='add-tts-message']",  "click", () => this._addTTSCustomMessage());
    on("select[data-tts-field], input[data-tts-field]", "change", (e) => {
      this._updateTTSField(e.currentTarget.dataset.ttsField, e.currentTarget.value);
    });
    const ttsCustomInput = dlg.querySelector('#tts-service-custom');
    if (ttsCustomInput) {
      ttsCustomInput.addEventListener("change", () => this._updateTTSCustomService(ttsCustomInput.value));
      ttsCustomInput.addEventListener("blur",   () => this._updateTTSCustomService(ttsCustomInput.value));
    }
    on("input[data-tts-msg-field], select[data-tts-msg-field]", "change", (e) => {
      this._updateTTSCustomMessage(e.currentTarget.dataset.ttsMsgId, e.currentTarget.dataset.ttsMsgField, e.currentTarget.value);
    });
    on("input[data-tts-msg-field]", "input", (e) => {
      this._updateTTSCustomMessage(e.currentTarget.dataset.ttsMsgId, e.currentTarget.dataset.ttsMsgField, e.currentTarget.value);
    });
    on("[data-tts-msg-remove]", "click", (e) => this._removeTTSCustomMessage(e.currentTarget.dataset.ttsMsgRemove));
    on("[data-tts-msg-toggle]", "click", (e) => {
      const id = e.currentTarget.dataset.ttsMsgToggle;
      const msg = this._tempConfig?.custom_messages?.find(m => m.id === id);
      if (msg) { msg.enabled = !msg.enabled; this._rebuildDialog(); }
    });
    on("[data-tts-test-msg]", "click", (e) => {
      const id = e.currentTarget.dataset.ttsTestMsg;
      const msg = this._tempConfig?.custom_messages?.find(m => m.id === id);
      if (msg) this._testTTSMessage(msg.message || '');
    });
    // v1.4.3: Speaker profile listeners
    const spAddSelect = dlg.querySelector('#sp-add-select');
    if (spAddSelect) {
      spAddSelect.addEventListener('change', (e) => {
        if (e.target.value) { this._addSpeakerProfile(e.target.value); e.target.value = ''; }
      });
    }
    on("[data-sp-remove]", "click", (e) => this._removeSpeakerProfile(e.currentTarget.dataset.spRemove));
    on("input[data-sp-field], select[data-sp-field]", "change", (e) => {
      this._updateSpeakerProfile(e.currentTarget.dataset.spEid, e.currentTarget.dataset.spField, e.currentTarget.value);
    });
    on("input[data-sp-field][type='range']", "input", (e) => {
      this._updateSpeakerProfile(e.currentTarget.dataset.spEid, e.currentTarget.dataset.spField, e.currentTarget.value);
    });
    on("input[data-sp-field][type='text']", "input", (e) => {
      this._updateSpeakerProfile(e.currentTarget.dataset.spEid, e.currentTarget.dataset.spField, e.currentTarget.value);
    });
    // Per-message speaker checkboxes
    on("input[data-msg-speaker-id]", "change", (e) => {
      this._updateCustomMessageSpeakers(
        e.currentTarget.dataset.msgSpeakerId,
        e.currentTarget.dataset.msgSpeakerEid,
        e.currentTarget.checked
      );
    });

    // Notification dialog
    on("[data-action='save-notification-dialog']", "click", () => this._saveNotificationDialog());

    const chPush = dlg.querySelector('#notif-ch-push');
    const chTTS  = dlg.querySelector('#notif-ch-tts');
    const svcGroup = dlg.querySelector('#notif-service-group');
    if (chPush) {
      chPush.addEventListener('change', () => {
        const channels = [];
        if (chPush.checked) channels.push('push');
        if (chTTS && chTTS.checked) channels.push('tts');
        if (this._tempConfig) this._tempConfig.channels = channels;
        if (svcGroup) svcGroup.style.display = chPush.checked ? '' : 'none';
      });
    }
    if (chTTS) {
      chTTS.addEventListener('change', () => {
        const channels = [];
        if (chPush && chPush.checked) channels.push('push');
        if (chTTS.checked) channels.push('tts');
        if (this._tempConfig) this._tempConfig.channels = channels;
        const spSection = dlg.querySelector('#notif-tts-speakers');
        if (spSection) spSection.style.display = chTTS.checked ? '' : 'none';
      });
    }
    dlg.querySelectorAll('.notif-tts-sp').forEach(cb => {
      cb.addEventListener('change', () => {
        const allCbs = [...dlg.querySelectorAll('.notif-tts-sp')];
        const checked = allCbs.filter(c => c.checked).map(c => c.dataset.spEid);
        if (this._tempConfig) {
          this._tempConfig.tts_speakers = checked.length === allCbs.length ? [] : checked;
        }
      });
    });
    ['notif-name','notif-trigger','notif-service','notif-message'].forEach(id => {
      const el = dlg.querySelector('#' + id);
      if (!el) return;
      const field = id.replace('notif-', '');
      el.addEventListener('input',  () => { if (this._tempConfig) this._tempConfig[field] = el.value; });
      el.addEventListener('change', () => { if (this._tempConfig) this._tempConfig[field] = el.value; });
    });

    // Scheduled test dialog
    on("[data-action='save-sched-test']", "click", () => this._saveSchedTest());

    // User dialog
    on("[data-action='save-user']", "click", () => this._saveUser());

    // Zone dialog
    on("[data-action='save-zone']", "click", () => this._saveZone());

    // Lights dialog: multi-select picker
    dlg.querySelectorAll('[data-lp-search]').forEach(inp => {
      const pickerId = inp.dataset.lpSearch;
      const list = dlg.querySelector(`[data-lp-list="${pickerId}"]`);
      if (!list) return;
      inp.addEventListener('input', () => {
        const q = inp.value.toLowerCase();
        list.querySelectorAll('[data-lp-row]').forEach(row => {
          row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
      });
    });
    dlg.querySelectorAll('[data-lp-add]').forEach(btn => {
      const pickerId = btn.dataset.lpAdd;
      const list = dlg.querySelector(`[data-lp-list="${pickerId}"]`);
      if (!list) return;
      btn.addEventListener('click', () => {
        const checked = [...list.querySelectorAll('[data-lp-cb]:checked')].map(cb => cb.dataset.entity);
        if (!checked.length) return;
        if (pickerId === 'flash') {
          checked.forEach(eid => { if (!this._tempConfig.entities.includes(eid)) this._tempConfig.entities.push(eid); });
        } else {
          checked.forEach(eid => {
            if (!(this._tempConfig.steady_entities || []).includes(eid))
              this._tempConfig.steady_entities = [...(this._tempConfig.steady_entities || []), eid];
          });
        }
        this._rebuildDialog();
      });
    });
  }

  _attachTabListeners() {
    
    // v1.5.0: Floorplan tab listeners (canvas, upload, drag, picker)
    if (this._activeTab === "floorplan") {
      this._attachFloorplanListeners();
    }

    // Module expansion handlers
    this.shadowRoot.querySelectorAll("[data-module-expand]").forEach(header => {
      header.addEventListener("click", (e) => {
        const moduleKey = header.dataset.moduleExpand;
        const mod = this._data.modules[moduleKey] || {};
        if (!mod.enabled) return;
        // Call the proper init function for each module
        const openers = {
          camera:  () => this._openCameraConfig(),
          lock:    () => this._openLockConfig(),
          lights:  () => this._openLightsConfig(),
          climate: () => this._openClimateConfig(),
          siren:   () => this._openSirenConfig(),
          tts:     () => this._openTTSConfig(),
        };
        if (openers[moduleKey]) openers[moduleKey]();
      });
    });
    
    // Module config save
    this.shadowRoot.querySelectorAll("[data-save-module-config]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const moduleKey = btn.dataset.saveModuleConfig;
        const textarea = this.shadowRoot.getElementById(`module-config-${moduleKey}`);
        
        try {
          const config = JSON.parse(textarea.value);
          const result = await this._callWS("save_module", {
            module_id: moduleKey,
            config: config
          });
          
          if (result && result.success !== false) {
            this._toast(`${MODULE_DEFS[moduleKey].name} configuration saved! Active immediately.`, 'success');
            this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
            await this._loadData();
          } else {
            this._toast(`Kunne ikke gemme: ${result?.error || "Ukendt fejl"}`, 'error');
          }
        } catch (err) {
          this._toast(`JSON error: ${err.message} - Check syntax in text field.`, 'error');
        }
      });
    });
    
    // Module cancel
    this.shadowRoot.querySelectorAll("[data-cancel-module]").forEach(btn => {
      btn.addEventListener("click", () => {
        this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
        this._render();
      });
    });

    const root = this.shadowRoot;

    // Sensor checkboxes
    root.querySelectorAll("[data-sensor]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._toggleSensor(btn.dataset.sensor);
      });
    });

    // Zone toggles
    root.querySelectorAll("[data-zone-toggle]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = btn.dataset.zoneToggle;
        const zone = this._data.zones[id];
        if (zone) {
          zone.enabled = !zone.enabled;
          this._callWS("save_zone", { zone_id: id, config: zone });
          this._render();
        }
      });
    });

    // Module toggles & expand
    root.querySelectorAll("[data-module-toggle]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._toggleModule(btn.dataset.moduleToggle);
      });
    });
    root.querySelectorAll("[data-module-expand]").forEach(el => {
      el.addEventListener("click", () => {
        const key = el.dataset.moduleExpand;
        // Fix F3/F4: Allow opening config even if module is disabled
        this._expandModule(key);
      });
    });

    // Notification/automation toggles
    root.querySelectorAll("[data-edit-notif]").forEach(btn => {
      btn.addEventListener("click", () => this._openNotificationDialog(btn.dataset.editNotif));
    });

    root.querySelectorAll("[data-delete-notif]").forEach(btn => {
      btn.addEventListener("click", () => this._deleteNotification(btn.dataset.deleteNotif));
    });

    // Test buttons
    root.querySelectorAll("[data-test-notif]").forEach(btn => {
      btn.addEventListener("click", () => this._testNotification(btn.dataset.testNotif));
    });
    root.querySelectorAll("[data-test-auto]").forEach(btn => {
      btn.addEventListener("click", () => this._testAutomation(btn.dataset.testAuto));
    });

    // Run test buttons (testing tab)
    root.querySelectorAll("[data-run-test]").forEach(btn => {
      btn.addEventListener("click", () => this._runTest(btn.dataset.runTest));
    });

    // Scheduled test listeners
    root.querySelectorAll("[data-action='add-sched-test']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._schedTemp = {
          name: '', test_type: 'quick', enabled: true, notify_on_fail: true,
          schedule: { mode: 'weekly', weekday: 6, hour: 8, minute: 0 },
        };
        this._showDialog = 'sched-test';
        this._render();
      });
    });

    root.querySelectorAll("[data-edit-sched]").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.editSched;
        const existing = this._data.scheduledTests[id] || {};
        this._schedTemp = { ...existing, _id: id };
        this._showDialog = 'sched-test';
        this._render();
      });
    });

    root.querySelectorAll("[data-delete-sched]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.deleteSched;
        const name = this._data.scheduledTests[id]?.name || 'this schedule';
        if (!await this._confirm('Fjern "' + name + '"?', 'Slet tidsplan')) return;
        await this._callWS('delete_scheduled_test', { test_id: id });
        await this._loadTestingData();
        this._render();
        this._toast('Tidsplan fjernet', 'success');
      });
    });

    root.querySelectorAll("[data-run-sched]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.runSched;
        const name = this._data.scheduledTests[id]?.name || 'test';
        this._toast('Kører "' + name + '"...', 'info');
        const result = await this._callWS('run_scheduled_test_now', { test_id: id });
        await this._loadTestingData();
        this._render();
        const overall = result?.result?.overall || 'unknown';
        this._toast('"' + name + '" completed: ' + overall.toUpperCase(), overall === 'pass' ? 'success' : 'error');
      });
    });

    root.querySelectorAll("[data-action='close-sched-dialog']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._showDialog = null;
        this._schedTemp = null;
        this._render();
      });
    });

    root.querySelectorAll("[data-action='save-sched-test']").forEach(btn => {
      btn.addEventListener("click", () => this._saveSchedTest());
    });

    root.querySelectorAll("[data-action='toggle-test-desc']").forEach(el => {
      el.addEventListener("click", () => {
        this._testDescExpanded = !this._testDescExpanded;
        this._render();
      });
    });

    // Collapsible sections
    root.querySelectorAll("[data-action='toggle-sensor-status-hidden']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._sensorStatusExpanded = !this._sensorStatusExpanded;
        this._render();
      });
    });

    root.querySelectorAll("[data-action='toggle-test-history']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._testHistoryExpanded = !this._testHistoryExpanded;
        this._render();
      });
    });

    root.querySelectorAll("[data-action='toggle-battery-ok']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._batteryOkExpanded = !this._batteryOkExpanded;
        this._render();
      });
    });
    root.querySelectorAll("[data-action='toggle-sensors-inactive']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._sensorsInactiveExpanded = !this._sensorsInactiveExpanded;
        this._render();
      });
    });

    // Allow Open toggle
    root.querySelectorAll("[data-allow-open]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const eid = btn.dataset.allowOpen;
        const s = this._data.sensors.find(s => s.entity_id === eid);
        if (!s) return;
        s.allow_open = !s.allow_open;
        // Gem alle aktiverede sensorer med allow_open state
        const bulk = {};
        for (const sensor of this._data.sensors) {
          if (sensor.enabled) {
            bulk[sensor.entity_id] = {
              enabled: true,
              sensor_type: sensor.sensor_type,
              entry_delay: sensor.entry_delay !== undefined ? sensor.entry_delay : null,
              auto_bypass: !!sensor.auto_bypass,
              auto_bypass_modes: Array.isArray(sensor.auto_bypass_modes) ? sensor.auto_bypass_modes : [],
              arm_on_close: !!sensor.arm_on_close,
              allow_open: !!sensor.allow_open,
            };
          }
        }
        await this._callWS("save_sensors", { sensors: bulk });
        this._render();
      });
    });

    // Environmental sensors section toggle
    root.querySelectorAll("[data-action='toggle-env-sensors']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._envExpanded = !this._envExpanded;
        this._render();
      });
    });

    // Hidden sensors section toggle
    root.querySelectorAll("[data-action='toggle-hidden-sensors']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._hiddenSensorsExpanded = !this._hiddenSensorsExpanded;
        this._render();
      });
    });

    // Hide sensor (mark as excluded)
    root.querySelectorAll("[data-hide-sensor]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const entityId = btn.dataset.hideSensor;
        if (!await this._confirm(
          'Denne sensor vil blive skjult fra panelet. Du kan gendanne den ved at redigere Secure Me-konfigurationen.',
          'Skjul sensor?'
        )) return;
        await this._callWS('hide_sensor', { entity_id: entityId, hidden: true });
        this._toast('Sensor skjult', 'success');
        await this._loadData();
      });
    });

    // Unmark environmental sensor (remove mis-classification)
    root.querySelectorAll("[data-unmark-env]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const entityId = btn.dataset.unmarkEnv;
        if (!await this._confirm(
          'Dette vil fjerne miljøklassificeringen og skjule sensoren. Den vil ikke længere udløse alarmnotifikationer.',
          'Fjern miljøsensor?'
        )) return;
        await this._callWS('unmark_environmental', { entity_id: entityId });
        this._toast('Miljøsensor fjernet', 'success');
        await this._loadData();
      });
    });


    // Fake Presence toggle (legacy Sensors tab)
    root.querySelectorAll("[data-action='toggle-fake-presence']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const current = this._data.fakePresence || false;
        const next = !current;
        this._data.fakePresence = next;
        // Toggle the actual clicked element directly so the CSS slide
        // animation (.sm-toggle .dot { transition: left 0.2s }) plays.
        // A full _render() replaces this button's innerHTML immediately,
        // which would destroy/recreate it mid-transition with no "before"
        // state to animate from, so we hold off the full render briefly.
        btn.classList.toggle('on', next);
        const [result] = await Promise.all([
          this._callWS('set_fake_presence', { active: next }),
          new Promise(r => setTimeout(r, 220)),  // let the 0.2s transition finish
        ]);
        if (result && result.active !== undefined) {
          this._data.fakePresence = result.active;
        } else {
          this._toast('Kunne ikke opdatere Fake Presence', 'error');
          this._data.fakePresence = current;  // revert
        }
        this._render();
      });
    });

    // Special Features: Auto Actions toggle buttons
    root.querySelectorAll("[data-aa-toggle]").forEach(btn => {
      btn.addEventListener("click", () => {
        const field = btn.dataset.aaToggle;
        if (!this._data.autoActions) this._data.autoActions = {};
        this._data.autoActions[field] = !this._data.autoActions[field];
        this._render();
      });
    });

    // Special Features: Auto Actions range sliders (live update label)
    root.querySelectorAll("[data-aa-range]").forEach(inp => {
      inp.addEventListener("input", () => {
        const field = inp.dataset.aaRange;
        if (!this._data.autoActions) this._data.autoActions = {};
        this._data.autoActions[field] = parseInt(inp.value);
        // Re-render to update the delay label without losing slider position
        this._render();
      });
    });

    // Special Features: Save Auto Actions
    root.querySelectorAll("[data-action='save-auto-actions']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const result = await this._callWS('save_auto_actions', { config: this._data.autoActions || {} });
        if (result && result.success) {
          this._toast('Auto-handlinger gemt', 'success');
        } else {
          this._toast('Kunne ikke gemme', 'error');
        }
      });
    });

    // Special Features: Fake Presence v2 toggle buttons
    root.querySelectorAll("[data-fp-toggle]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const field = btn.dataset.fpToggle;
        if (!this._data.fakePresenceV2) this._data.fakePresenceV2 = {};
        const next = !this._data.fakePresenceV2[field];
        this._data.fakePresenceV2[field] = next;
        // Toggle the clicked element directly so the CSS slide animation
        // plays. A full _render() destroys/recreates this button via
        // innerHTML, which would skip the transition entirely, so the
        // reconciling render is deferred until the animation has time to run.
        btn.classList.toggle('on', next);
        if (field === 'active') {
          const [result] = await Promise.all([
            this._callWS('save_fake_presence_v2', { config: this._data.fakePresenceV2 }),
            new Promise(r => setTimeout(r, 220)),
          ]);
          if (result && result.success) {
            // Keep legacy fakePresence bool in sync for Sensors tab badge
            this._data.fakePresence = this._data.fakePresenceV2.active || false;
          } else {
            this._toast('Kunne ikke opdatere Fake Presence', 'error');
            // Revert
            this._data.fakePresenceV2[field] = !next;
          }
          this._render();
        } else {
          setTimeout(() => this._render(), 220);
        }
      });
    });

    // Special Features: Save Fake Presence v2
    root.querySelectorAll("[data-action='save-fake-presence-v2']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const result = await this._callWS('save_fake_presence_v2', { config: this._data.fakePresenceV2 || {} });
        if (result && result.success) {
          this._data.fakePresence = (this._data.fakePresenceV2 || {}).active || false;
          this._toast('Fake Presence gemt', 'success');
        } else {
          this._toast('Kunne ikke gemme', 'error');
        }
      });
    });

    // Zone actions
    root.querySelectorAll("[data-action='add-zone']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._tempConfig = { type: 'entry', arm_modes: ['away'], sensors: [], home_alone_sensor_config: {} };
        this._showDialog = 'zone';
        // Pre-load cameras and media_players for Home Alone config dropdowns
        if (!this._availableEntities.camera) this._loadEntitiesByDomain('camera');
        if (!this._availableEntities.media_player) this._loadEntitiesByDomain('media_player');
        this._render();
      });
    });
    root.querySelectorAll("[data-edit-zone]").forEach(btn => {
      btn.addEventListener("click", () => this._editZone(btn.dataset.editZone));
    });
    root.querySelectorAll("[data-delete-zone]").forEach(btn => {
      btn.addEventListener("click", () => this._deleteZone(btn.dataset.deleteZone));
    });

    // User actions
    root.querySelectorAll("[data-action='add-user']").forEach(btn => {
      btn.addEventListener("click", async () => {
        this._tempConfig = {
          admin: false,
          notification_settings: {
            notify_service: '',
            receive_critical: true,
            receive_alerts: true,
            receive_own_actions: true,
            tts_quiet_start: null,
            tts_quiet_end: null,
          }
        };
        this._showDialog = 'user';
        if (!this._availablePersons) {
          try {
            const result = await this._callWS('get_persons');
            this._availablePersons = result?.persons || [];
          } catch(e) { this._availablePersons = []; }
        }
        await this._loadNotifyServices();
        this._render();
      });
    });
    root.querySelectorAll("[data-edit-user]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const userId = btn.dataset.editUser;
        const existing = this._data.users[userId] || {};
        this._tempConfig = {
          _userId: userId,
          name: existing.name || '',
          admin: existing.admin || false,
          nfc_tag: existing.nfc_tag || null,
          person_entity: existing.person_entity || null,
          notification_settings: {
            notify_service:      existing.notify_service      ?? '',
            receive_critical:    existing.receive_critical    !== false,
            receive_alerts:      existing.receive_alerts      !== false,
            receive_own_actions: existing.receive_own_actions !== false,
            tts_quiet_start:     existing.tts_quiet_start     ?? '',
            tts_quiet_end:       existing.tts_quiet_end       ?? '',
          },
        };
        this._showDialog = 'user';
        if (!this._availablePersons) {
          try {
            const result = await this._callWS('get_persons');
            this._availablePersons = result?.persons || [];
          } catch(e) { this._availablePersons = []; }
        }
        await this._loadNotifyServices();
        this._render();
      });
    });
    root.querySelectorAll("[data-delete-user]").forEach(btn => {
      btn.addEventListener("click", () => this._deleteUser(btn.dataset.deleteUser));
    });

    // Still placeholder actions
    root.querySelectorAll("[data-action='import-nfc'], [data-action='add-notification'], [data-action='add-automation']").forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        switch(action) {
          case "import-nfc":
            this._toast("Importér NFC-tags - kommer snart.", "info");
            break;
          case "add-notification":
            this._openNotificationDialog();
            break;
          case "add-automation":
            this._toast("Tilføj automatisering - kommer snart.", "info");
            break;
        }
      });
    });
    // Open camera config dialog
    const cameraConfigButtons = root.querySelectorAll("[data-action='open-camera-config']");
    cameraConfigButtons.forEach(btn => {
      btn.addEventListener("click", () => this._openCameraConfig());
    });
    
    // Close/cancel dialog
    root.querySelectorAll("[data-action='close-dialog'], [data-action='cancel-dialog']").forEach(btn => {
      btn.addEventListener("click", () => this._cancelDialog());
    });
    
    // Add camera button
    root.querySelectorAll("[data-action='add-camera']").forEach(btn => {
      btn.addEventListener("click", () => this._addCameraRow());
    });
    
    // Remove camera buttons
    root.querySelectorAll("[data-action='remove-camera']").forEach(btn => {
      btn.addEventListener("click", () => {
        const cameraId = parseInt(btn.dataset.cameraId);
        this._removeCameraRow(cameraId);
      });
    });
    
    // Save camera config
    root.querySelectorAll("[data-action='save-camera-config']").forEach(btn => {
      btn.addEventListener("click", () => this._saveCameraConfig());
    });
    
    // Camera field selects (entity_id, poe_port)
    root.querySelectorAll(".form-select[data-camera-id]").forEach(select => {
      select.addEventListener("change", () => {
        const cameraId = parseInt(select.dataset.cameraId);
        const field = select.dataset.field;
        this._updateCameraField(cameraId, field, select.value);
      });
    });
    
    // Radio options for recording mode
    root.querySelectorAll(".radio-option[data-camera-id]").forEach(option => {
      option.addEventListener("click", () => {
        const cameraId = parseInt(option.dataset.cameraId);
        const field = option.dataset.field;
        const value = option.dataset.value;
        this._updateCameraField(cameraId, field, value);
        // Update selected state
        const groupName = `mode-${cameraId}`;
        root.querySelectorAll(`.radio-option[data-camera-id="${cameraId}"]`).forEach(opt => {
          opt.classList.remove('selected');
        });
        option.classList.add('selected');
        // Update radio input
        const radio = option.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
      });
    });
    
    // Entity search functionality
    root.querySelectorAll(".entity-search[data-search-target]").forEach(input => {
      input.addEventListener("keyup", () => {
        const targetId = input.dataset.searchTarget;
        const select = root.querySelector(`#${targetId}`);
        if (!select) return;
        
        const filter = input.value.toLowerCase();
        const options = select.querySelectorAll('option');
        
        options.forEach(option => {
          if (option.value === '') {
            option.style.display = '';
            return;
          }
          const text = option.textContent.toLowerCase();
          option.style.display = text.includes(filter) ? '' : 'none';
        });
      });
    });

    
    // === Lock Module Handlers ===
    root.querySelectorAll("[data-action='open-lock-config']").forEach(b => b.addEventListener("click", () => this._openLockConfig()));
    root.querySelectorAll("[data-action='add-lock']").forEach(b => b.addEventListener("click", () => this._addLockRow()));
    root.querySelectorAll("[data-action='save-lock-config']").forEach(b => b.addEventListener("click", () => this._saveLockConfig()));
    root.querySelectorAll("[data-action='remove-lock']").forEach(b => b.addEventListener("click", () => this._removeLockRow(parseInt(b.dataset.lockId))));

    // Lock entity select
    root.querySelectorAll("select[data-lock-id][data-field='entity_id']").forEach(sel => {
      sel.addEventListener("change", () => this._updateLockField(parseInt(sel.dataset.lockId), 'entity_id', sel.value));
    });
    // Lock number inputs
    root.querySelectorAll("input[type='number'][data-lock-id]").forEach(inp => {
      inp.addEventListener("change", () => this._updateLockField(parseInt(inp.dataset.lockId), inp.dataset.field, inp.value));
    });
    // Lock checkboxes
    root.querySelectorAll("input[type='checkbox'][data-lock-id]").forEach(cb => {
      cb.addEventListener("change", () => this._updateLockField(parseInt(cb.dataset.lockId), cb.dataset.field, cb.checked));
    });
    // Lock search: filter select options live
    root.querySelectorAll("input[data-lock-search]").forEach(inp => {
      inp.addEventListener("input", () => {
        const lockId = inp.dataset.lockSearch;
        const search = inp.value.toLowerCase();
        const allEntities = this._allEntities || [];
        const domainEntities = this._availableEntities.lock || [];
        const sel = root.querySelector(`select[data-lock-id='${lockId}'][data-field='entity_id']`);
        if (!sel) return;
        const filtered = search.length > 1
          ? allEntities.filter(e => e.name.toLowerCase().includes(search) || e.entity_id.toLowerCase().includes(search)).slice(0, 25)
          : domainEntities;
        const currentVal = sel.value;
        sel.innerHTML = '<option value="">-- Vælg entitet --</option>' +
          filtered.map(e => `<option value="${e.entity_id}" ${e.entity_id === currentVal ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('') +
          (!filtered.find(e => e.entity_id === currentVal) && currentVal ? `<option value="${currentVal}" selected>${currentVal}</option>` : '');
      });
    });

    // === Climate Module Handlers ===
    root.querySelectorAll("[data-action='open-climate-config']").forEach(b => b.addEventListener("click", () => this._openClimateConfig()));
    root.querySelectorAll("[data-action='add-climate']").forEach(b => b.addEventListener("click", () => this._addClimateRow()));
    root.querySelectorAll("[data-action='save-climate-config']").forEach(b => b.addEventListener("click", () => this._saveClimateConfig()));
    root.querySelectorAll("[data-action='remove-climate']").forEach(b => b.addEventListener("click", () => this._removeClimateRow(parseInt(b.dataset.climateId))));

    // Climate selects (entity + mode dropdowns)
    root.querySelectorAll("select[data-climate-id]").forEach(sel => {
      sel.addEventListener("change", () => this._updateClimateField(parseInt(sel.dataset.climateId), sel.dataset.field, sel.value));
    });
    // Climate number inputs
    root.querySelectorAll("input[type='number'][data-climate-id]").forEach(inp => {
      inp.addEventListener("change", () => this._updateClimateField(parseInt(inp.dataset.climateId), inp.dataset.field, inp.value));
    });
    // Climate search: filter select options live
    root.querySelectorAll("input[data-climate-search]").forEach(inp => {
      inp.addEventListener("input", () => {
        const climateId = inp.dataset.climateSearch;
        const search = inp.value.toLowerCase();
        const allEntities = this._allEntities || [];
        const domainEntities = this._availableEntities.climate || [];
        const sel = root.querySelector(`select[data-climate-id='${climateId}'][data-field='entity_id']`);
        if (!sel) return;
        const filtered = search.length > 1
          ? allEntities.filter(e => e.name.toLowerCase().includes(search) || e.entity_id.toLowerCase().includes(search)).slice(0, 25)
          : domainEntities;
        const currentVal = sel.value;
        sel.innerHTML = '<option value="">-- Vælg entitet --</option>' +
          filtered.map(e => `<option value="${e.entity_id}" ${e.entity_id === currentVal ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('') +
          (!filtered.find(e => e.entity_id === currentVal) && currentVal ? `<option value="${currentVal}" selected>${currentVal}</option>` : '');
      });
    });

    // === Siren Module Handlers ===
    root.querySelectorAll("[data-action='open-siren-config']").forEach(b => b.addEventListener("click", () => this._openSirenConfig()));
    root.querySelectorAll("[data-action='add-siren']").forEach(b => b.addEventListener("click", () => this._addSirenRow()));
    root.querySelectorAll("[data-action='save-siren-config']").forEach(b => b.addEventListener("click", () => this._saveSirenConfig()));
    root.querySelectorAll("[data-action='quick-test-siren']").forEach(b => b.addEventListener("click", () => this._quickTestSiren()));
    root.querySelectorAll("[data-action='remove-siren']").forEach(b => b.addEventListener("click", () => this._removeSirenRow(parseInt(b.dataset.sirenId))));
    root.querySelectorAll("select[data-siren-id], input[data-siren-id]").forEach(inp => {
      inp.addEventListener("change", () => this._updateSirenField(parseInt(inp.dataset.sirenId), inp.dataset.field, inp.value));
    });

    // === Lights Module Handlers ===
    root.querySelectorAll("[data-action='open-lights-config']").forEach(b => b.addEventListener("click", () => this._openLightsConfig()));
    root.querySelectorAll("[data-action='save-lights-config']").forEach(b => b.addEventListener("click", () => this._saveLightsConfig()));
    root.querySelectorAll("[data-action='quick-test-lights']").forEach(b => b.addEventListener("click", () => this._quickTestLights()));
    root.querySelectorAll("[data-action='remove-light']").forEach(b => b.addEventListener("click", () => this._removeLightEntity(b.dataset.entity)));
    root.querySelectorAll("[data-action='remove-steady-light']").forEach(b => b.addEventListener("click", () => {
      this._tempConfig.steady_entities = (this._tempConfig.steady_entities || []).filter(e => e !== b.dataset.entity);
      this._rebuildDialog();
    }));

    // Lights field selects and checkboxes
    root.querySelectorAll("select[data-lights-field]").forEach(sel => {
      sel.addEventListener("change", () => this._updateLightsField(sel.dataset.lightsField, sel.value));
    });
    root.querySelectorAll("input[type='number'][data-lights-field]").forEach(inp => {
      inp.addEventListener("change", () => this._updateLightsField(inp.dataset.lightsField, inp.value));
    });
    root.querySelectorAll("input[type='checkbox'][data-lights-field]").forEach(cb => {
      cb.addEventListener("change", () => { this._updateLightsField(cb.dataset.lightsField, cb.checked); this._render(); });
    });

    // === TTS Module Handlers (tab-level only — dialog listeners in _attachDialogListeners) ===
    root.querySelectorAll("[data-action='open-tts-config']").forEach(b => b.addEventListener("click", () => this._openTTSConfig()));

    // Segment control
    root.querySelectorAll("[data-auto-section]").forEach(btn => {
      btn.addEventListener("click", () => this._setAutoSection(btn.dataset.autoSection));
    });
  }
}

// === Register Custom Element ===
// Guard prevents "name already used" error when HA re-executes JS on panel re-entry
if (!customElements.get("secure-me-panel")) {
  customElements.define("secure-me-panel", SecureMePanel);
}