/**
 * Secure Me - Configuration Panel
 * VERSION: 1.1.0
 *
 * Custom panel for Home Assistant using vanilla Custom Elements.
 * Uses HA CSS custom properties for theme compatibility.
 * Communicates with backend via WebSocket API.
 */

const DOMAIN = "secure_me";
const VERSION = "1.1.0";

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
  .sidebar-title { font-size: 17px; font-weight: 700; line-height: 1.2; }
  .sidebar-byline { font-size: 11px; color: var(--sm-text-tertiary); font-weight: 400; opacity: 0.7; }
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
  .badge.environmental { color: var(--sm-danger); background: var(--sm-danger-dim); font-weight: 700; }
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
  .sm-btn.ghost-outlined {
    background: transparent;
    color: var(--sm-text-secondary);
    border: 1px solid var(--sm-text-tertiary);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
  }
  .sm-btn.ghost-outlined:hover {
    border-color: var(--sm-text-secondary);
    background: rgba(255,255,255,0.04);
  }
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

  /* === Sensor two-column layout === */
  .sensor-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
  @media (max-width: 900px) { .sensor-two-col { grid-template-columns: 1fr; } }

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
    padding: 14px 16px;
    transition: opacity 0.2s ease;
  }
  .module-header.disabled { opacity: 0.45; }
  .module-icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s ease;
    cursor: pointer;
  }
  .module-icon:hover {
    filter: brightness(1.2);
    transform: scale(1.05);
  }
  .module-icon.disabled-icon {
    cursor: default;
  }
  .module-icon.disabled-icon:hover {
    filter: none;
    transform: none;
  }
  .module-name-area {
    flex: 1;
    cursor: pointer;
  }
  .module-header.disabled .module-name-area {
    cursor: default;
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
    font-size: 0; margin-bottom: 16px;
  }
  .placeholder-icon svg { width: 32px; height: 32px; }

  /* Status SVG icons inline sizing */
  .info-card svg { width: 20px; height: 20px; flex-shrink: 0; }
  .test-overall-icon svg { width: 28px; height: 28px; }
  .module-status-icon svg { width: 16px; height: 16px; }
  .dialog-close svg { width: 18px; height: 18px; }
  .dialog-close {
    background: none; border: none;
    color: var(--sm-text-secondary);
    cursor: pointer; padding: 4px;
    display: flex; align-items: center;
    border-radius: 6px;
    transition: color 0.15s, background 0.15s;
  }
  .dialog-close:hover { color: var(--sm-text); background: rgba(255,255,255,0.08); }
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

  .checkbox-option {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-bottom: 8px;
  }
  
  .checkbox-option:hover {
    background: rgba(255,255,255,0.05);
  }
  
  .checkbox-option input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    margin: 0;
  }
  
  .checkbox-option span {
    cursor: pointer;
    font-size: 14px;
    flex: 1;
  }

  .form-slider {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: var(--sm-border);
    outline: none;
    -webkit-appearance: none;
  }
  
  .form-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--sm-accent);
    cursor: pointer;
  }
  
  .form-slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--sm-accent);
    cursor: pointer;
    border: none;
  }
  
  .entity-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--sm-accent-dim);
    border: 1px solid var(--sm-accent);
    border-radius: 16px;
    font-size: 12px;
    margin: 4px;
  }
  
  .entity-chip button {
    background: none;
    border: none;
    color: var(--sm-text);
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 0;
    margin-left: 4px;
  }


  /* === Mobile Header (hidden on desktop) === */
  .mobile-header {
    display: none;
  }

  /* === Bottom Navigation Bar (hidden on desktop) === */
  .bottom-nav {
    display: none;
  }

  /* === More Drawer (hidden on desktop) === */
  .more-drawer-overlay {
    display: none;
  }

  @media (max-width: 768px) {
    :host {
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    /* Hide desktop sidebar completely */
    .sidebar {
      display: none;
    }

    /* Mobile top header */
    .mobile-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 16px;
      background: var(--sm-surface);
      border-bottom: 1px solid var(--sm-border);
      flex-shrink: 0;
      z-index: 10;
      min-height: 52px;
    }
    .mobile-header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .mobile-header-logo {
      width: 32px; height: 32px;
      border-radius: 9px;
      background: linear-gradient(135deg, var(--sm-accent), var(--sm-blue));
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 3px 8px var(--sm-accent-glow);
      flex-shrink: 0;
    }
    .mobile-header-logo svg { width: 17px; height: 17px; color: #fff; }
    .mobile-header-title {
      font-size: 16px;
      font-weight: 700;
      line-height: 1.2;
    }
    .mobile-header-subtitle {
      font-size: 10px;
      color: var(--sm-text-tertiary);
      opacity: 0.7;
    }
    .mobile-status-pill {
      display: flex; align-items: center; gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 12px; font-weight: 600;
      flex-shrink: 0;
    }
    .mobile-status-pill.disarmed { background: var(--sm-accent-dim); color: var(--sm-accent); }
    .mobile-status-pill.armed    { background: var(--sm-danger-dim); color: var(--sm-danger); }
    .mobile-status-pill.arming   { background: var(--sm-warning-dim); color: var(--sm-warning); }
    .mobile-status-dot {
      width: 7px; height: 7px; border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 6px currentColor;
    }

    /* Main content fills between header and bottom nav */
    .main-content {
      padding: 16px;
      max-width: 100%;
      flex: 1;
      overflow-y: auto;
      padding-bottom: 80px; /* room for bottom nav */
    }

    .zone-grid { grid-template-columns: 1fr; }

    .config-dialog-overlay { align-items: flex-end; }
    .config-dialog {
      width: 100%;
      max-height: 90vh;
      border-radius: 16px 16px 0 0;
      padding: 20px;
    }

    /* === Bottom Navigation Bar === */
    .bottom-nav {
      display: flex;
      position: fixed;
      bottom: 0; left: 0; right: 0;
      height: 64px;
      background: var(--sm-surface);
      border-top: 1px solid var(--sm-border);
      z-index: 100;
      padding-bottom: env(safe-area-inset-bottom, 0px);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .bottom-nav-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 3px;
      border: none;
      background: transparent;
      color: var(--sm-text-tertiary);
      font-family: inherit;
      font-size: 10px;
      font-weight: 500;
      cursor: pointer;
      padding: 8px 4px;
      transition: color 0.15s ease;
      -webkit-tap-highlight-color: transparent;
      position: relative;
    }
    .bottom-nav-item svg {
      width: 22px; height: 22px;
      opacity: 0.5;
      transition: opacity 0.15s ease, transform 0.15s ease;
    }
    .bottom-nav-item.active {
      color: var(--sm-accent);
    }
    .bottom-nav-item.active svg {
      opacity: 1;
      transform: scale(1.1);
    }
    .bottom-nav-item.active::before {
      content: '';
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 32px;
      height: 2px;
      background: var(--sm-accent);
      border-radius: 0 0 2px 2px;
    }
    .bottom-nav-item.more-active {
      color: var(--sm-text-secondary);
    }
    .bottom-nav-item.more-active svg {
      opacity: 0.8;
    }

    /* === More Drawer === */
    .more-drawer-overlay {
      display: block;
      position: fixed;
      bottom: 0; left: 0; right: 0; top: 0;
      background: rgba(0, 0, 0, 0.5);
      z-index: 200;
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
      animation: fadeIn 0.15s ease;
    }
    .more-drawer-overlay.hidden {
      display: none;
    }
    .more-drawer {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      background: var(--sm-surface);
      border-radius: 20px 20px 0 0;
      border-top: 1px solid var(--sm-border);
      padding: 12px 16px 32px;
      animation: slideUp 0.2s ease;
    }
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
    .more-drawer-handle {
      width: 36px; height: 4px;
      background: var(--sm-border);
      border-radius: 2px;
      margin: 0 auto 16px;
    }
    .more-drawer-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--sm-text-tertiary);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
      padding: 0 4px;
    }
    .more-drawer-item {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 12px;
      border-radius: 12px;
      border: none;
      background: transparent;
      color: var(--sm-text);
      font-family: inherit;
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
      width: 100%;
      text-align: left;
      transition: background 0.15s ease;
      -webkit-tap-highlight-color: transparent;
    }
    .more-drawer-item:active { background: rgba(255,255,255,0.06); }
    .more-drawer-item svg { width: 22px; height: 22px; color: var(--sm-text-secondary); flex-shrink: 0; }
    .more-drawer-item.active { color: var(--sm-accent); }
    .more-drawer-item.active svg { color: var(--sm-accent); }
  }

  @media (max-width: 480px) {
    .main-content {
      padding: 12px;
      padding-bottom: 80px;
    }
    .sm-card {
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 12px;
    }
    .section-title { font-size: 15px; }
  }



  /* === Dialog System === */
  .collapsible-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    padding: 12px 0;
    user-select: none;
  }
  .collapsible-header .chevron {
    width: 16px; height: 16px;
    transition: transform 0.2s ease;
    color: var(--sm-text-tertiary);
  }
  .collapsible-header.expanded .chevron {
    transform: rotate(180deg);
  }
  .collapsible-body {
    overflow: hidden;
    max-height: 0;
    transition: max-height 0.3s ease;
  }
  .collapsible-body.expanded {
    max-height: 2000px;
  }
  .sensor-status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .sensor-status-dot.online { background: var(--sm-accent); box-shadow: 0 0 6px var(--sm-accent); }
  .sensor-status-dot.offline { background: var(--sm-danger); box-shadow: 0 0 6px var(--sm-danger); }
  .test-grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
  }
  @media (max-width: 600px) {
    .test-grid-3 { grid-template-columns: 1fr; }
  }

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
  
  /* Dropdown options styling - Fix F1 */
  .form-select option {
    background: var(--primary-background-color, #111);
    color: var(--primary-text-color, #fff);
    padding: 8px;
  }
  
  .form-select option:hover,
  .form-select option:focus {
    background: var(--accent-color, #3498db);
    color: #fff;
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
  }

  /* === v0.7.0: Toast Notifications === */
  .sm-toast-container {
    position: fixed;
    top: 20px; right: 20px;
    z-index: 9999;
    display: flex; flex-direction: column; gap: 8px;
    pointer-events: none;
  }
  .sm-toast {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 13px; font-weight: 500;
    max-width: 320px;
    pointer-events: all;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    animation: sm-toast-in 0.25s cubic-bezier(0.34,1.56,0.64,1);
    backdrop-filter: blur(12px);
  }
  .sm-toast.success { background: rgba(52,199,89,0.18); border: 1px solid rgba(52,199,89,0.3); color: var(--sm-accent); }
  .sm-toast.error   { background: rgba(255,69,58,0.18);  border: 1px solid rgba(255,69,58,0.3);  color: var(--sm-danger); }
  .sm-toast.warning { background: rgba(255,159,10,0.18); border: 1px solid rgba(255,159,10,0.3); color: var(--sm-warning); }
  .sm-toast.info    { background: rgba(10,132,255,0.18); border: 1px solid rgba(10,132,255,0.3); color: var(--sm-blue); }
  .sm-toast svg { width: 18px; height: 18px; flex-shrink: 0; }
  .sm-toast-msg { flex: 1; }
  .sm-toast-close { opacity: 0.6; cursor: pointer; background: none; border: none; color: inherit; padding: 0; line-height: 1; }
  .sm-toast-close:hover { opacity: 1; }
  .sm-toast.fading { animation: sm-toast-out 0.2s ease forwards; }
  @keyframes sm-toast-in  { from { opacity:0; transform:translateX(20px); } to { opacity:1; transform:translateX(0); } }
  @keyframes sm-toast-out { from { opacity:1; transform:translateX(0);    } to { opacity:0; transform:translateX(20px); } }

  /* === v0.7.0: In-panel Confirm Dialog === */
  .sm-confirm-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.55);
    backdrop-filter: blur(4px);
    z-index: 9998;
    display: flex; align-items: center; justify-content: center;
  }
  .sm-confirm-dialog {
    background: var(--sm-surface);
    border: 1px solid var(--sm-border);
    border-radius: 16px;
    padding: 24px;
    max-width: 320px; width: 90%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    animation: sm-toast-in 0.2s ease;
  }
  .sm-confirm-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
  .sm-confirm-msg   { font-size: 13px; color: var(--sm-text-secondary); margin-bottom: 20px; line-height: 1.5; }
  .sm-confirm-btns  { display: flex; gap: 10px; justify-content: flex-end; }
  .sm-confirm-cancel { padding: 8px 16px; border-radius: 8px; border: 1px solid var(--sm-border); background: transparent; color: var(--sm-text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; }
  .sm-confirm-ok     { padding: 8px 16px; border-radius: 8px; border: none; background: var(--sm-danger); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; }
  .sm-confirm-cancel:hover { background: rgba(255,255,255,0.06); }
  .sm-confirm-ok:hover     { filter: brightness(1.1); }

  /* === v0.7.0: Module health badge on module card === */
  .module-health-badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 8px; border-radius: 20px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.3px;
  }
  .module-health-badge.ok      { background: rgba(52,199,89,0.15);  color: var(--sm-accent);  }
  .module-health-badge.warn    { background: rgba(255,159,10,0.15); color: var(--sm-warning); }
  .module-health-badge.error   { background: rgba(255,69,58,0.15);  color: var(--sm-danger);  }
  .module-health-badge.degraded{ background: rgba(255,69,58,0.15);  color: var(--sm-danger);  }
  .module-health-badge.unknown { background: rgba(255,255,255,0.07);color: var(--sm-text-tertiary); }
  .module-health-badge svg { width: 10px; height: 10px; }

  /* === v0.7.0: Triggered state pulse on sidebar status pill === */
  .status-pill.triggered {
    background: rgba(255,69,58,0.2);
    color: var(--sm-danger);
    animation: sm-pulse-red 1s ease-in-out infinite;
  }
  .mobile-status-pill.triggered {
    background: rgba(255,69,58,0.2);
    color: var(--sm-danger);
    animation: sm-pulse-red 1s ease-in-out infinite;
  }
  .status-pill.pending {
    background: rgba(255,159,10,0.18);
    color: var(--sm-warning);
  }
  .mobile-status-pill.pending {
    background: rgba(255,159,10,0.18);
    color: var(--sm-warning);
  }
  @keyframes sm-pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,69,58,0.4); }
    50%       { box-shadow: 0 0 0 8px rgba(255,69,58,0); }
  }`;

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
  circle: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>',
};

const icon = (name) => ICONS[name] || "";

// === Tab Definitions ===
const TABS = [
  { key: "sensors", label: "Sensors", icon: "sensor" },
  { key: "zones", label: "Zones", icon: "zone" },
  { key: "users", label: "Users", icon: "user" },
  { key: "modules", label: "Modules", icon: "module" },
  { key: "automations", label: "Actions", icon: "bell" },
  { key: "testing", label: "Test", icon: "flask" },
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
    this._testRunning = false;
    this._batteryOkExpanded = false;  // Collapsible: batteries >50%
    this._hiddenSensorsExpanded = false; // Collapsible: auto-hidden sensors
    this._availablePersons = null;       // Cached person entities for user dialog
    this._sensorStatusExpanded = true; // Sensor online/offline section
    this._sensorsInactiveExpanded = false; // Collapsible: inactive sensors
	this._healthUpdateUnsubscribe = null;
    this._lastHealthUpdate = null;
  }


  // PERF: In-place patch of alarm state pills — avoids full re-render on every state change.
  // Mirrors the _updateWattDisplay / _updateBarsInPlace pattern from pc-user-statistics-panel.
  _updateStatusPills() {
    const stateClass = this._alarmState === "triggered" ? "triggered"
      : this._alarmState === "pending" ? "pending"
      : this._alarmState.includes("armed") ? "armed"
      : this._alarmState === "arming" ? "arming" : "disarmed";

    const stateLabel = {
      disarmed: "Disarmed",
      arming: "Arming...",
      armed_away: "Armed Away",
      armed_home: "Armed Home",
      armed_night: "Armed Night",
      armed_vacation: "Armed Vacation",
      pending: "Pending",
      triggered: "TRIGGERED",
    }[this._alarmState] || this._alarmState;

    const allClasses = ["disarmed", "armed", "arming", "pending", "triggered"];

    // Desktop sidebar pill (use shell ID for reliability)
    const pill = this.shadowRoot?.getElementById("shell-status-pill")
              || this.shadowRoot?.querySelector(".status-pill");
    if (pill) {
      allClasses.forEach(c => pill.classList.remove(c));
      pill.classList.add(stateClass);
      const dot = pill.querySelector(".status-dot");
      const textNode = [...pill.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
      if (textNode) textNode.textContent = " " + stateLabel;
      else if (dot) dot.insertAdjacentText("afterend", " " + stateLabel);
    }

    // Mobile header pill (use shell ID for reliability)
    const mobilePill = this.shadowRoot?.getElementById("shell-mobile-pill")
                    || this.shadowRoot?.querySelector(".mobile-status-pill");
    if (mobilePill) {
      allClasses.forEach(c => mobilePill.classList.remove(c));
      mobilePill.classList.add(stateClass);
      const mDot = mobilePill.querySelector(".mobile-status-dot");
      const mText = [...mobilePill.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
      if (mText) mText.textContent = " " + stateLabel;
      else if (mDot) mDot.insertAdjacentText("afterend", " " + stateLabel);
    }
  }

  // PERF v0.6.0: Two render modes:
  //   _render()       — immediate, for user-initiated actions (tab switch, dialog)
  //   _queueRender()  — debounced 50ms, for data loads and background updates
  //                     Batches multiple rapid calls into one DOM update.
  _queueRender() {
    if (this._renderTimeout) {
      clearTimeout(this._renderTimeout);
    }
    this._renderTimeout = setTimeout(() => {
      // Focus guard: never wipe the DOM while the user is actively typing
      // in an input, textarea or select. Background events (health updates,
      // data polls) must not destroy unsaved keystrokes or cursor position.
      // _render() can still be called directly for user-initiated actions.
      const active = this.shadowRoot?.activeElement;
      if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT")) {
        // Reschedule and check again in 300ms
        this._renderTimeout = setTimeout(() => {
          this._render();
          this._renderTimeout = null;
        }, 300);
        return;
      }
      this._render();
      this._renderTimeout = null;
    }, 50);
  }

  // === v0.7.0: Toast Notification System ===
  // Replaces all alert() calls with non-blocking in-panel toasts.
  // type: 'success' | 'error' | 'warning' | 'info'
  _toast(message, type = 'success', duration = 4000) {
    // Use the persistent shell toast container (never rebuilt)
    let container = this.shadowRoot.getElementById('shell-toast')
                 || this.shadowRoot.querySelector('.sm-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'sm-toast-container';
      this.shadowRoot.appendChild(container);
    }

    const toastIcon = {
      success: icon('ok'),
      error:   icon('fail'),
      warning: icon('warn'),
      info:    icon('circle'),
    }[type] || icon('circle');

    const toast = document.createElement('div');
    toast.className = `sm-toast ${type}`;
    toast.innerHTML = `
      ${toastIcon}
      <span class="sm-toast-msg">${message}</span>
      <button class="sm-toast-close">${icon('close')}</button>
    `;

    const dismiss = () => {
      toast.classList.add('fading');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    };

    toast.querySelector('.sm-toast-close').addEventListener('click', dismiss);
    container.appendChild(toast);
    if (duration > 0) setTimeout(dismiss, duration);
  }

  // === v0.7.0: In-panel Confirm Dialog ===
  // Replaces browser confirm() with a styled panel-native dialog.
  // Returns a Promise<boolean>.
  _confirm(message, title = 'Confirm') {
    return new Promise((resolve) => {
      // Remove any existing confirm overlay
      this.shadowRoot.querySelector('.sm-confirm-overlay')?.remove();

      const overlay = document.createElement('div');
      overlay.className = 'sm-confirm-overlay';
      overlay.innerHTML = `
        <div class="sm-confirm-dialog">
          <div class="sm-confirm-title">${title}</div>
          <div class="sm-confirm-msg">${message}</div>
          <div class="sm-confirm-btns">
            <button class="sm-confirm-cancel">Cancel</button>
            <button class="sm-confirm-ok">Delete</button>
          </div>
        </div>
      `;

      overlay.querySelector('.sm-confirm-cancel').addEventListener('click', () => {
        overlay.remove(); resolve(false);
      });
      overlay.querySelector('.sm-confirm-ok').addEventListener('click', () => {
        overlay.remove(); resolve(true);
      });
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) { overlay.remove(); resolve(false); }
      });

      this.shadowRoot.appendChild(overlay);
    });
  }

  set hass(hass) {
    this._hass = hass;
	// F2 FIX: Ensure health event subscription
    if (hass && hass.connection && !this._healthUpdateUnsubscribe) {
      this._subscribeToHealthUpdates();
    }
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
    // Guard: only call if it's actually a function (subscription may still be pending)
    if (typeof this._healthUpdateUnsubscribe === 'function') {
      this._healthUpdateUnsubscribe();
      this._healthUpdateUnsubscribe = null;
    } else {
      this._healthUpdateUnsubscribe = null;
    }
    
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

    if (this._healthUpdateUnsubscribe) {
      return;
    }

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
              this._updateStatusPills();
            }
          }
        },
        'secure_me_health_updated'
      );
      console.log('[Secure Me] Subscribed to health updates');
    } catch (err) {
      console.warn('[Secure Me] Health subscription failed:', err);
      this._healthUpdateUnsubscribe = null;
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
      return await this._hass.callWS({ type: `${DOMAIN}/${type}`, ...data });
    } catch (err) {
      console.error(`Secure Me WS error (${type}):`, err);
      return null;
    }
  }

  async _loadData() {
    // PERF: Split into two phases.
    // Phase 1 — fast: 7 essential calls needed to render any tab immediately.
    // Phase 2 — lazy: health + test results are only needed on the Testing tab.
    const [sensors, zones, users, modules, notifications, automations, state, fakePresence] =
      await Promise.all([
        this._callWS("get_sensors"),
        this._callWS("get_zones"),
        this._callWS("get_users"),
        this._callWS("get_modules"),
        this._callWS("get_notifications"),
        this._callWS("get_automations"),
        this._callWS("get_alarm_state"),
        this._callWS("get_fake_presence"),
      ]);

    if (sensors) this._data.sensors = sensors.sensors || [];
    if (zones) this._data.zones = zones.zones || {};
    if (users) this._data.users = users.users || {};
    if (modules) this._data.modules = modules.modules || {};
    if (notifications) this._data.notifications = notifications.notifications || {};
    if (automations) this._data.automations = automations.automations || {};
    if (state) this._alarmState = state.state || "disarmed";
    if (fakePresence) {
      this._data.fakePresence = fakePresence.active || false;
      this._data.homeAloneCameras = fakePresence.home_alone_cameras || [];
    }

    // Render immediately with essential data — no waiting for heavy tabs
    this._queueRender();

    // Phase 2 — lazy: fetch health + test results in background
    this._loadTestingData();
  }

  async _loadTestingData() {
    const [health, testResults] = await Promise.all([
      this._callWS("get_health_summary"),
      this._callWS("get_test_results"),
    ]);
    if (health) this._data.health = health;
    if (testResults) this._data.testResults = testResults.results || [];
    // Only re-render if user is already on the testing tab
    if (this._activeTab === "testing") this._queueRender();
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
      this._toast("Test notification sent!", "success");
    } else {
      this._toast("Could not send: " + (result?.error || "Unknown error"), "error");
    }
  }

  async _testAutomation(autoId) {
    const result = await this._callWS("test_automation", { automation_id: autoId });
    if (result && result.success) {
      this._toast("Test automation executed!", "success");
    } else {
      this._toast("Could not execute: " + (result?.error || "Unknown error"), "error");
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
    const BOTTOM_TABS = TABS.slice(0, 5);
    const MORE_TABS   = TABS.slice(5);

    this.shadowRoot.innerHTML = `
      <style>${panelStyles}</style>

      <!-- MOBILE HEADER (hidden on desktop) -->
      <header class="mobile-header">
        <div class="mobile-header-left">
          <div class="mobile-header-logo">${icon("shield")}</div>
          <div>
            <div class="mobile-header-title">Secure Me</div>
            <div class="mobile-header-subtitle">by KingPainter</div>
          </div>
        </div>
        <div class="mobile-status-pill disarmed" id="shell-mobile-pill">
          <div class="mobile-status-dot"></div>
          Disarmed
        </div>
      </header>

      <!-- SIDEBAR (desktop only) -->
      <nav class="sidebar">
        <div class="sidebar-header">
          <div class="sidebar-logo">${icon("shield")}</div>
          <span>
            <div class="sidebar-title">Secure Me</div>
            <div class="sidebar-byline">by KingPainter</div>
          </span>
        </div>

        <div class="sidebar-status">
          <div class="status-pill disarmed" id="shell-status-pill">
            <div class="status-dot"></div>
            Disarmed
          </div>
        </div>

        <div class="nav-tabs" id="shell-nav-tabs">
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
          <div>Secure Me v${VERSION}</div>
        </div>
      </nav>

      <!-- MAIN CONTENT — patched by _render() -->
      <main class="main-content" id="shell-main"></main>

      <!-- BOTTOM NAVIGATION BAR (mobile only) -->
      <nav class="bottom-nav" id="shell-bottom-nav">
        ${BOTTOM_TABS.map(t => `
          <button class="bottom-nav-item ${this._activeTab === t.key ? "active" : ""}"
                  data-tab="${t.key}">
            ${icon(t.icon)}
            <span>${t.label}</span>
          </button>
        `).join("")}
        <button class="bottom-nav-item" id="more-btn">
          ${icon("dots")}
          <span>More</span>
        </button>
      </nav>

      <!-- MORE DRAWER OVERLAY (mobile only) -->
      <div class="more-drawer-overlay hidden" id="more-overlay">
        <div class="more-drawer">
          <div class="more-drawer-handle"></div>
          <div class="more-drawer-title">More</div>
          ${MORE_TABS.map(t => `
            <button class="more-drawer-item ${this._activeTab === t.key ? "active" : ""}"
                    data-tab="${t.key}">
              ${icon(t.icon)}
              <span>${t.label}</span>
            </button>
          `).join("")}
        </div>
      </div>

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

    // Desktop sidebar nav
    root.querySelectorAll(".nav-tab[data-tab]").forEach(btn => {
      btn.addEventListener("click", () => this._setTab(btn.dataset.tab));
    });

    // Mobile bottom nav
    root.querySelectorAll("#shell-bottom-nav .bottom-nav-item[data-tab]").forEach(btn => {
      btn.addEventListener("click", () => this._setTab(btn.dataset.tab));
    });

    // More drawer
    const moreBtn     = root.getElementById("more-btn");
    const moreOverlay = root.getElementById("more-overlay");
    if (moreBtn && moreOverlay) {
      moreBtn.addEventListener("click", () => moreOverlay.classList.toggle("hidden"));
      moreOverlay.addEventListener("click", (e) => {
        if (e.target === moreOverlay) moreOverlay.classList.add("hidden");
      });
      moreOverlay.querySelectorAll(".more-drawer-item[data-tab]").forEach(btn => {
        btn.addEventListener("click", () => {
          moreOverlay.classList.add("hidden");
          this._setTab(btn.dataset.tab);
        });
      });
    }
  }

  // Update nav active state without full re-render
  _updateNavActive() {
    this.shadowRoot.querySelectorAll(".nav-tab[data-tab]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === this._activeTab);
    });
    this.shadowRoot.querySelectorAll("#shell-bottom-nav .bottom-nav-item[data-tab]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === this._activeTab);
    });
    // More button: highlight if active tab is in MORE_TABS
    const MORE_TABS = TABS.slice(5);
    const moreIsActive = MORE_TABS.some(t => t.key === this._activeTab);
    const moreBtn = this.shadowRoot.getElementById("more-btn");
    if (moreBtn) moreBtn.classList.toggle("more-active", moreIsActive);
    // More drawer items
    this.shadowRoot.querySelectorAll(".more-drawer-item[data-tab]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === this._activeTab);
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

    // Patch tab content
    mainContent.innerHTML = this._renderTab();

    // Update nav active classes (no DOM teardown)
    this._updateNavActive();

    // Update status pills in-place
    this._updateStatusPills();

    // Manage dialog: inject or remove from mount point
    const dialogMount = this.shadowRoot.getElementById("shell-dialog-mount");
    if (dialogMount) {
      const dialogHtml = this._showDialog === 'camera'  ? this._renderCameraDialog()
        : this._showDialog === 'lock'    ? this._renderLockDialog()
        : this._showDialog === 'climate' ? this._renderClimateDialog()
        : this._showDialog === 'siren'   ? this._renderSirenDialog()
        : this._showDialog === 'lights'  ? this._renderLightsDialog()
        : this._showDialog === 'tts'     ? this._renderTTSDialog()
        : this._showDialog === 'user'    ? this._renderUserDialog()
        : '';
      dialogMount.innerHTML = dialogHtml;
    }

    this._attachTabListeners();

    // Restore scroll position
    requestAnimationFrame(() => {
      const m = this.shadowRoot.getElementById("shell-main");
      if (m && scrollTop > 0) m.scrollTop = scrollTop;
    });
  }

  _renderTab() {
    switch (this._activeTab) {
      case "sensors": return this._renderSensors();
      case "zones": return this._renderZones();
      case "users": return this._renderUsers();
      case "modules": return this._renderModules();
      case "automations": return this._renderAutomations();
      case "testing": return this._renderTesting();
      case "future": return this._renderFuture();
      default: return "";
    }
  }

  // ===
  // TAB: SENSORS
  // ===
  _renderSensors() {
    const sensors = this._data.sensors || [];
    const envSensors    = sensors.filter(s => s.is_environmental && !s.env_unmarked);
    const normalSensors = sensors.filter(s => !s.is_environmental || s.env_unmarked);
    const enabled       = normalSensors.filter(s => s.enabled && !s.auto_hidden);
    const disabled      = normalSensors.filter(s => !s.enabled && !s.auto_hidden);
    const autoHidden    = normalSensors.filter(s => s.auto_hidden);
    const typeLabels    = { contact: "Contact", motion: "Motion", presence: "Presence", environmental: "Environmental" };

    const renderSensorRow = (s) => `
      <div class="sm-list-row ${s.enabled ? "" : "disabled"}"
           style="grid-template-columns:1fr auto auto auto">
        <div>
          <div style="font-size:14px;font-weight:500">${s.name}</div>
          <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:monospace">${s.entity_id}</div>
        </div>
        <span class="badge ${s.sensor_type}">${typeLabels[s.sensor_type] || s.sensor_type}</span>
        ${!s.enabled ? `<button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;color:var(--sm-danger)"
                data-hide-sensor="${s.entity_id}" title="Hide this sensor">${icon("trash")}</button>` : '<span></span>'}
        <button class="sm-checkbox ${s.enabled ? "checked" : ""}"
                data-sensor="${s.entity_id}">
          ${s.enabled ? icon("check") : ""}
        </button>
      </div>
    `;

    const renderEnvRow = (s) => `
      <div style="display:grid;grid-template-columns:1fr auto auto;align-items:center;
                  padding:10px 16px;border-bottom:1px solid var(--sm-border)">
        <div>
          <div style="font-size:14px;font-weight:500">${s.name}</div>
          <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:monospace">${s.entity_id}</div>
        </div>
        <span class="badge environmental" style="margin-right:8px">Required</span>
        <button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;color:var(--sm-text-tertiary)"
                data-unmark-env="${s.entity_id}" title="Remove incorrect environmental classification">
          Remove
        </button>
      </div>
    `;

    const renderHiddenRow = (s) => `
      <div style="display:grid;grid-template-columns:1fr auto auto;align-items:center;
                  padding:8px 16px;border-bottom:1px solid var(--sm-border);opacity:0.65">
        <div>
          <div style="font-size:13px;font-weight:400;color:var(--sm-text-secondary)">${s.name}</div>
          <div style="font-size:10px;color:var(--sm-text-tertiary);font-family:monospace">${s.entity_id}</div>
        </div>
        <span class="badge" style="background:rgba(255,255,255,0.06);color:var(--sm-text-tertiary)">Auto-hidden</span>
        <button class="sm-btn ghost sm" style="padding:4px 8px;font-size:11px;margin-left:8px"
                data-hide-sensor="${s.entity_id}" title="Permanently exclude this sensor">
          Exclude
        </button>
      </div>
    `;

    const fakePresenceActive = this._data.fakePresence || false;

    return `
      <div class="section-header">
        <div>
          <h3 class="section-title">Available Sensors</h3>
          <p class="section-subtitle">${enabled.length} of ${normalSensors.filter(s=>!s.auto_hidden).length} regular sensors active</p>
        </div>
        <span class="badge accent">${enabled.length} active</span>
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
                : 'Inactive &mdash; alarm behaves normally.'}
            </div>
          </div>
          <button class="sm-toggle ${fakePresenceActive ? 'on' : ''}" data-action="toggle-fake-presence">
            <div class="dot"></div>
          </button>
        </div>
        ${fakePresenceActive ? `
          <div style="margin-top:12px;padding:10px 12px;border-radius:8px;background:var(--sm-warning-dim);
                      border:1px solid rgba(255,159,10,0.2);font-size:12px;color:var(--sm-warning)">
            Fake presence is ON. The alarm will not auto-arm while this is active.
            Remember to turn it off when you leave.
          </div>
        ` : ''}
      </div>

      ${envSensors.length > 0 ? `
        <div class="sm-card no-pad" style="overflow:hidden;margin-bottom:16px;border-color:rgba(255,59,48,0.3)">
          <div class="sm-list-header" style="background:rgba(255,59,48,0.08);border-bottom:1px solid rgba(255,59,48,0.2)">
            <span style="display:flex;align-items:center;gap:8px">
              <span style="color:var(--sm-danger)">${icon("warn")}</span>
              Environmental Sensors — Always Active (${envSensors.length})
            </span>
            <span style="font-size:11px;color:var(--sm-text-secondary)">Notifications cannot be disabled</span>
          </div>
          ${envSensors.map(s => renderEnvRow(s)).join("")}
        </div>
      ` : ""}

      <div class="sensor-two-col">
        <div class="sm-card no-pad" style="overflow:hidden">
          <div class="sm-list-header" style="grid-template-columns:1fr auto auto auto">
            <span>Active (${enabled.length})</span><span>Type</span><span></span><span style="text-align:right">On</span>
          </div>
          ${enabled.length > 0 ? enabled.map(s => renderSensorRow(s)).join("") : `
            <div style="padding:20px;text-align:center;color:var(--sm-text-tertiary);font-size:13px">
              No sensors activated yet.
            </div>
          `}
        </div>

        <div class="sm-card no-pad" style="overflow:hidden">
          <div class="sm-list-header" style="grid-template-columns:1fr auto auto auto">
            <span>Inactive (${disabled.length})</span><span>Type</span><span style="font-size:11px;color:var(--sm-danger)">Hide</span><span style="text-align:right">On</span>
          </div>
          ${disabled.length > 0 ? disabled.map(s => renderSensorRow(s)).join("") : `
            <div style="padding:20px;text-align:center;color:var(--sm-text-tertiary);font-size:13px">
              All sensors are active.
            </div>
          `}
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
          <div class="info-title" style="color:var(--sm-warning)">Minimum Requirements</div>
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
    const enabledSensors = (this._data.sensors || []).filter(s => s.enabled);
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
              <div style="display:flex;gap:8px;align-items:center">
                <button class="sm-btn ghost sm" data-delete-zone="${id}" title="Delete zone">${icon("trash")}</button>
                <button class="sm-toggle ${z.enabled ? "on" : ""}" data-zone-toggle="${id}">
                  <div class="dot"></div>
                </button>
              </div>
            </div>
            <div style="margin-top:12px;font-size:12px;color:var(--sm-text-secondary)">
              ${(z.sensors || []).length} sensors assigned
            </div>
            <div class="zone-modes">
              ${(z.modes || ["away", "home", "night"]).map(m =>
                '<span class="zone-mode">' + m + '</span>'
              ).join("")}
            </div>
          </div>
        `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No zones created yet. Click "Add Zone" to start.</div>'}
      </div>

      ${this._showDialog === 'zone' ? this._renderZoneDialog() : ''}
    `;
  }

  _renderZoneDialog() {
    const enabledSensors = (this._data.sensors || []).filter(s => s.enabled);
    const temp = this._tempConfig || {};
    const typeLabels = { entry: "Entry/Exit", interior: "Interior", perimeter: "Perimeter", instant: "Instant" };

    return '<div class="config-dialog-overlay">' +
      '<div class="config-dialog">' +
        '<div class="dialog-header">' +
          icon('shield') +
          '<div class="dialog-title">Add Zone</div>' +
          '<button class="dialog-close" data-action="close-dialog">' + icon("close") + '</button>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Zone Name</label>' +
          '<input type="text" class="form-input" id="zone-name" placeholder="e.g. Front Door, Living Room" value="' + (temp.name || '') + '">' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Zone Type</label>' +
          '<select class="form-select" id="zone-type">' +
            '<option value="entry"' + (temp.type === 'entry' ? ' selected' : '') + '>Entry/Exit - Doors with delay</option>' +
            '<option value="interior"' + (temp.type === 'interior' ? ' selected' : '') + '>Interior - Motion sensors</option>' +
            '<option value="perimeter"' + (temp.type === 'perimeter' ? ' selected' : '') + '>Perimeter - Instant windows</option>' +
            '<option value="instant"' + (temp.type === 'instant' ? ' selected' : '') + '>Instant - No delay trigger</option>' +
          '</select>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Active in Modes</label>' +
          '<div style="display:flex;flex-wrap:wrap;gap:8px">' +
            ['away', 'home', 'night', 'vacation'].map(m =>
              '<label style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:8px;background:rgba(255,255,255,0.05);cursor:pointer;font-size:13px">' +
                '<input type="checkbox" class="zone-mode-cb" value="' + m + '"' + ((temp.modes || ['away','home','night']).includes(m) ? ' checked' : '') + '> ' + m +
              '</label>'
            ).join('') +
          '</div>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Assign Sensors (' + enabledSensors.length + ' available)</label>' +
          (enabledSensors.length > 0 ?
            enabledSensors.map(s =>
              '<label style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:8px;cursor:pointer;border:1px solid var(--sm-border);margin-bottom:6px;font-size:13px">' +
                '<input type="checkbox" class="zone-sensor-cb" value="' + s.entity_id + '"' + ((temp.sensors || []).includes(s.entity_id) ? ' checked' : '') + '>' +
                '<span style="flex:1">' + s.name + '</span>' +
                '<span class="badge ' + s.sensor_type + '" style="font-size:10px">' + s.sensor_type + '</span>' +
              '</label>'
            ).join('') :
            '<div style="padding:12px;text-align:center;color:var(--sm-text-tertiary);font-size:12px">No sensors enabled. Activate sensors in the Sensors tab first.</div>'
          ) +
        '</div>' +

        '<div class="dialog-footer">' +
          '<button class="btn-dialog cancel" data-action="close-dialog">Cancel</button>' +
          '<button class="btn-dialog save" data-action="save-zone">Save Zone</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  async _saveZone() {
    const root = this.shadowRoot;
    const name = root.querySelector('#zone-name')?.value?.trim();
    const type = root.querySelector('#zone-type')?.value || 'entry';
    const modes = Array.from(root.querySelectorAll('.zone-mode-cb:checked')).map(cb => cb.value);
    const sensors = Array.from(root.querySelectorAll('.zone-sensor-cb:checked')).map(cb => cb.value);

    if (!name) {
      this._toast('Please enter a zone name.', 'warning'); return;
      return;
    }

    const zoneId = 'zone_' + Date.now();
    const config = {
      name: name,
      type: type,
      enabled: true,
      modes: modes,
      sensors: sensors,
    };

    const result = await this._callWS('save_zone', { zone_id: zoneId, config: config });
    if (result && result.success !== false) {
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
    } else {
      this._toast('Could not save zone: ' + (result?.error || 'Unknown error'), 'error');
    }
  }

  async _deleteZone(zoneId) {
    if (!await this._confirm('This zone and all its sensors will be removed.', 'Delete Zone?')) return;
    await this._callWS('delete_zone', { zone_id: zoneId });
    this._toast('Zone deleted', 'success');
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
                  <div style="font-size:11px;color:var(--sm-blue);margin-top:4px;font-family:monospace">
                    Tracker: ${u.person_entity}
                  </div>` : ""}
              </div>
            </div>
            <div style="display:flex;gap:6px">
              <button class="sm-btn default sm" data-edit-user="${id}">${icon("settings")} Edit</button>
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
              <span style="color:var(--sm-blue);font-size:13px">Person tracker linked</span>
              <span style="font-size:11px;color:var(--sm-text-secondary);font-family:monospace;margin-left:auto">${u.person_entity}</span>
            </div>
          ` : ""}
        </div>
      `).join("") || '<div class="sm-card" style="text-align:center;color:var(--sm-text-secondary)">No users created yet. Click "Add User" to start.</div>'}

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

  _renderUserDialog() {
    const temp = this._tempConfig || {};
    const isEdit = !!temp._userId;
    const title = isEdit ? 'Edit User' : 'Add User';

    return '<div class="config-dialog-overlay">' +
      '<div class="config-dialog">' +
        '<div class="dialog-header">' +
          icon('user') +
          '<div class="dialog-title">' + title + '</div>' +
          '<button class="dialog-close" data-action="close-dialog">' + icon("close") + '</button>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">User Name</label>' +
          '<input type="text" class="form-input" id="user-name" placeholder="e.g. Flemming, Sarah" value="' + (temp.name || '') + '">' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">' + (isEdit ? 'New Access Code (leave blank to keep existing)' : 'Access Code (4-6 digits)') + '</label>' +
          '<input type="password" class="form-input" id="user-code" placeholder="' + (isEdit ? 'Leave blank to keep current code' : 'e.g. 1234') + '" maxlength="6" pattern="[0-9]*" inputmode="numeric" value="">' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">' + (isEdit ? 'Confirm New Code' : 'Confirm Code') + '</label>' +
          '<input type="password" class="form-input" id="user-code-confirm" placeholder="' + (isEdit ? 'Leave blank to keep current code' : 'Repeat code') + '" maxlength="6" pattern="[0-9]*" inputmode="numeric" value="">' +
        '</div>' +

        '<div class="form-group">' +
          '<label style="display:flex;align-items:center;gap:10px;cursor:pointer;padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.05);font-size:14px">' +
            '<input type="checkbox" id="user-admin"' + (temp.admin ? ' checked' : '') + '>' +
            '<span style="flex:1">Administrator</span>' +
            '<span style="font-size:11px;color:var(--sm-text-tertiary)">Full access</span>' +
          '</label>' +
        '</div>' +

        '<div class="form-group">' +
          '<label class="form-label">Link Person Tracker (optional)</label>' +
          '<select class="form-select" id="user-person-entity">' +
            '<option value="">-- None (manual arm/disarm only) --</option>' +
            (this._availablePersons || []).map(p =>
              '<option value="' + p.entity_id + '"' + (temp.person_entity === p.entity_id ? ' selected' : '') + '>' +
                p.name + ' (' + p.entity_id + ')' +
              '</option>'
            ).join('') +
          '</select>' +
          '<div style="font-size:11px;color:var(--sm-text-tertiary);margin-top:4px">' +
            'Link to a person entity for automatic arm/disarm based on presence' +
          '</div>' +
        '</div>' +

        '<div class="dialog-footer">' +
          '<button class="btn-dialog cancel" data-action="close-dialog">Cancel</button>' +
          '<button class="btn-dialog save" data-action="save-user">' + (isEdit ? 'Save Changes' : 'Save User') + '</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  async _saveUser() {
    const root = this.shadowRoot;
    const name = root.querySelector('#user-name')?.value?.trim();
    const code = root.querySelector('#user-code')?.value?.trim();
    const codeConfirm = root.querySelector('#user-code-confirm')?.value?.trim();
    const admin = root.querySelector('#user-admin')?.checked || false;
    const personEntity = root.querySelector('#user-person-entity')?.value || null;
    const isEdit = !!this._tempConfig?._userId;
    const userId = this._tempConfig?._userId || '';

    if (!name) { this._toast('Please enter a user name.', 'warning'); return; }

    if (isEdit) {
      // Edit mode: code is optional — only validate if provided
      if (code) {
        if (code.length < 4) { this._toast('Code must be at least 4 digits.', 'warning'); return; }
        if (code !== codeConfirm) { this._toast('Codes do not match.', 'warning'); return; }
        if (!/^[0-9]+$/.test(code)) { this._toast('Code must be numbers only.', 'warning'); return; }
      }
      // Build config — preserve existing code if not changed
      const existing = this._data.users[userId] || {};
      const config = {
        ...existing,
        name: name,
        admin: admin,
        person_entity: personEntity || null,
      };
      if (code) config.code = code;  // Only update code if a new one was entered

      const result = await this._callWS('save_user', { user_id: userId, config: config });
      if (result && result.success !== false) {
        this._showDialog = null;
        this._tempConfig = null;
        await this._loadData();
        this._toast('User updated', 'success');
      } else {
        this._toast('Could not update user: ' + (result?.error || 'Unknown error'), 'error');
      }
    } else {
      // Add mode: code is required
      if (!code || code.length < 4) { this._toast('Code must be at least 4 digits.', 'warning'); return; }
      if (code !== codeConfirm) { this._toast('Codes do not match.', 'warning'); return; }
      if (!/^[0-9]+$/.test(code)) { this._toast('Code must be numbers only.', 'warning'); return; }

      const config = {
        name: name,
        code: code,
        admin: admin,
        nfc_tag: null,
        person_entity: personEntity || null,
      };
      const result = await this._callWS('save_user', { user_id: '', config: config });
      if (result && result.success !== false) {
        this._showDialog = null;
        this._tempConfig = null;
        await this._loadData();
      } else {
        this._toast('Could not save user: ' + (result?.error || 'Unknown error'), 'error');
      }
    }
  }

  async _deleteUser(userId) {
    if (!await this._confirm('This user will be permanently removed.', 'Delete User?')) return;
    await this._callWS('delete_user', { user_id: userId });
    this._toast('User deleted', 'success');
    await this._loadData();
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
        <span class="badge accent">${enabledCount} active</span>
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
              <div class="module-name-area" data-module-expand="${key}">
                <div style="font-size:14px;font-weight:600">${def.name}</div>
                <div style="font-size:12px;color:var(--sm-text-secondary);display:flex;align-items:center;gap:6px">
                  ${def.desc}
                  ${healthBadge}
                </div>
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
                <div style="font-size:13px;font-weight:600">Cameras Configured</div>
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
            ` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No cameras configured yet</div>'}
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
                <div style="font-size:13px;font-weight:600">Locks Configured</div>
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
            ` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No locks configured yet</div>'}
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
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Configure thermostats for energy saving</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Thermostats Configured</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${thermostatCount} thermostat${thermostatCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${thermostatCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.thermostats.map(t => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${t.entity_id}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No thermostats configured yet</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-climate-config">${icon("settings")} Configure Thermostats</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Close</button>
          </div>
        </div>`;
    }
    
    // Siren module
    if (moduleKey === 'siren') {
      const sirenCount = moduleData.sirens?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Configure alarm sirens and patterns</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Sirens Configured</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${sirenCount} siren${sirenCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${sirenCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.sirens.map(s => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${s.entity_id}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No sirens configured yet</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-siren-config">${icon("settings")} Configure Sirens</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Close</button>
          </div>
        </div>`;
    }
    
    // Lights module
    if (moduleKey === 'lights') {
      const lightCount = moduleData.entities?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Configure light automation and effects</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Lights Configured</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${lightCount} light${lightCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${lightCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.entities.slice(0, 5).map(e => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${e}</span></div>`).join('')}
              ${lightCount > 5 ? `<div style="text-align:center;padding:6px;color:var(--sm-text-secondary);font-size:11px">+${lightCount - 5} more...</div>` : ''}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No lights configured yet</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-lights-config">${icon("settings")} Configure Lights</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Close</button>
          </div>
        </div>`;
    }
    
    // TTS module
    if (moduleKey === 'tts') {
      const speakerCount = moduleData.entities?.length || 0;
      return `
        <div style="padding:20px;background:rgba(0,0,0,0.2);border-top:1px solid var(--sm-border)">
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">${moduleDef.name} Configuration</div>
          <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:16px">Configure voice notifications</div>
          <div style="padding:16px;background:var(--sm-surface);border:1px solid var(--sm-border);border-radius:8px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
              
              <div><div style="font-size:13px;font-weight:600">Speakers Configured</div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">${speakerCount} speaker${speakerCount !== 1 ? 's' : ''}</div></div>
            </div>
            ${speakerCount > 0 ? `<div style="margin-top:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:6px">
              ${moduleData.entities.map(e => `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)">
                ${icon("chevron")}<span style="font-size:12px">${e}</span></div>`).join('')}
            </div>` : '<div style="text-align:center;padding:20px;color:var(--sm-text-tertiary);font-size:12px">No speakers configured yet</div>'}
          </div>
          <div style="display:flex;gap:8px">
            <button class="sm-btn primary" data-action="open-tts-config">${icon("settings")} Configure TTS</button>
            <button class="sm-btn default" data-cancel-module="${moduleKey}">Close</button>
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
                         font-family:monospace;font-size:12px;resize:vertical">${configJson}</textarea>
        
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
  _renderFuture() {
    const cameras = this._data.homeAloneCameras || [];
    const availableCameras = this._availableEntities.camera || [];

    return `
      <div class="section-header">
        <h3 class="section-title">Future & Advanced</h3>
        <span class="badge" style="background:var(--sm-purple-dim);color:var(--sm-purple)">Preview</span>
      </div>

      <div class="sm-card" style="padding:16px;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <div style="width:38px;height:38px;border-radius:10px;background:var(--sm-blue-dim);
                      display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--sm-blue)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/>
              <line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/>
              <line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/>
              <line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/>
              <line x1="17" y1="7" x2="22" y2="7"/>
            </svg>
          </div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600">Home Alone Monitor</div>
            <div style="font-size:12px;color:var(--sm-text-secondary);margin-top:2px">
              Simulate presence by activating cameras randomly while away
            </div>
          </div>
          <span class="badge" style="background:var(--sm-blue-dim);color:var(--sm-blue)">${cameras.length} camera${cameras.length !== 1 ? 's' : ''}</span>
        </div>

        <div style="font-size:12px;color:var(--sm-text-secondary);margin-bottom:10px">
          Select cameras to include in the Home Alone rotation:
        </div>

        ${cameras.length > 0 ? `
          <div style="margin-bottom:12px;padding:10px 12px;background:rgba(0,0,0,0.2);border-radius:8px">
            ${cameras.map(c => `
              <div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0">
                <span style="font-size:12px">${c.name || c.entity_id || c}</span>
                <button class="sm-btn ghost sm" style="padding:2px 8px;font-size:11px;color:var(--sm-danger)"
                        data-remove-home-alone="${c.entity_id || c}">Remove</button>
              </div>
            `).join('')}
          </div>
        ` : `
          <div style="padding:12px;text-align:center;color:var(--sm-text-tertiary);font-size:12px;margin-bottom:10px">
            No cameras selected yet
          </div>
        `}

        <div style="display:flex;gap:8px;align-items:center">
          <select class="sm-select" id="home-alone-camera-select" style="flex:1">
            <option value="">-- Add a camera --</option>
            ${availableCameras
              .filter(c => !cameras.some(x => (x.entity_id || x) === c.entity_id))
              .map(c => `<option value="${c.entity_id}">${c.name || c.entity_id}</option>`)
              .join('')}
          </select>
          <button class="sm-btn primary sm" data-action="add-home-alone-camera">Add</button>
        </div>

        ${cameras.length > 0 ? `
          <div style="margin-top:12px;display:flex;justify-content:flex-end">
            <button class="sm-btn default sm" data-action="save-home-alone-cameras">Save Camera List</button>
          </div>
        ` : ''}
      </div>

      <div class="sm-card" style="padding:20px;text-align:center;opacity:0.6">
        <div style="font-size:13px;color:var(--sm-text-secondary);margin-bottom:8px">Coming Soon</div>
        <div style="font-size:12px;color:var(--sm-text-tertiary)">
          Pet immunity &bull; AI person detection &bull; Cloud sync &bull; Voice control
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
  }

  // ===
  // TAB: TESTING
  // ===
  _renderTesting() {
    const health = this._data.health || {};
    const results = this._data.testResults || [];
    const lastResult = results[0] || null;
    const score = health.health_score ?? 100;
    const modules = health.modules || {};
    const batteries = health.batteries || [];
    const isRunning = this._testRunning || false;

    const scoreColor = score >= 90 ? "var(--sm-accent)" :
                       score >= 70 ? "var(--sm-warning)" : "var(--sm-danger)";

    return `
      <!-- Health Overview -->
      <div class="section-header">
        <h3 class="section-title">System Health</h3>
        <span class="badge accent">${score}%</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        <div style="padding:20px">
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px">
            <div style="width:64px;height:64px;border-radius:50%;
                 border:4px solid ${scoreColor};
                 display:flex;align-items:center;justify-content:center;
                 font-size:22px;font-weight:700;color:${scoreColor}">
              ${score}
            </div>
            <div>
              <div style="font-size:16px;font-weight:600">
                ${score >= 90 ? "All Systems Healthy" :
                  score >= 70 ? "Minor Issues Detected" : "Critical Issues Found"}
              </div>
              <div style="font-size:12px;color:var(--sm-text-secondary)">
                ${health.available_entities || 0}/${health.total_entities || 0} entities available
                &middot; ${health.low_battery_count || 0} low batteries
              </div>
            </div>
          </div>

          <!-- Module Status Grid -->
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px">
            ${Object.entries(modules).map(([id, m]) => {
              const color = !m.enabled ? "var(--sm-text-tertiary)" :
                            m.status === "ok" ? "var(--sm-accent)" : "var(--sm-danger)";
              const statusIcon = !m.enabled ? icon("circle") :
                                 m.status === "ok" ? icon("check") : icon("fail");
              return `
                <div style="padding:10px 12px;background:rgba(255,255,255,0.04);
                     border-radius:8px;border:1px solid ${color}22;
                     display:flex;align-items:center;gap:8px">
                  <span style="color:${color};font-weight:700;font-size:14px">${statusIcon}</span>
                  <div>
                    <div style="font-size:12px;font-weight:600;text-transform:capitalize">${id}</div>
                    <div style="font-size:11px;color:var(--sm-text-secondary)">
                      ${!m.enabled ? "disabled" : m.total === 0 ? "not configured" : m.available + "/" + m.total + " ok"}
                    </div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      </div>

      <!-- Test Controls -->
      <div class="section-header" style="margin-top:24px">
        <h3 class="section-title">Run Tests</h3>
        ${isRunning ? '<span class="badge entry">Running...</span>' : ''}
      </div>

      <div class="sm-card">
        <div class="test-grid-3">
          <button class="sm-btn primary" data-run-test="quick"
                  ${isRunning ? "disabled" : ""} style="padding:16px;flex-direction:column;gap:6px;
                  display:flex;align-items:center;justify-content:center">
            
            <span style="font-size:13px;font-weight:600">Quick Test</span>
            <span style="font-size:11px;opacity:0.7">Vital checks only</span>
          </button>
          <button class="sm-btn default" data-run-test="standard"
                  ${isRunning ? "disabled" : ""} style="padding:16px;flex-direction:column;gap:6px;
                  display:flex;align-items:center;justify-content:center">
            
            <span style="font-size:13px;font-weight:600">Standard Test</span>
            <span style="font-size:11px;opacity:0.7">Extended module tests</span>
          </button>
          <button class="sm-btn danger" data-run-test="full"
                  ${isRunning ? "disabled" : ""} style="padding:16px;flex-direction:column;gap:6px;
                  display:flex;align-items:center;justify-content:center;background:var(--sm-purple-dim);color:var(--sm-purple)">
            
            <span style="font-size:13px;font-weight:600">Full Test</span>
            <span style="font-size:11px;opacity:0.7">All configured systems</span>
          </button>
        </div>

        <!-- Module-specific test buttons -->
        <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:8px">
          ${Object.entries(modules).filter(([, m]) => m.enabled).map(([id]) => `
            <button class="sm-btn ghost-outlined" data-run-test="${id}"
                    ${isRunning ? "disabled" : ""}
                    style="text-transform:capitalize">
              Test ${id}
            </button>
          `).join("")}
        </div>
      </div>

      <!-- Last Test Result -->
      <div class="section-header" style="margin-top:24px">
        <h3 class="section-title">Last Test Run</h3>
        ${lastResult ? `<span class="badge ${lastResult.overall === "pass" ? "accent" :
          lastResult.overall === "warning" ? "entry" : "perimeter"}">${lastResult.overall.toUpperCase()}</span>` : ""}
      </div>

      ${lastResult ? this._renderTestResult(lastResult) : `
        <div class="sm-card" style="text-align:center;padding:32px;color:var(--sm-text-tertiary)">
          No tests run yet. Click a test button above to start.
        </div>
      `}

      <!-- Sensor Online/Offline Overview -->
      ${this._renderSensorStatus()}

      <!-- Battery Overview -->
      ${this._renderBatteryOverview(batteries)}

      <!-- Test History -->
      ${results.length > 1 ? `
        <div class="section-header" style="margin-top:24px">
          <h3 class="section-title">Test History</h3>
          <span class="badge actions">${results.length} results</span>
        </div>
        <div class="sm-card" style="padding:0;overflow:hidden">
          ${results.slice(0, 5).map((r, i) => `
            <div style="padding:12px 16px;display:flex;align-items:center;gap:12px;
                 ${i > 0 ? "border-top:1px solid var(--sm-border)" : ""}">
              <span style="font-size:16px">
                ${r.overall === "pass" ? icon("ok") : r.overall === "warning" ? icon("warn") : icon("fail")}
              </span>
              <div style="flex:1">
                <div style="font-size:13px;font-weight:600;text-transform:capitalize">${r.test_type} Test</div>
                <div style="font-size:11px;color:var(--sm-text-secondary)">${r.timestamp}</div>
              </div>
              <div style="text-align:right">
                <div style="font-size:12px;font-weight:600">
                  ${r.summary ? r.summary.passed : 0}/${(r.summary ? (r.summary.passed||0) + (r.summary.failed||0) + (r.summary.warned||0) : 0)} passed
                  ${r.summary?.warned ? `, ${r.summary.warned} warned` : ""}
                </div>
                <div style="font-size:11px;color:var(--sm-text-secondary)">${r.duration_seconds}s</div>
              </div>
            </div>
          `).join("")}
        </div>
      ` : ""}
    `;
  }

  _renderTestResult(result) {
    const mods = result.modules || {};
    const bats = result.batteries || {};
    const summary = result.summary || {};

    return `
      <div class="sm-card" style="padding:0;overflow:hidden">
        <div style="padding:16px 20px;background:${
          result.overall === "pass" ? "var(--sm-accent-dim)" :
          result.overall === "warning" ? "var(--sm-warning-dim)" : "var(--sm-danger-dim)"
        };display:flex;align-items:center;gap:12px">
          <span style="font-size:24px">
            ${result.overall === "pass" ? icon("ok") : result.overall === "warning" ? icon("warn") : icon("fail")}
          </span>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;text-transform:capitalize">
              ${result.test_type} Test &mdash; ${result.overall.toUpperCase()}
            </div>
            <div style="font-size:12px;opacity:0.8">
              ${result.timestamp} &middot; ${result.duration_seconds}s
              &middot; ${summary.passed || 0} passed, ${summary.failed || 0} failed${summary.warned ? ", " + summary.warned + " warned" : ""}, ${summary.skipped || 0} skipped
            </div>
          </div>
        </div>

        <div style="padding:12px 16px">
          ${Object.entries(mods).map(([id, m]) => {
            const color = m.status === "pass"    ? "var(--sm-accent)" :
                          m.status === "skipped" ? "var(--sm-text-tertiary)" :
                          m.status === "warning" ? "var(--sm-warning)" :
                          m.status === "fail"    ? "var(--sm-danger)" : "var(--sm-warning)";
            const statusText = m.status === "pass"    ? "PASS" :
                               m.status === "skipped" ? "SKIP" :
                               m.status === "warning" ? "WARN" :
                               m.status === "fail"    ? "FAIL" : "ERR";
            const detail = m.status === "warning" && m.reason === "no_entities"
              ? "Not configured - add entities in module settings"
              : m.test_result?.message || m.message || "";
            return `
              <div style="display:flex;align-items:center;gap:12px;padding:8px 0;
                   border-bottom:1px solid var(--sm-border)">
                <span style="color:${color};font-weight:700;font-size:11px;
                     min-width:40px">${statusText}</span>
                <div style="flex:1">
                  <span style="font-size:13px;font-weight:500;text-transform:capitalize">${id}</span>
                  ${m.entities_total != null ? `
                    <span style="font-size:11px;color:var(--sm-text-secondary);margin-left:8px">
                      ${m.entities_available}/${m.entities_total} entities
                    </span>
                  ` : ""}
                  ${detail ? `
                    <div style="font-size:11px;color:var(--sm-text-secondary);margin-top:2px">${detail}</div>
                  ` : ""}
                </div>
                ${m.reason && m.reason !== "no_entities" ? `
                  <span style="font-size:11px;color:var(--sm-text-tertiary)">${m.reason}</span>
                ` : ""}
              </div>
            `;
          }).join("")}

          ${bats.total > 0 ? `
            <div style="padding:10px 0;border-top:1px solid var(--sm-border);margin-top:4px">
              <div style="font-size:11px;font-weight:600;color:var(--sm-text-tertiary);
                   text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">
                Batteries (informational)
              </div>
              <div style="display:flex;gap:12px;font-size:12px">
                <span>${bats.total} total</span>
                ${bats.low_count > 0 ? `
                  <span style="color:var(--sm-warning)">${bats.low_count} low</span>
                ` : ""}
                ${bats.critical_count > 0 ? `
                  <span style="color:var(--sm-danger)">${bats.critical_count} critical</span>
                ` : ""}
                ${bats.low_count === 0 && bats.critical_count === 0 ? `
                  <span style="color:var(--sm-accent)">All OK</span>
                ` : ""}
              </div>
            </div>
          ` : ""}
        </div>
      </div>
    `;
  }

  _renderSensorStatus() {
    if (!this._hass) return '';
    
    // Discover all sensors that are configured in the alarm
    const configuredSensors = this._data.sensors || [];
    if (configuredSensors.length === 0) {
      return `
        <div class="section-header" style="margin-top:24px">
          <h3 class="section-title">Sensor Status</h3>
        </div>
        <div class="sm-card" style="text-align:center;padding:24px;color:var(--sm-text-tertiary)">
          No sensors configured. Enable sensors in the Sensors tab.
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
        state: state ? state.state : 'unknown',
      };
    });

    const online = sensorStatuses.filter(s => s.online).length;
    const offline = sensorStatuses.filter(s => !s.online).length;

    return `
      <div class="section-header" style="margin-top:24px">
        <h3 class="section-title">Sensor Status</h3>
        <span class="badge ${offline > 0 ? 'perimeter' : 'accent'}">${online}/${sensorStatuses.length} online</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        ${sensorStatuses.map((s, i) => `
          <div style="padding:10px 16px;display:flex;align-items:center;gap:12px;
               ${i > 0 ? "border-top:1px solid var(--sm-border)" : ""}">
            <div class="sensor-status-dot ${s.online ? 'online' : 'offline'}"></div>
            <div style="flex:1;min-width:0">
              <div style="font-size:12px;font-weight:500;white-space:nowrap;
                   overflow:hidden;text-overflow:ellipsis">${s.name}</div>
              <div style="font-size:11px;color:var(--sm-text-tertiary);font-family:monospace">${s.entity_id}</div>
            </div>
            <span class="badge ${s.sensor_type}">${s.sensor_type}</span>
            <span style="font-size:11px;font-weight:600;
                  color:${s.online ? 'var(--sm-accent)' : 'var(--sm-danger)'};
                  min-width:50px;text-align:right">
              ${s.online ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        `).join("")}
      </div>
    `;
  }

  _renderBatteryOverview(batteries) {
    if (!batteries || batteries.length === 0) {
      return `
        <div class="section-header" style="margin-top:24px">
          <h3 class="section-title">Battery Overview</h3>
        </div>
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

    return `
      <div class="section-header" style="margin-top:24px">
        <h3 class="section-title">Battery Overview</h3>
        <span class="badge accent">${batteries.length} tracked</span>
      </div>

      <div class="sm-card" style="padding:0;overflow:hidden">
        <!-- Low batteries (always visible) -->
        ${lowBatteries.length > 0 ? `
          ${lowBatteries.map((bat, i) => renderBatteryRow(bat, i, i > 0)).join("")}
        ` : `
          <div style="padding:16px;text-align:center;color:var(--sm-accent);font-size:13px;font-weight:600">
            All batteries above 50%
          </div>
        `}

        <!-- OK batteries (collapsible) -->
        ${okBatteries.length > 0 ? `
          <div style="border-top:1px solid var(--sm-border)">
            <div class="collapsible-header ${this._batteryOkExpanded ? 'expanded' : ''}"
                 data-action="toggle-battery-ok"
                 style="padding:12px 16px;margin:0">
              <span style="font-size:12px;color:var(--sm-text-secondary)">
                ${okBatteries.length} batteries above 50%
              </span>
              <span class="chevron">${icon("chevron")}</span>
            </div>
            <div class="collapsible-body ${this._batteryOkExpanded ? 'expanded' : ''}">
              ${okBatteries.map((bat, i) => renderBatteryRow(bat, i, true)).join("")}
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
    this._render();
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
    // Validation
    const invalid = this._tempConfig.cameras.filter(c => !c.entity_id);
    if (invalid.length > 0) {
      this._toast('Please select a camera entity for all cameras before saving.', 'warning'); return;
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
      this._toast('Camera configuration saved! Restart HA to activate.', 'success');
    } else {
      this._toast('Could not save: ' + (result?.error || 'Unknown error'), 'error');
    }
  }

  async _cancelDialog() {
    if (await this._confirm('Unsaved changes will be lost.', 'Discard Changes?')) {
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
            
            <div class="dialog-title">Camera Module Configuration</div>
            <button class="dialog-close" data-action="close-dialog"></button>
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
             Delete
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
    const invalid = this._tempConfig.locks.filter(l => !l.entity_id);
    if (invalid.length > 0) { this._toast('Please select an entity for all locks.', 'warning'); return; }
    const config = { enabled: true, locks: this._tempConfig.locks.map(l => ({ entity_id: l.entity_id, lock_on_arm: l.lock_on_arm, unlock_on_disarm: l.unlock_on_disarm, retry_attempts: l.retry_attempts, retry_delay: l.retry_delay })) };
    const result = await this._callWS('save_module', { module_id: 'lock', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Lock configuration saved! Restart HA to activate.', 'success');
    } else { this._toast('Save failed: ' + (result?.error || 'Unknown error'), 'error'); }
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
    <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:99999;backdrop-filter:blur(4px);">
      <div style="background:var(--sm-surface,#1c1c1e);border:1px solid var(--sm-border,#333);border-radius:16px;padding:28px;max-width:620px;width:92%;max-height:88vh;overflow-y:auto;position:relative;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          
          <div style="flex:1;font-size:18px;font-weight:600;color:var(--sm-text,#fff);">Lock Module Configuration</div>
          <button data-action="close-dialog" style="background:none;border:none;color:var(--sm-text,#fff);font-size:24px;cursor:pointer;line-height:1;"></button>
        </div>

        ${domainLocks.length > 0 ? `
        <div style="background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:8px;padding:12px;margin-bottom:16px;font-size:12px;color:#34c759;">
           Found ${domainLocks.length} lock entity(ies) in Home Assistant
        </div>` : `
        <div style="background:rgba(255,159,10,0.1);border:1px solid rgba(255,159,10,0.3);border-radius:8px;padding:12px;margin-bottom:16px;font-size:12px;color:#ff9f0a;">
          Â  No entities found in lock domain. Use manual search below to add any entity.
        </div>`}

        <button data-action="add-lock" style="width:100%;padding:10px;background:rgba(52,199,89,0.15);border:1px dashed #34c759;border-radius:8px;color:#34c759;cursor:pointer;font-size:14px;margin-bottom:16px;">
           Add Lock
        </button>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${locks.map((lock, idx) => `
          <div style="background:rgba(255,255,255,0.05);border:1px solid var(--sm-border,#333);border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;font-size:14px;color:var(--sm-text,#fff);">Lock ${idx + 1}</span>
              <button data-action="remove-lock" data-lock-id="${lock.id}" style="background:rgba(255,69,58,0.15);border:1px solid #ff453a;color:#ff453a;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;">Remove</button>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:6px;">Entity</label>
              ${lock.entity_id ? `<div style="padding:8px 12px;background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:6px;font-size:13px;color:#34c759;margin-bottom:6px;"> ${lock.entity_id}</div>` : ''}
              <div style="display:flex;gap:6px;align-items:center;margin-bottom:6px;">
                <input type="text" placeholder="Search entities (type 2+ chars)..." 
                  data-lock-search="${lock.id}"
                  style="flex:1;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;" 
                  value="${search}">
              </div>
              <select data-lock-id="${lock.id}" data-field="entity_id" style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="">-- Select entity --</option>
                ${filtered.map(e => `<option value="${e.entity_id}" ${e.entity_id === lock.entity_id ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('')}
                ${!filtered.find(e => e.entity_id === lock.entity_id) && lock.entity_id ? `<option value="${lock.entity_id}" selected>${lock.entity_id}</option>` : ''}
              </select>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:8px;">Behavior</label>
              <label style="display:flex;align-items:center;gap:8px;margin-bottom:8px;cursor:pointer;">
                <input type="checkbox" data-lock-id="${lock.id}" data-field="lock_on_arm" ${lock.lock_on_arm ? 'checked' : ''} style="width:16px;height:16px;cursor:pointer;">
                <span style="font-size:13px;color:var(--sm-text,#fff);">Lock when alarm is armed</span>
              </label>
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                <input type="checkbox" data-lock-id="${lock.id}" data-field="unlock_on_disarm" ${lock.unlock_on_disarm ? 'checked' : ''} style="width:16px;height:16px;cursor:pointer;">
                <span style="font-size:13px;color:var(--sm-text,#fff);">Unlock when alarm is disarmed</span>
              </label>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Retry attempts</label>
                <input type="number" min="0" max="10" data-lock-id="${lock.id}" data-field="retry_attempts" value="${lock.retry_attempts}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Retry delay (sec)</label>
                <input type="number" min="0" max="60" data-lock-id="${lock.id}" data-field="retry_delay" value="${lock.retry_delay}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
              </div>
            </div>
          </div>`).join('')}
        </div>

        <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;padding-top:16px;border-top:1px solid var(--sm-border,#333);">
          <button data-action="cancel-dialog" style="padding:10px 22px;background:rgba(255,255,255,0.08);border:1px solid var(--sm-border,#444);border-radius:8px;color:var(--sm-text,#fff);cursor:pointer;font-size:14px;">Cancel</button>
          <button data-action="save-lock-config" style="padding:10px 22px;background:#34c759;border:none;border-radius:8px;color:#000;cursor:pointer;font-size:14px;font-weight:600;">Save Configuration</button>
        </div>
      </div>
    </div>`;
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
    const invalid = this._tempConfig.thermostats.filter(t => !t.entity_id);
    if (invalid.length > 0) { this._toast('Please select an entity for all thermostats.', 'warning'); return; }
    const config = { enabled: true, thermostats: this._tempConfig.thermostats.map(t => ({ entity_id: t.entity_id, arm_mode: t.arm_mode, disarm_mode: t.disarm_mode, eco_temp: t.eco_temp, comfort_temp: t.comfort_temp })) };
    const result = await this._callWS('save_module', { module_id: 'climate', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Climate configuration saved! Restart HA to activate.', 'success');
    } else { this._toast('Save failed: ' + (result?.error || 'Unknown error'), 'error'); }
  }

  _renderClimateDialog() {
    const thermostats = this._tempConfig?.thermostats || [];
    const domainEntities = this._availableEntities.climate || [];
    const allEntities = this._allEntities || [];

    return `
    <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:99999;backdrop-filter:blur(4px);">
      <div style="background:var(--sm-surface,#1c1c1e);border:1px solid var(--sm-border,#333);border-radius:16px;padding:28px;max-width:640px;width:92%;max-height:88vh;overflow-y:auto;position:relative;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          
          <div style="flex:1;font-size:18px;font-weight:600;color:var(--sm-text,#fff);">Climate Module Configuration</div>
          <button data-action="close-dialog" style="background:none;border:none;color:var(--sm-text,#fff);font-size:24px;cursor:pointer;"></button>
        </div>

        ${domainEntities.length > 0 ? `
        <div style="background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:8px;padding:12px;margin-bottom:16px;font-size:12px;color:#34c759;">
           Found ${domainEntities.length} climate entity(ies) in Home Assistant
        </div>` : `
        <div style="background:rgba(255,159,10,0.1);border:1px solid rgba(255,159,10,0.3);border-radius:8px;padding:12px;margin-bottom:16px;font-size:12px;color:#ff9f0a;">
          Â  No climate entities found. Use manual search to add any entity.
        </div>`}

        <button data-action="add-climate" style="width:100%;padding:10px;background:rgba(52,199,89,0.15);border:1px dashed #34c759;border-radius:8px;color:#34c759;cursor:pointer;font-size:14px;margin-bottom:16px;">
           Add Thermostat
        </button>

        <div style="display:flex;flex-direction:column;gap:12px;">
          ${thermostats.map((t, idx) => `
          <div style="background:rgba(255,255,255,0.05);border:1px solid var(--sm-border,#333);border-radius:10px;padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
              <span style="font-weight:600;font-size:14px;color:var(--sm-text,#fff);">Thermostat ${idx + 1}</span>
              <button data-action="remove-climate" data-climate-id="${t.id}" style="background:rgba(255,69,58,0.15);border:1px solid #ff453a;color:#ff453a;border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;">Remove</button>
            </div>

            <div style="margin-bottom:12px;">
              <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:6px;">Entity</label>
              ${t.entity_id ? `<div style="padding:8px 12px;background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.3);border-radius:6px;font-size:13px;color:#34c759;margin-bottom:6px;"> ${t.entity_id}</div>` : ''}
              <input type="text" placeholder="Search entities (type 2+ chars for all, or leave blank for climate only)..."
                data-climate-search="${t.id}"
                style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;margin-bottom:6px;">
              <select data-climate-id="${t.id}" data-field="entity_id" style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                <option value="">-- Select entity --</option>
                ${domainEntities.map(e => `<option value="${e.entity_id}" ${e.entity_id === t.entity_id ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('')}
                ${!domainEntities.find(e => e.entity_id === t.entity_id) && t.entity_id ? `<option value="${t.entity_id}" selected>${t.entity_id}</option>` : ''}
              </select>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">When Armed</label>
                <select data-climate-id="${t.id}" data-field="arm_mode" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                  <option value="off" ${t.arm_mode==='off'?'selected':''}>Turn Off</option>
                  <option value="eco" ${t.arm_mode==='eco'?'selected':''}>Eco Mode</option>
                  <option value="away" ${t.arm_mode==='away'?'selected':''}>Away Mode</option>
                </select>
              </div>
              <div>
                <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">When Disarmed</label>
                <select data-climate-id="${t.id}" data-field="disarm_mode" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
                  <option value="heat" ${t.disarm_mode==='heat'?'selected':''}>Heat</option>
                  <option value="cool" ${t.disarm_mode==='cool'?'selected':''}>Cool</option>
                  <option value="auto" ${t.disarm_mode==='auto'?'selected':''}>Auto</option>
                  <option value="restore" ${t.disarm_mode==='restore'?'selected':''}>Restore Previous</option>
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

        <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;padding-top:16px;border-top:1px solid var(--sm-border,#333);">
          <button data-action="cancel-dialog" style="padding:10px 22px;background:rgba(255,255,255,0.08);border:1px solid var(--sm-border,#444);border-radius:8px;color:var(--sm-text,#fff);cursor:pointer;font-size:14px;">Cancel</button>
          <button data-action="save-climate-config" style="padding:10px 22px;background:#34c759;border:none;border-radius:8px;color:#000;cursor:pointer;font-size:14px;font-weight:600;">Save Configuration</button>
        </div>
      </div>
    </div>`;
  }

  // === Siren Config Dialog ===
  async _openSirenConfig() {
    await this._loadEntitiesByDomain('siren');
    
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
    const invalid = this._tempConfig.sirens.filter(s => !s.entity_id);
    if (invalid.length > 0) {
      this._toast('Please select a siren entity for all sirens before saving.', 'warning'); return;
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
      this._toast('Siren configuration saved! Restart HA to activate.', 'success');
    } else {
      this._toast('Could not save: ' + (result?.error || 'Unknown error'), 'error');
    }
  }

  _renderSirenDialog() {
    const sirens = this._tempConfig?.sirens || [];
    const availableSirens = this._availableEntities.siren || [];
    
    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            
            <div class="dialog-title">Siren Module Configuration</div>
            <button class="dialog-close" data-action="close-dialog"></button>
          </div>
          
          <button class="add-item-btn" data-action="add-siren">
            ${icon("plus")} Add Siren
          </button>
          
          <div class="item-list">
            ${sirens.length === 0 ? 
              '<div style="text-align:center;color:var(--sm-text-secondary);padding:20px;">No sirens configured.</div>' :
              sirens.map((s, idx) => this._renderSirenRow(s, idx)).join('')
            }
          </div>
          
          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Cancel</button>
            <button class="btn-dialog save" data-action="save-siren-config">Save Configuration</button>
          </div>
        </div>
      </div>
    `;
  }

  _renderSirenRow(siren, idx) {
    const availableSirens = this._availableEntities.siren || [];
    
    return `
      <div class="item-card">
        <div class="item-header">
          <div class="item-number">Siren ${idx + 1}</div>
          <button class="delete-item-btn" data-action="remove-siren" data-siren-id="${siren.id}">Delete</button>
        </div>
        
        <div class="form-group">
          <label class="form-label">Siren Entity</label>
          <input type="text" class="entity-search" placeholder="Search sirens..." data-search-target="siren-select-${siren.id}">
          <select class="form-select" id="siren-select-${siren.id}" data-siren-id="${siren.id}" data-field="entity_id">
            <option value="">-- Select Siren --</option>
            ${availableSirens.map(s => `
              <option value="${s.entity_id}" ${s.entity_id === siren.entity_id ? 'selected' : ''}>${s.name} (${s.entity_id})</option>
            `).join('')}
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label">Alarm Pattern</label>
          <select class="form-select" data-siren-id="${siren.id}" data-field="pattern">
            <option value="continuous" ${siren.pattern === 'continuous' ? 'selected' : ''}>Continuous</option>
            <option value="intermittent" ${siren.pattern === 'intermittent' ? 'selected' : ''}>Intermittent</option>
            <option value="rapid" ${siren.pattern === 'rapid' ? 'selected' : ''}>Rapid Beeps</option>
          </select>
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="form-group">
            <label class="form-label">Duration (seconds)</label>
            <input type="number" class="form-input" min="10" max="600" step="10" data-siren-id="${siren.id}" data-field="duration" value="${siren.duration}">
          </div>
          <div class="form-group">
            <label class="form-label">Volume (%)</label>
            <input type="number" class="form-input" min="0" max="100" step="5" data-siren-id="${siren.id}" data-field="volume" value="${siren.volume}">
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
    this._render();
  }

  _updateLightsField(field, value) {
    if (field === 'trigger_flash') this._tempConfig[field] = (value === true || value === 'true');
    else if (field === 'flash_duration') this._tempConfig[field] = parseInt(value) || 30;
    else this._tempConfig[field] = value;
  }

  async _saveLightsConfig() {
    if (this._tempConfig.entities.length === 0) { this._toast('Please add at least one light entity.', 'warning'); return; }
    const config = { enabled: true, entities: this._tempConfig.entities, arm_action: this._tempConfig.arm_action, disarm_action: this._tempConfig.disarm_action, trigger_flash: this._tempConfig.trigger_flash, flash_pattern: this._tempConfig.flash_pattern, flash_duration: this._tempConfig.flash_duration };
    const result = await this._callWS('save_module', { module_id: 'lights', config });
    if (result && result.success !== false) {
      this._showDialog = null; this._tempConfig = null; await this._loadData();
      this._toast('Lights configuration saved! Restart HA to activate.', 'success');
    } else { this._toast('Save failed: ' + (result?.error || 'Unknown error'), 'error'); }
  }

  _renderLightsDialog() {
    const selected = this._tempConfig?.entities || [];
    const domainLights = this._availableEntities.light || [];
    const allEntities = this._allEntities || [];
    const available = domainLights.filter(l => !selected.includes(l.entity_id));

    return `
    <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:99999;backdrop-filter:blur(4px);">
      <div style="background:var(--sm-surface,#1c1c1e);border:1px solid var(--sm-border,#333);border-radius:16px;padding:28px;max-width:640px;width:92%;max-height:88vh;overflow-y:auto;position:relative;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
          
          <div style="flex:1;font-size:18px;font-weight:600;color:var(--sm-text,#fff);">Lights Module Configuration</div>
          <button data-action="close-dialog" style="background:none;border:none;color:var(--sm-text,#fff);font-size:24px;cursor:pointer;"></button>
        </div>

        <div style="margin-bottom:16px;">
          <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:8px;">Selected Lights (${selected.length})</label>
          <div style="min-height:48px;padding:8px;background:rgba(255,255,255,0.04);border:1px solid var(--sm-border,#333);border-radius:8px;display:flex;flex-wrap:wrap;gap:6px;">
            ${selected.length === 0
              ? '<span style="color:#666;font-size:12px;padding:6px;">No lights selected yet</span>'
              : selected.map(eid => {
                  const e = domainLights.find(l => l.entity_id === eid);
                  const name = e?.name || eid;
                  return `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(52,199,89,0.15);border:1px solid rgba(52,199,89,0.4);border-radius:20px;font-size:12px;color:#34c759;">
                    ${name}
                    <button data-action="remove-light" data-entity="${eid}" style="background:none;border:none;color:#34c759;cursor:pointer;font-size:16px;line-height:1;padding:0;"></button>
                  </span>`;
                }).join('')
            }
          </div>
        </div>

        <div style="margin-bottom:16px;">
          <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:6px;">Add Light</label>
          <input type="text" id="lights-search-input" placeholder="Search entities (type 2+ chars for all, or leave blank for light domain)..."
            style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;margin-bottom:6px;">
          <select id="lights-add-select" data-action="add-light-from-select"
            style="width:100%;padding:8px 12px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
            <option value="">-- Select light to add --</option>
            ${available.map(e => `<option value="${e.entity_id}">${e.name} (${e.entity_id})</option>`).join('')}
          </select>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
          <div>
            <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">When Armed</label>
            <select data-lights-field="arm_action" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
              <option value="turn_off" ${this._tempConfig?.arm_action==='turn_off'?'selected':''}>Turn Off</option>
              <option value="leave" ${this._tempConfig?.arm_action==='leave'?'selected':''}>Leave As-Is</option>
            </select>
          </div>
          <div>
            <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">When Disarmed</label>
            <select data-lights-field="disarm_action" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
              <option value="restore" ${this._tempConfig?.disarm_action==='restore'?'selected':''}>Restore Previous</option>
              <option value="turn_on" ${this._tempConfig?.disarm_action==='turn_on'?'selected':''}>Turn On</option>
            </select>
          </div>
        </div>

        <label style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer;padding:10px;background:rgba(255,255,255,0.04);border-radius:8px;">
          <input type="checkbox" data-lights-field="trigger_flash" ${this._tempConfig?.trigger_flash?'checked':''} style="width:16px;height:16px;cursor:pointer;">
          <span style="font-size:13px;color:var(--sm-text,#fff);">Flash lights when alarm triggers</span>
        </label>

        ${this._tempConfig?.trigger_flash ? `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;margin-bottom:12px;">
          <div>
            <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Flash Pattern</label>
            <select data-lights-field="flash_pattern" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;">
              <option value="rapid" ${this._tempConfig?.flash_pattern==='rapid'?'selected':''}>Rapid</option>
              <option value="slow" ${this._tempConfig?.flash_pattern==='slow'?'selected':''}>Slow</option>
              <option value="intermittent" ${this._tempConfig?.flash_pattern==='intermittent'?'selected':''}>Intermittent</option>
            </select>
          </div>
          <div>
            <label style="display:block;font-size:12px;color:var(--sm-text-secondary,#999);margin-bottom:4px;">Duration (seconds)</label>
            <input type="number" min="5" max="300" data-lights-field="flash_duration" value="${this._tempConfig?.flash_duration||30}" style="width:100%;padding:8px;background:rgba(255,255,255,0.07);border:1px solid var(--sm-border,#444);border-radius:6px;color:var(--sm-text,#fff);font-size:13px;box-sizing:border-box;">
          </div>
        </div>` : ''}

        <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px;padding-top:16px;border-top:1px solid var(--sm-border,#333);">
          <button data-action="cancel-dialog" style="padding:10px 22px;background:rgba(255,255,255,0.08);border:1px solid var(--sm-border,#444);border-radius:8px;color:var(--sm-text,#fff);cursor:pointer;font-size:14px;">Cancel</button>
          <button data-action="save-lights-config" style="padding:10px 22px;background:#34c759;border:none;border-radius:8px;color:#000;cursor:pointer;font-size:14px;font-weight:600;">Save Configuration</button>
        </div>
      </div>
    </div>`;
  }

  // === TTS Config Dialog ===
  async _openTTSConfig() {
    await this._loadEntitiesByDomain('media_player');
    await this._loadEntitiesByDomain('tts');
    
    const currentConfig = this._data.modules.tts || {};
    this._tempConfig = {
      entities: currentConfig.entities || [],
      tts_service: currentConfig.tts_service || 'tts.cloud_say',
      language: currentConfig.language || 'da',
      volume: currentConfig.volume || 70,
      messages: currentConfig.messages || {
        armed: 'Alarm aktiveret',
        disarmed: 'Alarm deaktiveret',
        triggered: 'ALARM! Indtr detekteret!'
      }
    };
    
    this._showDialog = 'tts';
    this._render();
  }

  _addTTSEntity(entityId) {
    if (!this._tempConfig.entities.includes(entityId)) {
      this._tempConfig.entities.push(entityId);
      this._patchTTSDialog();
    }
  }

  _removeTTSEntity(entityId) {
    this._tempConfig.entities = this._tempConfig.entities.filter(e => e !== entityId);
    this._patchTTSDialog();
  }

  _patchTTSDialog() {
    // Surgical patch: only rebuild the speaker chips and dropdown — no full re-render
    const dialogMount = this.shadowRoot.getElementById('shell-dialog-mount');
    if (!dialogMount) { this._render(); return; }
    const availableMP = this._availableEntities.media_player || [];
    const availableTTS = this._availableEntities.tts || [];
    const allEntities = [...availableMP, ...availableTTS];
    const selectedEntities = this._tempConfig.entities;
    const unselected = allEntities.filter(e => !selectedEntities.includes(e.entity_id));
    // Patch chips
    const chipsEl = dialogMount.querySelector('[data-tts-chips]');
    if (chipsEl) {
      chipsEl.innerHTML = selectedEntities.length === 0
        ? '<div style="text-align:center;color:var(--sm-text-tertiary);padding:20px">No speakers selected</div>'
        : selectedEntities.map(entityId => {
            const entity = allEntities.find(e => e.entity_id === entityId);
            return `<span class="entity-chip">${entity?.name || entityId}<button data-action="remove-tts" data-entity="${entityId}"></button></span>`;
          }).join('');
      // Re-attach remove listeners
      chipsEl.querySelectorAll('[data-action="remove-tts"]').forEach(b => {
        b.addEventListener('click', () => this._removeTTSEntity(b.dataset.entity));
      });
    }
    // Patch dropdown
    const addSelect = dialogMount.querySelector('#tts-add-select');
    if (addSelect) {
      const currentVal = addSelect.value;
      addSelect.innerHTML = '<option value="">-- Select Speaker to Add --</option>' +
        unselected.map(e => `<option value="${e.entity_id}">${e.name} (${e.entity_id})</option>`).join('');
      addSelect.value = '';
    }
  }

  _updateTTSField(field, value) {
    if (field === 'volume') {
      this._tempConfig[field] = parseInt(value) || 0;
    } else if (field.startsWith('msg_')) {
      const msgType = field.replace('msg_', '');
      this._tempConfig.messages[msgType] = value;
    } else if (field === 'tts_service') {
      const customInput = this.shadowRoot.querySelector('#tts-service-custom');
      if (value === 'custom') {
        if (customInput) customInput.style.display = 'block';
      } else {
        if (customInput) customInput.style.display = 'none';
        this._tempConfig[field] = value;
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

  async _saveTTSConfig() {
    if (this._tempConfig.entities.length === 0) {
      this._toast('Please select at least one media player before saving.', 'warning'); return;
      return;
    }
    
    const config = {
      enabled: true,
      entities: this._tempConfig.entities,
      tts_service: this._tempConfig.tts_service || 'tts.cloud_say',
      language: this._tempConfig.language,
      volume: this._tempConfig.volume,
      messages: this._tempConfig.messages
    };
    
    const result = await this._callWS('save_module', {
      module_id: 'tts',
      config: config
    });
    
    if (result && result.success !== false) {
      this._showDialog = null;
      this._tempConfig = null;
      await this._loadData();
      this._toast('TTS configuration saved! Restart HA to activate.', 'success');
    } else {
      this._toast('Could not save: ' + (result?.error || 'Unknown error'), 'error');
    }
  }

  _renderTTSDialog() {
    const selectedEntities = this._tempConfig?.entities || [];
    const availableMP = this._availableEntities.media_player || [];
    const availableTTS = this._availableEntities.tts || [];
    const allEntities = [...availableMP, ...availableTTS];
    const unselected = allEntities.filter(e => !selectedEntities.includes(e.entity_id));
    
    return `
      <div class="config-dialog-overlay">
        <div class="config-dialog">
          <div class="dialog-header">
            
            <div class="dialog-title">TTS Module Configuration</div>
            <button class="dialog-close" data-action="close-dialog"></button>
          </div>
          
          <div class="form-group">
            <label class="form-label">Selected Speakers</label>
            <div data-tts-chips style="min-height:60px;padding:8px;background:rgba(255,255,255,0.05);border:1px solid var(--sm-border);border-radius:8px">
              ${selectedEntities.length === 0 ? 
                '<div style="text-align:center;color:var(--sm-text-tertiary);padding:20px">No speakers selected</div>' :
                selectedEntities.map(entityId => {
                  const entity = allEntities.find(e => e.entity_id === entityId);
                  return `<span class="entity-chip">${entity?.name || entityId}<button data-action="remove-tts" data-entity="${entityId}"></button></span>`;
                }).join('')
              }
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Add Speaker</label>
            <input type="text" class="entity-search" placeholder="Search speakers..." data-search-target="tts-add-select">
            <select class="form-select" id="tts-add-select" data-action="select-tts">
              <option value="">-- Select Speaker to Add --</option>
              ${unselected.map(e => `<option value="${e.entity_id}">${e.name} (${e.entity_id})</option>`).join('')}
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">TTS Service</label>
            <select class="form-select" data-tts-field="tts_service" id="tts-service-select">
              <option value="tts.cloud_say" ${(this._tempConfig?.tts_service||'tts.cloud_say')==='tts.cloud_say' ? 'selected' : ''}>tts.cloud_say (Nabu Casa Cloud)</option>
              <option value="tts.google_translate_say" ${this._tempConfig?.tts_service==='tts.google_translate_say' ? 'selected' : ''}>tts.google_translate_say (Google Translate)</option>
              <option value="tts.google_say" ${this._tempConfig?.tts_service==='tts.google_say' ? 'selected' : ''}>tts.google_say (Google Cast)</option>
              <option value="tts.piper" ${this._tempConfig?.tts_service==='tts.piper' ? 'selected' : ''}>tts.piper (Local/Piper)</option>
              <option value="tts.voice_rss" ${this._tempConfig?.tts_service==='tts.voice_rss' ? 'selected' : ''}>tts.voice_rss (VoiceRSS)</option>
              <option value="custom" ${this._tempConfig?.tts_service && !['tts.cloud_say','tts.google_translate_say','tts.google_say','tts.piper','tts.voice_rss'].includes(this._tempConfig.tts_service) ? 'selected' : ''}>Custom service...</option>
            </select>
            <input type="text" class="form-input" id="tts-service-custom"
              placeholder="e.g. tts.my_custom_say"
              style="margin-top:6px;display:${this._tempConfig?.tts_service && !['tts.cloud_say','tts.google_translate_say','tts.google_say','tts.piper','tts.voice_rss','',undefined,null].includes(this._tempConfig?.tts_service) ? 'block' : 'none'}"
              value="${!['tts.cloud_say','tts.google_translate_say','tts.google_say','tts.piper','tts.voice_rss',''].includes(this._tempConfig?.tts_service||'') ? (this._tempConfig?.tts_service||'') : ''}">
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="form-group">
              <label class="form-label">Language</label>
              <select class="form-select" data-tts-field="language">
                <option value="da" ${this._tempConfig?.language === 'da' ? 'selected' : ''}>Danish</option>
                <option value="en" ${this._tempConfig?.language === 'en' ? 'selected' : ''}>English</option>
                <option value="de" ${this._tempConfig?.language === 'de' ? 'selected' : ''}>German</option>
                <option value="sv" ${this._tempConfig?.language === 'sv' ? 'selected' : ''}>Swedish</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Volume: <span data-volume-label>${this._tempConfig?.volume || 70}</span>%</label>
              <input type="range" class="form-slider" min="0" max="100" step="5" data-tts-field="volume" value="${this._tempConfig?.volume || 70}">
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Armed Message</label>
            <input type="text" class="form-input" placeholder="e.g., Alarm aktiveret" data-tts-field="msg_armed" value="${this._tempConfig?.messages?.armed || ''}">
          </div>
          
          <div class="form-group">
            <label class="form-label">Disarmed Message</label>
            <input type="text" class="form-input" placeholder="e.g., Alarm deaktiveret" data-tts-field="msg_disarmed" value="${this._tempConfig?.messages?.disarmed || ''}">
          </div>
          
          <div class="form-group">
            <label class="form-label">Triggered Message</label>
            <input type="text" class="form-input" placeholder="e.g., ALARM! Indtr detekteret!" data-tts-field="msg_triggered" value="${this._tempConfig?.messages?.triggered || ''}">
          </div>
          
          <div class="dialog-footer">
            <button class="btn-dialog cancel" data-action="cancel-dialog">Cancel</button>
            <button class="btn-dialog save" data-action="save-tts-config">Save Configuration</button>
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
            this._toast(`${MODULE_DEFS[moduleKey].name} configuration saved! Restart HA to activate.`, 'success');
            this._expandedModule = null;
    this._showDialog = null;  // 'camera', 'lock', etc.
    this._tempConfig = null;  // Temporary config during editing
    this._availableEntities = {};  // Cache of entities by domain
            await this._loadData();
          } else {
            this._toast(`Could not save: ${result?.error || "Unknown error"}`, 'error');
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

    // Run test buttons (testing tab)
    root.querySelectorAll("[data-run-test]").forEach(btn => {
      btn.addEventListener("click", () => this._runTest(btn.dataset.runTest));
    });

    // Collapsible sections
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
          'This sensor will be hidden from the panel. You can restore it by editing the Secure Me configuration.',
          'Hide Sensor?'
        )) return;
        await this._callWS('hide_sensor', { entity_id: entityId, hidden: true });
        this._toast('Sensor hidden', 'success');
        await this._loadData();
      });
    });

    // Unmark environmental sensor (remove mis-classification)
    root.querySelectorAll("[data-unmark-env]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const entityId = btn.dataset.unmarkEnv;
        if (!await this._confirm(
          'This will remove the environmental classification and hide the sensor. It will no longer trigger alarm notifications.',
          'Remove Environmental Sensor?'
        )) return;
        await this._callWS('unmark_environmental', { entity_id: entityId });
        this._toast('Environmental sensor removed', 'success');
        await this._loadData();
      });
    });


    // Fake Presence toggle
    root.querySelectorAll("[data-action='toggle-fake-presence']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const current = this._data.fakePresence || false;
        const result = await this._callWS('set_fake_presence', { active: !current });
        if (result && result.active !== undefined) {
          this._data.fakePresence = result.active;
          this._render();
        } else {
          this._toast('Could not update Fake Presence', 'error');
        }
      });
    });

    // Future tab — Home Alone Monitor
    root.querySelectorAll("[data-action='add-home-alone-camera']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const sel = this.shadowRoot.querySelector('#home-alone-camera-select');
        if (!sel || !sel.value) return;
        const cameras = [...(this._data.homeAloneCameras || [])];
        const entityId = sel.value;
        if (!cameras.some(c => (c.entity_id || c) === entityId)) {
          cameras.push({ entity_id: entityId, name: sel.options[sel.selectedIndex]?.text || entityId });
          this._data.homeAloneCameras = cameras;
          this._render();
        }
      });
    });

    root.querySelectorAll("[data-remove-home-alone]").forEach(btn => {
      btn.addEventListener("click", () => {
        const entityId = btn.dataset.removeHomeAlone;
        this._data.homeAloneCameras = (this._data.homeAloneCameras || [])
          .filter(c => (c.entity_id || c) !== entityId);
        this._render();
      });
    });

    root.querySelectorAll("[data-action='save-home-alone-cameras']").forEach(btn => {
      btn.addEventListener("click", async () => {
        const cameras = (this._data.homeAloneCameras || []).map(c => c.entity_id || c);
        const result = await this._callWS('save_home_alone_cameras', { cameras });
        if (result) {
          this._toast('Home Alone cameras saved', 'success');
        } else {
          this._toast('Could not save cameras', 'error');
        }
      });
    });

    // Zone actions
    root.querySelectorAll("[data-action='add-zone']").forEach(btn => {
      btn.addEventListener("click", () => {
        this._tempConfig = { type: 'entry', modes: ['away','home','night'], sensors: [] };
        this._showDialog = 'zone';
        this._render();
      });
    });
    root.querySelectorAll("[data-action='save-zone']").forEach(btn => {
      btn.addEventListener("click", () => this._saveZone());
    });
    root.querySelectorAll("[data-delete-zone]").forEach(btn => {
      btn.addEventListener("click", () => this._deleteZone(btn.dataset.deleteZone));
    });

    // User actions
    root.querySelectorAll("[data-action='add-user']").forEach(btn => {
      btn.addEventListener("click", async () => {
        this._tempConfig = { admin: false };
        this._showDialog = 'user';
        if (!this._availablePersons) {
          try {
            const result = await this._callWS('get_persons');
            this._availablePersons = result?.persons || [];
          } catch(e) {
            this._availablePersons = [];
          }
        }
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
        };
        this._showDialog = 'user';
        if (!this._availablePersons) {
          try {
            const result = await this._callWS('get_persons');
            this._availablePersons = result?.persons || [];
          } catch(e) {
            this._availablePersons = [];
          }
        }
        this._render();
      });
    });
    root.querySelectorAll("[data-action='save-user']").forEach(btn => {
      btn.addEventListener("click", () => this._saveUser());
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
            this._toast("Import NFC tags - coming soon.", "info");
            break;
          case "add-notification":
            this._toast("Add Notification - coming soon.", "info");
            break;
          case "add-automation":
            this._toast("Add Automation - coming soon.", "info");
            break;
        }
      });
    });
    // === Dialog Event Listeners ===
    
    // Open camera config dialog
    const cameraConfigButtons = root.querySelectorAll("[data-action='open-camera-config']");
    console.log(' DEBUG: Found', cameraConfigButtons.length, 'camera config buttons');
    cameraConfigButtons.forEach(btn => {
      console.log(' DEBUG: Attaching listener to camera button');
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
        sel.innerHTML = '<option value="">-- Select entity --</option>' +
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
        sel.innerHTML = '<option value="">-- Select entity --</option>' +
          filtered.map(e => `<option value="${e.entity_id}" ${e.entity_id === currentVal ? 'selected' : ''}>${e.name} (${e.entity_id})</option>`).join('') +
          (!filtered.find(e => e.entity_id === currentVal) && currentVal ? `<option value="${currentVal}" selected>${currentVal}</option>` : '');
      });
    });

    // === Siren Module Handlers ===
    root.querySelectorAll("[data-action='open-siren-config']").forEach(b => b.addEventListener("click", () => this._openSirenConfig()));
    root.querySelectorAll("[data-action='add-siren']").forEach(b => b.addEventListener("click", () => this._addSirenRow()));
    root.querySelectorAll("[data-action='save-siren-config']").forEach(b => b.addEventListener("click", () => this._saveSirenConfig()));
    root.querySelectorAll("[data-action='remove-siren']").forEach(b => b.addEventListener("click", () => this._removeSirenRow(parseInt(b.dataset.sirenId))));
    root.querySelectorAll("select[data-siren-id], input[data-siren-id]").forEach(inp => {
      inp.addEventListener("change", () => this._updateSirenField(parseInt(inp.dataset.sirenId), inp.dataset.field, inp.value));
    });

    // === Lights Module Handlers ===
    root.querySelectorAll("[data-action='open-lights-config']").forEach(b => b.addEventListener("click", () => this._openLightsConfig()));
    root.querySelectorAll("[data-action='save-lights-config']").forEach(b => b.addEventListener("click", () => this._saveLightsConfig()));
    root.querySelectorAll("[data-action='remove-light']").forEach(b => b.addEventListener("click", () => this._removeLightEntity(b.dataset.entity)));

    // Lights: add from select
    const lightsAddSelect = root.querySelector("#lights-add-select");
    if (lightsAddSelect) {
      lightsAddSelect.addEventListener("change", () => {
        if (lightsAddSelect.value) { this._addLightEntity(lightsAddSelect.value); lightsAddSelect.value = ''; }
      });
    }
    // Lights: search filters select
    const lightsSearchInput = root.querySelector("#lights-search-input");
    if (lightsSearchInput) {
      lightsSearchInput.addEventListener("input", () => {
        const search = lightsSearchInput.value.toLowerCase();
        const allEntities = this._allEntities || [];
        const domainEntities = this._availableEntities.light || [];
        const selected = this._tempConfig?.entities || [];
        const filtered = search.length > 1
          ? allEntities.filter(e => !selected.includes(e.entity_id) && (e.name.toLowerCase().includes(search) || e.entity_id.toLowerCase().includes(search))).slice(0, 25)
          : domainEntities.filter(e => !selected.includes(e.entity_id));
        if (lightsAddSelect) {
          lightsAddSelect.innerHTML = '<option value="">-- Select light to add --</option>' +
            filtered.map(e => `<option value="${e.entity_id}">${e.name} (${e.entity_id})</option>`).join('');
        }
      });
    }
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

    // === TTS Module Handlers ===
    root.querySelectorAll("[data-action='open-tts-config']").forEach(b => b.addEventListener("click", () => this._openTTSConfig()));
    root.querySelectorAll("[data-action='save-tts-config']").forEach(b => b.addEventListener("click", () => this._saveTTSConfig()));
    root.querySelectorAll("[data-action='remove-tts']").forEach(b => b.addEventListener("click", () => this._removeTTSEntity(b.dataset.entity)));
    
    // Fix F2: Add handler for TTS speaker selection
    root.querySelectorAll("[data-action='select-tts']").forEach(sel => {
      sel.addEventListener("change", () => {
        if (sel.value) {
          this._addTTSEntity(sel.value);
          sel.value = ""; // Reset dropdown
        }
      });
    });
    
    root.querySelectorAll("[data-action='add-light-from-select']").forEach(sel => {
      sel.addEventListener("change", () => { if (sel.value) this._addLightEntity(sel.value); });
    });
    root.querySelectorAll("select[data-tts-field], input[data-tts-field]").forEach(inp => {
      inp.addEventListener("change", () => this._updateTTSField(inp.dataset.ttsField, inp.value));
    });
    root.querySelectorAll("input[type='range'][data-tts-field]").forEach(inp => {
      inp.addEventListener("input", () => {
        this._updateTTSField(inp.dataset.ttsField, inp.value);
        // Patch volume label surgically — no full re-render needed
        const label = root.querySelector('[data-volume-label]');
        if (label) label.textContent = inp.value + '%';
      });
    });
    const ttsCustomInput = root.querySelector('#tts-service-custom');
    if (ttsCustomInput) {
      ttsCustomInput.addEventListener("change", () => this._updateTTSCustomService(ttsCustomInput.value));
      ttsCustomInput.addEventListener("blur", () => this._updateTTSCustomService(ttsCustomInput.value));
    }

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
