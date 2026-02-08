/**
 * Secure Me - Configuration Panel
 * VERSION: 0.3.0-alpha (Camera GUI Config)
 *
 * Custom panel for Home Assistant using vanilla Custom Elements.
 * Uses HA CSS custom properties for theme compatibility.
 * Communicates with backend via WebSocket API.
 */

const DOMAIN = "secure_me";
const VERSION = "0.3.0-alpha";

// === Styles ===
const panelStyles = `
  :host {
    --sm-accent: #34c759;
    --sm-accent-dim: rgba(52,199,89,0.12);
    --sm-accent-glow: rgba(52,199,89,0.3);
    --sm-danger: #ff453a;
    --sm-danger-dim: rgba(255,69,58,0.12);
    --sm-warning: #ff9f0a;
    --sm-warning-dim: rgba(255,159,10,0.12);
    --sm-blue: #0a84ff;
    --sm-blue-dim: rgba(10,132,255,0.12);
    --sm-purple: #bf5af2;
    --sm-purple-dim: rgba(191,90,242,0.12);
    --sm-teal: #64d2ff;
    --sm-teal-dim: rgba(100,210,255,0.12);

    /* Use HA variables with fallbacks */
    --sm-bg: var(--primary-background-color, #1c1c1e);
    --sm-surface: var(--card-background-color, #2c2c2e);
    --sm-border: var(--divider-color, rgba(255,255,255,0.06));
    --sm-text: var(--primary-text-color, #f5f5f7);
    --sm-text-secondary: var(--secondary-text-color, rgba(255,255,255,0.55));
    --sm-text-tertiary: var(--disabled-text-color, rgba(255,255,255,0.35));

    display: flex;
    font-family: var(--paper-font-body1_-_font-family, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif);
    background: var(--sm-bg);
    color: var(--sm-text);
    height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  /* === Sidebar === */
  .sidebar {
    width: 220px;
    min-height: 100vh;
    background: var(--sm-surface);
    border-right: 1px solid var(--sm-border);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    overflow-y: auto;
  }
  .sidebar-header {
    padding: 20px 20px 16px;
    border-bottom: 1px solid var(--sm-border);
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .sidebar-logo {
    width: 36px; height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--sm-accent), var(--sm-blue));
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 12px var(--sm-accent-glow);
  }
  .sidebar-logo svg { width: 20px; height: 20px; color: #fff; }
  .sidebar-title { font-size: 15px; font-weight: 700; }
  .sidebar-version { font-size: 11px; color: var(--sm-text-tertiary); }

  .sidebar-status {
    padding: 12px 16px;
    border-bottom: 1px solid var(--sm-border);
  }
  .status-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; border-radius: 10px;
    font-size: 12px; font-weight: 600;
  }
  .status-pill.disarmed { background: var(--sm-accent-dim); color: var(--sm-accent); }
  .status-pill.armed { background: var(--sm-danger-dim); color: var(--sm-danger); }
  .status-pill.arming { background: var(--sm-warning-dim); color: var(--sm-warning); }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 8px currentColor;
  }

  /* === Nav Tabs === */
  .nav-tabs {
    padding: 8px 10px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .nav-tab {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border-radius: 10px;
    border: none; cursor: pointer;
    background: transparent;
    color: var(--sm-text-secondary);
    font-size: 13px; font-weight: 400;
    font-family: inherit;
    text-align: left; width: 100%;
    transition: background 0.15s ease;
  }
  .nav-tab:hover { background: rgba(255,255,255,0.04); }
  .nav-tab.active {
    background: rgba(255,255,255,0.1);
    color: var(--sm-text);
    font-weight: 600;
  }
  .nav-tab svg { width: 18px; height: 18px; opacity: 0.6; }
  .nav-tab.active svg { opacity: 1; }
  .nav-tab .badge-soon {
    margin-left: auto; font-size: 9px;
    padding: 1px 5px; border-radius: 4px;
    background: rgba(255,255,255,0.08);
    color: var(--sm-text-tertiary);
  }

  .sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid var(--sm-border);
    font-size: 11px;
    color: var(--sm-text-tertiary);
  }

  /* === Main Content === */
  .main-content {
    flex: 1;
    padding: 28px 32px;
    overflow-y: auto;
    max-width: 740px;
    overscroll-behavior: contain;
    scroll-behavior: smooth;
  }

  /* === Cards === */
  .sm-card {
    background: var(--sm-surface);
    border-radius: 16px;
    border: 1px solid var(--sm-border);
    padding: 20px;
    margin-bottom: 12px;
  }
  .sm-card.no-pad { padding: 0; }

  /* === Table === */
  .sm-list-header {
    display: grid; gap: 0; align-items: center;
    padding: 10px 16px;
    background: rgba(255,255,255,0.03);
    border-bottom: 1px solid var(--sm-border);
    font-size: 11px; font-weight: 600;
    color: var(--sm-text-tertiary);
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .sm-list-row {
    display: grid; gap: 12px; align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--sm-border);
    transition: opacity 0.2s ease;
  }
  .sm-list-row:last-child { border-bottom: none; }
  .sm-list-row.disabled { opacity: 0.45; }

  /* === Badges === */
  .badge {
    display: inline-block;
    padding: 2px 8px; border-radius: 6px;
    font-size: 11px; font-weight: 600;
    letter-spacing: 0.02em;
  }
  .badge.contact { color: var(--sm-blue); background: var(--sm-blue-dim); }
  .badge.motion { color: var(--sm-purple); background: var(--sm-purple-dim); }
  .badge.presence { color: var(--sm-teal); background: var(--sm-teal-dim); }
  .badge.entry { color: var(--sm-warning); background: var(--sm-warning-dim); }
  .badge.interior { color: var(--sm-blue); background: var(--sm-blue-dim); }
  .badge.perimeter { color: var(--sm-danger); background: var(--sm-danger-dim); }
  .badge.instant { color: var(--sm-purple); background: var(--sm-purple-dim); }
  .badge.accent { color: var(--sm-accent); background: var(--sm-accent-dim); }
  .badge.actions { color: var(--sm-purple); background: var(--sm-purple-dim); }

  /* === Checkbox === */
  .sm-checkbox {
    width: 20px; height: 20px; border-radius: 6px;
    border: 2px solid var(--sm-text-tertiary);
    background: transparent;
    cursor: pointer; display: flex;
    align-items: center; justify-content: center;
    transition: all 0.15s ease; padding: 0;
    flex-shrink: 0;
  }
  .sm-checkbox.checked {
    border: none;
    background: var(--sm-accent);
  }
  .sm-checkbox svg { width: 14px; height: 14px; color: #fff; }

  /* === Toggle === */
  .sm-toggle {
    width: 44px; height: 24px; border-radius: 24px;
    background: rgba(255,255,255,0.15);
    cursor: pointer; position: relative;
    transition: background 0.2s ease;
    flex-shrink: 0; border: none; padding: 0;
  }
  .sm-toggle.on { background: var(--sm-accent); }
  .sm-toggle .dot {
    width: 18px; height: 18px; border-radius: 50%;
    background: #fff; position: absolute; top: 3px;
    left: 3px; transition: left 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  }
  .sm-toggle.on .dot { left: 23px; }

  /* === Buttons === */
  .sm-btn {
    border: none; border-radius: 10px;
    padding: 8px 16px; font-size: 13px;
    cursor: pointer; display: inline-flex;
    align-items: center; gap: 6px;
    transition: all 0.15s ease;
    font-family: inherit;
  }
  .sm-btn.sm { padding: 6px 12px; font-size: 12px; }
  .sm-btn.primary { background: var(--sm-accent); color: #000; font-weight: 600; }
  .sm-btn.default { background: rgba(255,255,255,0.08); color: var(--sm-text); }
  .sm-btn.danger { background: var(--sm-danger-dim); color: var(--sm-danger); }
  .sm-btn.ghost { background: transparent; color: var(--sm-text-secondary); }
  .sm-btn:hover { filter: brightness(1.1); }
  .sm-btn svg { width: 14px; height: 14px; }

  /* === Inputs === */
  .sm-input, .sm-select {
    width: 100%; padding: 8px 12px; border-radius: 8px;
    background: rgba(255,255,255,0.08); color: var(--sm-text);
    border: 1px solid var(--sm-border); font-size: 13px;
    font-family: inherit; box-sizing: border-box;
  }
  .sm-select { appearance: auto; }
  .sm-label {
    font-size: 11px; color: var(--sm-text-secondary);
    display: block; margin-bottom: 4px;
  }

  /* === Section === */
  .section-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 16px;
  }
  .section-title {
    font-size: 16px; font-weight: 600;
    color: var(--sm-text); margin: 0;
  }
  .section-subtitle {
    font-size: 13px; color: var(--sm-text-secondary);
    margin: 4px 0 0;
  }

  /* === Info === */
  .info-card {
    padding: 14px 16px; border-radius: 12px;
    display: flex; gap: 12px; align-items: flex-start;
    margin-bottom: 12px;
  }
  .info-card.warning { background: var(--sm-warning-dim); border: 1px solid rgba(255,159,10,0.2); }
  .info-card.info { background: var(--sm-blue-dim); border: 1px solid rgba(10,132,255,0.2); }
  .info-card .info-title { font-size: 13px; font-weight: 600; }
  .info-card .info-text { font-size: 12px; color: var(--sm-text-secondary); margin-top: 4px; }

  /* === Zone === */
  .zone-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .zone-card { cursor: pointer; }
  .zone-modes { display: flex; gap: 4px; margin-top: 8px; }
  .zone-mode {
    padding: 2px 6px; border-radius: 4px; font-size: 10px;
    background: rgba(255,255,255,0.08); color: var(--sm-text-secondary);
  }

  /* === User === */
  .user-avatar {
    width: 40px; height: 40px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 16px; flex-shrink: 0;
  }
  .nfc-tag {
    padding: 8px 12px; border-radius: 8px;
    display: flex; align-items: center; gap: 8px;
    border: 1px solid rgba(191,90,242,0.15);
    background: var(--sm-purple-dim);
    margin-top: 12px;
  }
  .nfc-tag-id { font-size: 12px; color: var(--sm-purple); font-family: monospace; }

  /* === Module === */
  .module-header {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px; cursor: pointer;
    transition: opacity 0.2s ease;
  }
  .module-header.disabled { opacity: 0.45; cursor: default; }
  .module-icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s ease;
  }
  .module-config {
    padding: 0 16px 16px;
    border-top: 1px solid var(--sm-border);
    padding-top: 16px;
  }
  .module-entity-row {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--sm-border);
  }

  /* === Segmented === */
  .segment-control {
    display: flex; background: rgba(255,255,255,0.05);
    border-radius: 10px; padding: 3px;
    margin-bottom: 16px;
  }
  .segment-btn {
    flex: 1; padding: 8px 12px; border-radius: 8px;
    border: none; background: transparent;
    color: var(--sm-text-secondary);
    font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.2s ease;
    font-family: inherit;
  }
  .segment-btn.active {
    background: var(--sm-surface);
    color: var(--sm-text);
  }

  /* === Notification Automation === */
  .notif-message {
    font-size: 12px; color: var(--sm-text-secondary);
    margin-top: 6px; padding: 6px 10px; border-radius: 6px;
    background: rgba(255,255,255,0.04);
    font-family: monospace;
  }
  .notif-actions { display: flex; gap: 8px; margin-top: 12px; }

  /* === Placeholder === */
  .placeholder {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 20px; text-align: center;
  }
  .placeholder-icon {
    width: 64px; height: 64px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; margin-bottom: 16px;
  }
  .placeholder h3 { margin: 0; font-size: 18px; font-weight: 600; }
  .placeholder p {
    color: var(--sm-text-secondary); font-size: 14px;
    max-width: 320px; margin-top: 8px;
  }

  /* === Narrow === */
  :host([narrow]) .sidebar { width: 56px; }
  :host([narrow]) .sidebar-header span,
  :host([narrow]) .sidebar-status,
  :host([narrow]) .nav-tab span:not(.nav-icon),
  :host([narrow]) .nav-tab .badge-soon,
  :host([narrow]) .sidebar-footer { display: none; }
  :host([narrow]) .nav-tab { justify-content: center; padding: 12px; }
  :host([narrow]) .main-content { padding: 16px; }
  :host([narrow]) .zone-grid { grid-template-columns: 1fr; }

  /* Mobile Responsive */
  @media (max-width: 768px) {
    :host {
      flex-direction: column;
    }
    .sidebar {
      width: 100%;
      min-height: auto;
      border-right: none;
      border-bottom: 1px solid var(--sm-border);
      max-height: 200px;
      overflow-y: auto;
    }
    .nav-tabs {
      flex-direction: row;
      overflow-x: auto;
      padding: 8px;
      gap: 4px;
    }
    .nav-tab {
      min-width: 90px;
      padding: 8px 10px;
      justify-content: center;
    }
    .main-content {
      padding: 16px;
      max-width: 100%;
    }
  }
  
  @media (max-width: 480px) {
    .main-content {
      padding: 12px;
    }
    .sm-card {
      padding: 12px;
      margin-bottom: 8px;
    }
  }



  /* === Dialog System === */
  .config-dialog-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    backdrop-filter: blur(4px);
    animation: fadeIn 0.2s ease;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .config-dialog {
    max-width: 650px;
    max-height: 90vh;
    width: 90%;
    background: var(--sm-surface);
    border-radius: 16px;
    border: 1px solid var(--sm-border);
    padding: 24px;
    overflow-y: auto;
    animation: slideUp 0.3s ease;
  }
  
  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  
  .dialog-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--sm-border);
  }
  
  .dialog-title {
    font-size: 20px;
    font-weight: 700;
    flex: 1;
  }
  
  .dialog-close {
    background: rgba(255,255,255,0.08);
    border: none;
    border-radius: 8px;
    width: 32px;
    height: 32px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--sm-text-secondary);
    transition: all 0.2s;
  }
  
  .dialog-close:hover {
    background: rgba(255,255,255,0.12);
  }
  
  .item-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .item-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--sm-border);
    border-radius: 12px;
    padding: 16px;
  }
  
  .item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  
  .item-number {
    font-size: 16px;
    font-weight: 600;
    color: var(--sm-text);
  }
  
  .form-group {
    margin-bottom: 16px;
  }
  
  .form-group:last-child {
    margin-bottom: 0;
  }
  
  .form-label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 6px;
    color: var(--sm-text-secondary);
  }
  
  .form-label .optional-hint {
    font-size: 12px;
    color: var(--sm-text-tertiary);
    font-style: italic;
    font-weight: 400;
  }
  
  .form-select, .form-input {
    width: 100%;
    padding: 10px 12px;
    background: rgba(255,255,255,0.08);
    border: 1px solid var(--sm-border);
    border-radius: 8px;
    color: var(--sm-text);
    font-size: 14px;
    font-family: inherit;
    box-sizing: border-box;
  }
  
  .form-select {
    cursor: pointer;
  }
  
  .form-select:focus, .form-input:focus {
    outline: none;
    border-color: var(--sm-accent);
    background: rgba(255,255,255,0.1);
  }
  
  .entity-search {
    width: 100%;
    padding: 8px 12px;
    background: rgba(255,255,255,0.08);
    border: 1px solid var(--sm-border);
    border-radius: 8px;
    color: var(--sm-text);
    font-size: 14px;
    margin-bottom: 8px;
    box-sizing: border-box;
  }
  
  .entity-search:focus {
    outline: none;
    border-color: var(--sm-accent);
  }
  
  .entity-search::placeholder {
    color: var(--sm-text-tertiary);
  }
  
  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .radio-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    border: 1px solid transparent;
  }
  
  .radio-option:hover {
    background: rgba(255,255,255,0.05);
  }
  
  .radio-option.selected {
    background: rgba(52,199,89,0.12);
    border-color: var(--sm-accent);
  }
  
  .radio-option input[type="radio"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    margin: 0;
  }
  
  .radio-option label {
    cursor: pointer;
    font-size: 14px;
    flex: 1;
    margin: 0;
  }
  
  .dialog-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    padding-top: 20px;
    margin-top: 20px;
    border-top: 1px solid var(--sm-border);
  }
  
  .btn-dialog {
    padding: 10px 20px;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }
  
  .btn-dialog.cancel {
    background: rgba(255,255,255,0.08);
    color: var(--sm-text);
  }
  
  .btn-dialog.cancel:hover {
    background: rgba(255,255,255,0.12);
  }
  
  .btn-dialog.save {
    background: var(--sm-accent);
    color: #000;
  }
  
  .btn-dialog.save:hover {
    filter: brightness(1.1);
  }
  
  .add-item-btn {
    background: rgba(52,199,89,0.12);
    color: var(--sm-accent);
    border: 1px solid rgba(52,199,89,0.3);
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 20px;
    transition: all 0.2s;
  }
  
  .add-item-btn:hover {
    background: rgba(52,199,89,0.2);
  }
  
  .delete-item-btn {
    background: rgba(255,69,58,0.12);
    color: var(--sm-danger);
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .delete-item-btn:hover {
    background: rgba(255,69,58,0.2);
  }
  
  @media (max-width: 768px) {
    .config-dialog {
      width: 95%;
      max-height: 85vh;
      padding: 20px;
    }
    
    .dialog-header {
      margin-bottom: 20px;
    }
    
    .dialog-title {
      font-size: 18px;
    }
  }`;

// === Icons ===
const ICONS = {
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  sensor: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
  zone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  module: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
  bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
  flask: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6v5l4 9H5l4-9V3z"/><line x1="10" y1="3" x2="14" y2="3"/></svg>',
  rocket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  bulb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>',
  thermo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>',
  siren: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><line x1="12" y1="2" x2="12" y2="4"/></svg>',
  speaker: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>',
  nfc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8.32a7.43 7.43 0 0 1 0 7.36"/><path d="M9.46 6.21a11.76 11.76 0 0 1 0 11.58"/><path d="M12.91 4.1a15.91 15.91 0 0 1 .01 15.8"/><path d="M16.37 2a20.16 20.16 0 0 1 0 20"/></svg>',
};

const icon = (name) => ICONS[name] || "";

// === Tab Definitions ===
const TABS = [
  { key: "sensors", label: "Sensors", icon: "sensor" },
  { key: "zones", label: "Zones", icon: "zone" },
  { key: "users", label: "Users", icon: "user" },
  { key: "modules", label: "Modules", icon: "module" },
  { key: "automations", label: "Actions", icon: "bell" },
  { key: "testing", label: "Test", icon: "flask", badge: "SOON" },
  { key: "future", label: "Future", icon: "rocket" },
];

// Module definitions
const MODULE_DEFS = {
  camera: { name: "Camera", icon: "camera", desc: "POE control & recording", color: "var(--sm-blue)", domain: "camera" },
  lock: { name: "Lock", icon: "lock", desc: "Smart lock control with retry", color: "var(--sm-accent)", domain: "lock" },
  lights: { name: "Lights", icon: "bulb", desc: "Auto lights & alarm flash", color: "var(--sm-warning)", domain: "light" },
  climate: { name: "Climate", icon: "thermo", desc: "Multi-zone heating", color: "var(--sm-danger)", domain: "climate" },
  siren: { name: "Siren", icon: "siren", desc: "Alarm sound with failsafe", color: "var(--sm-danger)", domain: "siren" },
  tts: { name: "TTS", icon: "speaker", desc: "Danish voice messages", color: "var(--sm-purple)", domain: "tts" },
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
    this._data = {
      sensors: [],
      zones: {},
      users: {},
      modules: {},
      notifications: {},
      automations: {},
    };
    this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
    this._autoSection = "notifications";
    this._renderTimeout = null;
  }


  _queueRender() {
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
    }
    this._renderTimeout = setTimeout(() => {
      this._render();
      this._renderTimeout = null;
    }, 50);
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._initialized = true;
      this._loadData();
    }
    // DON'T re-render on every hass update - only when needed
    // This prevents scroll jumping
  }

  set narrow(narrow) {
    this._narrow = narrow;
    if (narrow) this.setAttribute("narrow", "");
    else this.removeAttribute("narrow");
  }

  set panel(panel) { this._panel = panel; }
  set route(route) { this._route = route; }

  disconnectedCallback() {
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
      this._renderTimeout = null;
    }
  }


  // === Web Socket Helpers ===
  async _callWS(type, data = {}) {
    if (!this._hass) return null;
    try {
      return await this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
    } catch (err) {
      console.error(`Secure Me WS error (${type}):`, err);
      return null;
    }
  }

  async _loadData() {
    const [sensors, zones, users, modules, notifications, automations, state] =
      await Promise.all([
        this._callWS("get_sensors"),
        this._callWS("get_zones"),
        this._callWS("get_users"),
        this._callWS("get_modules"),
        this._callWS("get_notifications"),
        this._callWS("get_automations"),
        this._callWS("get_alarm_state"),
      ]);

    if (sensors) this._data.sensors = sensors.sensors || [];
    if (zones) this._data.zones = zones.zones || {};
    if (users) this._data.users = users.users || {};
    if (modules) this._data.modules = modules.modules || {};
    if (notifications) this._data.notifications = notifications.notifications || {};
    if (automations) this._data.automations = automations.automations || {};
    if (state) this._alarmState = state.state || "disarmed";

    this._render();
  }

  // === Event ===
  _setTab(tab) { this._activeTab = tab; this._render(); }

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
      alert("✓ Test notification sent!");
    } else {
      alert("✗ Could not send: " + (result?.error || "Unknown error"));
    }
  }

  async _testAutomation(autoId) {
    const result = await this._callWS("test_automation", { automation_id: autoId });
    if (result && result.success) {
      alert("✓ Test automation executed!");
    } else {
      alert("✗ Could not execute: " + (result?.error || "Unknown error"));
    }
  }

  _setAutoSection(section) { this._autoSection = section; this._render(); }

  // === Render ===
  _render() {
    // Save scroll position before re-render
    const mainContent = this.shadowRoot.querySelector('.main-content');
    const scrollTop = mainContent ? mainContent.scrollTop : 0;

    const stateClass = this._alarmState.includes("armed") ? "armed"
      : this._alarmState === "arming" ? "arming" : "disarmed";

    const stateLabel = {
      disarmed: "Disarmed",
      arming: "Arming...",
      armed_away: "Armed Away",
      armed_home: "Armed Home",
      armed_night: "Armed Night",
      armed_vacation: "Armed Vacation",
      pending: "Pending",
      triggered: "🚨 TRIGGERED",
    }[this._alarmState] || this._alarmState;

    this.shadowRoot.innerHTML = `
      <style>${panelStyles}</style>

      <!-- SIDEBAR -->
      <nav class="sidebar">
        <div class="sidebar-header">
          <div class="sidebar-logo">${icon("shield")}</div>
          <span>
            <div class="sidebar-title">Secure Me</div>
            <div class="sidebar-version">v${VERSION}</div>
          </span>
        </div>

        <div class="sidebar-status">
          <div class="status-pill ${stateClass}">
            <div class="status-dot"></div>
            ${stateLabel}
          </div>
        </div>

        <div class="nav-tabs">
          ${TABS.map(t => `
            <button class="nav-tab ${this._activeTab === t.key ? "active" : ""}"
                    data-tab="${t.key}">
              <span class="nav-icon">${icon(t.icon)}</span>
              <span>${t.label}</span>
              ${t.badge ? `<span class="badge-soon">${t.badge}</span>` : ""}
            </button>
          `).join("")}
        </div>

        <div class="sidebar-footer">
          <div>Secure Me</div>
        
        
        ${this._showDialog === 'camera' ? this._renderCameraDialog() : ''}
      </div>
      </nav>

      <!-- MAIN CONTENT -->
      <main class="main-content">
        ${this._renderTab()}
      </main>
    `;

    // === Attach ===
    this.shadowRoot.querySelectorAll(".nav-tab").forEach(btn => {
      btn.addEventListener("click", () => this._setTab(btn.dataset.tab));
    });
    this._attachTabListeners();

    // Restore scroll position after re-render
    requestAnimationFrame(() => {
      const newMainContent = this.shadowRoot.querySelector('.main-content');
      if (newMainContent && scrollTop > 0) {
        newMainContent.scrollTop = scrollTop;
      }
    });
  }

  _renderTab() {
    switch (this._activeTab) {
      case "sensors": return this._renderSensors();
      case "zones": return this._renderZones();
      case "users": return this._renderUsers();
      case "modules": return this._renderModules();
      case "automations": return this._renderAutomations();
      case "testing": return this._renderPlaceholder("🧪", "Test Framework", "Coming in Phase 3 -- here you can run system tests, view results and monitor alarm health.", "warning", "Phase 3 -- Planned");
      case "future": return this._renderPlaceholder("🚀", "Upcoming Features", "Pet immunity, AI person detection, cloud sync, voice control and much more.", "purple", "Future Development");
      default: return "";
    }
  }

  // ===
  // TAB: SENSORS
  // ===
  _renderSensors() {
    const sensors = this._data.sensors || [];
    const enabled = sensors.filter(s => s.enabled).length;
    const typeLabels = { contact: "Contact", motion: "Motion", presence: "Presence" };

    return `
      <div class="section-header">
        <div>
          <h3 class="section-title">Available Sensors</h3>
          <p class="section-subtitle">${enabled} af ${sensors.length} sensorer aktive</p>
        </div>
        <span class="badge accent">${enabled} aktive</span>
      </div>

      <div class="sm-card no-pad" style="overflow:hidden">
        <div class="sm-list-header" style="grid-template-columns:1fr auto auto">
          <span>Sensor</span><span>Type</span><span style="text-align:right">Aktiv</span>
        </div>
        ${sensors.map(s => `
          <div class="sm-list-row ${s.enabled ? "" : "disabled"}"
               style="grid-template-columns:1fr auto auto">
            <div>
              <div style="font-size:14px;font-weight:500">${s.name}</div>
              <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:monospace">${s.entity_id}</div>
            </div>
            <span class="badge ${s.sensor_type}">${typeLabels[s.sensor_type] || s.sensor_type}</span>
            <button class="sm-checkbox ${s.enabled ? "checked" : ""}"
                    data-sensor="${s.entity_id}">
              ${s.enabled ? icon("check") : ""}
            </button>
          </div>
        `).join("")}
      </div>

      <div class="info-card warning">
        <span style="font-size:18px">🚨 ⚠️</span>
        <div>
          <div class="info-title" style="color:var(--sm-warning)">Minimumskrav</div>
          <div class="info-text">
            The alarm requires at least 1 contact sensor AND 1 motion sensor to be activated.
            Presence sensors are optional but recommended.
          </div>
        </div>
      </div>
    `;
  }

  // ===
  // TAB: ZONES
  // ===
  _renderZones() {
    const zones = this._data.zones || {};
    const typeLabels = { entry: "Entry/Exit", interior: "Interior", perimeter: "Perimeter", instant: "Instant" };

    return `
      <div class="section-header">
        <h3 class="section-title">Zones</h3>
        <button class="sm-btn primary sm" data-action="add-zone">
          ${icon("plus")} Add Zone
        </button>
      </div>

      <div class="zone-grid">
        ${Object.entries(zones).map(([id, z]) => `
          <div class="sm-card zone-card" style="padding:16px;
               border-color:${z.enabled ? "var(--sm-" + (z.type === "entry" ? "warning" : z.type === "perimeter" ? "danger" : "blue") + ")" : "var(--sm-border)"};
               opacity:${z.enabled ? 1 : 0.5}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div>
                <div style="font-size:15px;font-weight:600">${z.name || id}</div>
                <span class="badge ${z.type}">${typeLabels[z.type] || z.type}</span>
              </div>
              <button class="sm-toggle ${z.enabled ? "on" : ""}" data-zone-toggle="${id}">
                <div class="dot"></div>
              </button>
            </div>
            <div style="margin-top:12px;font-size:12px;color:var(--sm-text-secondary)">
              ${(z.sensors || []).length} sensorer tildelt
            </div>
            <div class="zone-modes">
              ${(z.modes || ["away", "home", "night"]).map(m =>
                `<span class="zone-mode">${m}</span>`
              ).join("")}
            </div>
          </div>
        `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No zones created yet. Click "Add Zone" to start.</div>'}
      </div>
    `;
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
                  Kode: ${u.code || "••••"}
                </div>
              </div>
            </div>
            <button class="sm-btn ghost sm" data-delete-user="${id}">${icon("trash")}</button>
          </div>
          ${u.nfc_tag ? `
            <div class="nfc-tag">
              <span style="color:var(--sm-purple)">${icon("nfc")}</span>
              <span class="nfc-tag-id">${u.nfc_tag}</span>
              <span style="font-size:11px;color:var(--sm-text-secondary);margin-left:auto">NFC Tag</span>
            </div>
          ` : `
            <div style="margin-top:12px">
              <button class="sm-btn ghost sm">${icon("nfc")} Tilknyt NFC tag</button>
            </div>
          `}
        </div>
      `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No users created yet.</div>'}

      <div class="info-card info">
        <span style="color:var(--sm-blue)">${icon("nfc")}</span>
        <div style="flex:1">
          <div class="info-title" style="color:var(--sm-blue)">Import NFC tags</div>
          <div class="info-text">Import existing NFC tags from Home Assistant</div>
        </div>
        <button class="sm-btn default sm" data-action="import-nfc">Import</button>
      </div>
    `;
  }

  // ===
  // TAB: MODULES
  // ===
  _renderModules() {
    const modules = this._data.modules || {};
    const enabledCount = Object.values(modules).filter(m => m.enabled).length;

    return `
      <div class="section-header">
        <h3 class="section-title">Modules</h3>
        <span class="badge accent">${enabledCount} aktive</span>
      </div>

      ${Object.entries(MODULE_DEFS).map(([key, def]) => {
        const mod = modules[key] || { enabled: false };
        const expanded = this._expandedModule === key && mod.enabled;
        return `
          <div class="sm-card" style="padding:0;overflow:hidden;
               border-color:${mod.enabled ? def.color + "33" : "var(--sm-border)"}">
            <div class="module-header ${mod.enabled ? "" : "disabled"}"
                 data-module-expand="${key}">
              <div class="module-icon" style="background:${mod.enabled ? def.color + "22" : "rgba(255,255,255,0.05)"};
                   color:${mod.enabled ? def.color : "var(--sm-text-tertiary)"}">
                ${icon(def.icon)}
              </div>
              <div style="flex:1">
                <div style="font-size:14px;font-weight:600">${def.name}</div>
                <div style="font-size:12px;color:var(--sm-text-secondary)">${def.desc}</div>
              </div>
              <button class="sm-toggle ${mod.enabled ? "on" : ""}"
                      data-module-toggle="${key}">
                <div class="dot"></div>
              </button>
            </div>
            ${expanded ? this._renderModuleConfig(key) : ""}
          </div>
        `;
      }).join("")}
    `;
  }

  _renderModuleConfig(moduleKey) {
    const moduleDef = MODULE_DEFS[moduleKey];
    const moduleData = this._data.modules[moduleKey] || {};
    const configJson = JSON.stringify(moduleData, null, 2);
    
    return `
      <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
        <div style="font-size:14px;font-weight:600;margin-bottom:8px">
          ${moduleDef.name} Configuration
        </div>
        <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">
          Edit konfiguration nedenfor (JSON format):
        </div>
        
        <textarea id="module-config-${moduleKey}" 
                  style="width:100%;min-height:200px;padding:12px;background:var(--sm-surface);
                         border:1px solid var(--sm-border);border-radius:8px;color:var(--sm-text);
                         font-family:monospace;font-size:12px;resize:vertical">${configJson}</textarea>
        
        <div style="margin-top:16px;display:flex;gap:8px">
          <button class="sm-btn primary" data-save-module-config="${moduleKey}">
            ${icon("check")} Save Changes
          </button>
          <button class="sm-btn default" data-cancel-module="${moduleKey}">
            Cancel
          </button>
        </div>
        
        <div style="margin-top:16px;padding:12px;background:var(--sm-blue-dim);border-radius:8px;font-size:11px">
          <strong>ðŸ’¡ Eksempel konfiguration:</strong>
          <details style="margin-top:8px">
            <summary style="cursor:pointer;font-weight:600">Vis eksempel for ${moduleDef.name}</summary>
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
  // TAB: AUTOMATIONS & NOTIFICATIONS
  // ===
  _renderAutomations() {
    const section = this._autoSection;
    const notifications = this._data.notifications || {};
    const automations = this._data.automations || {};

    return `
      <div class="segment-control">
        <button class="segment-btn ${section === "notifications" ? "active" : ""}"
                data-auto-section="notifications">Notifications</button>
        <button class="segment-btn ${section === "automations" ? "active" : ""}"
                data-auto-section="automations">Automations</button>
      </div>

      ${section === "notifications" ? `
        <div class="section-header">
          <h3 class="section-title">Notifications</h3>
          <button class="sm-btn primary sm" data-action="add-notification">
            ${icon("plus")} Ny notifikation
          </button>
        </div>
        ${Object.entries(notifications).map(([id, n]) => `
          <div class="sm-card" style="padding:16px;opacity:${n.enabled ? 1 : 0.5}">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
              <div style="flex:1">
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:14px;font-weight:600">${n.name || "Notifikation"}</span>
                  ${n.actions ? '<span class="badge actions">Actions</span>' : ""}
                </div>
                <div class="notif-message">${n.message || ""}</div>
              </div>
              <button class="sm-toggle ${n.enabled ? "on" : ""}"
                      data-notif-toggle="${id}">
                <div class="dot"></div>
              </button>
            </div>
            <div class="notif-actions">
              <button class="sm-btn default sm" data-test-notif="${id}">
                ${icon("play")} Test
              </button>
              <button class="sm-btn ghost sm" data-delete-notif="${id}">
                ${icon("trash")}
              </button>
            </div>
          </div>
        `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No notifications created yet.</div>'}
      ` : `
        <div class="section-header">
          <h3 class="section-title">Automations</h3>
          <button class="sm-btn primary sm" data-action="add-automation">
            ${icon("plus")} Ny automation
          </button>
        </div>
        ${Object.entries(automations).map(([id, a]) => `
          <div class="sm-card" style="padding:16px;opacity:${a.enabled ? 1 : 0.5}">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-size:14px;font-weight:600">${a.name || "Automation"}</div>
                <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:4px">
                  Trigger: <span class="badge entry">${a.trigger || "?"}</span>
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
        `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No automations created yet.</div>'}

        <div class="info-card info">
          <span style="font-size:20px">📘</span>
          <div style="flex:1">
            <div class="info-title" style="color:var(--sm-blue)">Blueprints</div>
            <div class="info-text">Use ready-made blueprints for alarm lighting, siren control and more</div>
          </div>
          <button class="sm-btn default sm">Gennemse</button>
        </div>
      `}
    `;
  }

  // ===
  // PLACEHOLDER TAB
  // ===
  _renderPlaceholder(emoji, title, desc, colorName, badgeText) {
    return `
      <div class="placeholder">
        <div class="placeholder-icon" style="background:var(--sm-${colorName}-dim)">${emoji}</div>
        <h3>${title}</h3>
        <p>${desc}</p>
        <span class="badge ${colorName === "warning" ? "entry" : "actions"}">${badgeText}</span>
      </div>
    `;
  }

  // ===
  // EVENT LISTENER ATTACHMENT
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
    // Validation
    const invalid = this._tempConfig.cameras.filter(c => !c.entity_id);
    if (invalid.length > 0) {
      alert('Please select a camera entity for all cameras before saving.');
      return;
    }
    
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
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      alert('✅ Camera configuration saved!\n\nRestart Home Assistant to activate changes.');
    } else {
      alert('❌ Could not save: ' + (result?.error || 'Unknown error'));
    }
  }

  _cancelDialog() {
    if (confirm('Discard changes?')) {
      this._showDialog = null;
      this._tempConfig = null;
      this._render();
    }
  }

  _renderCameraDialog() {
    const cameras = this._tempConfig?.cameras || [];
    const availableCameras = this._availableEntities.camera || [];
    const availableSwitches = this._availableEntities.switch || [];
    
    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            <span style="font-size: 24px;">📷</span>
            <div class="dialog-title">Camera Module Configuration</div>
            <button class="dialog-close" data-action="close-dialog">×</button>
          </div>
          
          <button class="add-item-btn" data-action="add-camera">
            ${icon("plus")} Add Camera
          </button>
          
          <div class="item-list">
            ${cameras.length === 0 ? 
              '<div style="text-align:center;color:var(--sm-text-secondary);padding:20px;">No cameras configured. Click "Add Camera" to start.</div>' :
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
            🗑 Delete
          </button>
        </div>
        
        <div class="form-group">
          <label class="form-label">Camera Entity</label>
          <input type="text" 
                 class="entity-search" 
                 placeholder="Search cameras..."
                 data-search-target="camera-select-${camera.id}">
          <select class="form-select" 
                  id="camera-select-${camera.id}"
                  data-camera-id="${camera.id}"
                  data-field="entity_id">
            <option value="">-- Select Camera --</option>
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
          <label class="form-label">Recording Mode</label>
          <div class="radio-group">
            <div class="radio-option ${camera.recording_mode === 'disabled' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="disabled">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="disabled"
                     ${camera.recording_mode === 'disabled' ? 'checked' : ''}>
              <label>Disabled</label>
            </div>
            <div class="radio-option ${camera.recording_mode === 'continuous' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="continuous">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="continuous"
                     ${camera.recording_mode === 'continuous' ? 'checked' : ''}>
              <label>Continuous Recording</label>
            </div>
            <div class="radio-option ${camera.recording_mode === 'motion' ? 'selected' : ''}"
                 data-camera-id="${camera.id}"
                 data-field="recording_mode"
                 data-value="motion">
              <input type="radio" 
                     name="mode-${camera.id}" 
                     value="motion"
                     ${camera.recording_mode === 'motion' ? 'checked' : ''}>
              <label>Motion-Triggered</label>
            </div>
          </div>
        </div>
      </div>
    `;
  }


  _attachTabListeners() {
    
    // Module expansion handlers
    this.shadowRoot.querySelectorAll("[data-module-expand]").forEach(header => {
      header.addEventListener("click", (e) => {
        const moduleKey = header.dataset.moduleExpand;
        this._expandedModule = this._expandedModule === moduleKey ? null : moduleKey;
        this._render();
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
            alert(`âœ… ${MODULE_DEFS[moduleKey].name} configuration saved!\n\nRestart Home Assistant to activate changes.`);
            this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
            await this._loadData();
          } else {
            alert(`âŒ Could not save: ${result?.error || "Unknown error"}`);
          }
        } catch (err) {
          alert(`âŒ JSON error: ${err.message}\n\nCheck the syntax in the text field.`);
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
        if (this._data.modules[key]?.enabled) this._expandModule(key);
      });
    });

    // Notification/automation toggles
    root.querySelectorAll("[data-notif-toggle]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._toggleNotification(btn.dataset.notifToggle);
      });
    });

    // Test buttons
    root.querySelectorAll("[data-test-notif]").forEach(btn => {
      btn.addEventListener("click", () => this._testNotification(btn.dataset.testNotif));
    });
    root.querySelectorAll("[data-test-auto]").forEach(btn => {
      btn.addEventListener("click", () => this._testAutomation(btn.dataset.testAuto));
    });


    // Action button handlers
    root.querySelectorAll("[data-action]").forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        switch(action) {
          case "add-zone":
            alert("Add Zone functionality coming in Phase 3.\n\nThis will open a dialog to create new zones with:\n- Zone name\n- Zone type (Entry/Exit, Interior, etc.)\n- Sensor assignment");
            break;
          case "add-user":
            alert("Add User functionality coming in Phase 3.\n\nThis will open a dialog to create new users with:\n- User name\n- Access code\n- Permissions");
            break;
          case "import-nfc":
            alert("Import NFC tags functionality coming in Phase 3.\n\nThis will scan Home Assistant for NFC tag entities and allow you to assign them to users.");
            break;
          case "add-notification":
            alert("Add Notification functionality coming in Phase 3.\n\nThis will create custom notification templates for alarm events.");
            break;
          case "add-automation":
            alert("Add Automation functionality coming in Phase 3.\n\nThis will create custom automation scripts for alarm actions.");
            break;
          default:
            console.warn("Unknown action:", action);
        }
      });
    });
    // === Dialog Event Listeners ===
    
    // Open camera config dialog
    root.querySelectorAll("[data-action='open-camera-config']").forEach(btn => {
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

    
    // Segment control
    root.querySelectorAll("[data-auto-section]").forEach(btn => {
      btn.addEventListener("click", () => this._setAutoSection(btn.dataset.autoSection));
    });
  }
}

// === Register Custom Element ===
customElements.define("secure-me-panel", SecureMePanel);
