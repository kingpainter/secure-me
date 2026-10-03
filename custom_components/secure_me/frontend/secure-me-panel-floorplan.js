/**
 * Floorplan Live-View Mixin (v2.2.0)
 *
 * Provides floorplan rendering, sensor state updates, and UI interactions
 * for all armed modes (away, home, night, vacation, home_alone).
 *
 * Extracted from secure-me-panel.js to isolate the floorplan feature
 * and reduce main panel file size.
 */

export const FloorplanMixin = (base) => class extends base {
  /**
   * Render the floorplan tab content.
   *
   * Shows:
   * - Message when disarmed
   * - Floorplan canvas with live sensor updates when armed + toggle enabled
   * - Toggle button to show/hide live-view (always visible when armed)
   */
  _renderFloorplan() {
    const isArmed = ["armed_away", "armed_home", "armed_night", "armed_vacation", "armed_home_alone"]
      .includes(this._alarmState);

    // Disarmed: show message
    if (!isArmed) {
      return `
        <div style="padding: 20px; text-align: center;">
          <div class="sm-card" style="border: none; background: rgba(107,114,128,0.1); padding: 32px;">
            <div style="font-size: 14px; color: var(--sm-text-dim, #999);">
              Etageplan er kun tilgængeligt når systemet er aktiveret.
            </div>
          </div>
        </div>
      `;
    }

    // Armed: show toggle + canvas (if enabled)
    const toggleLabel = this._fpLiveViewEnabled
      ? "Skjul direkte visning"
      : "Vis direkte visning";

    const toggleIcon = this._fpLiveViewEnabled
      ? "eye-off"
      : "eye";

    let canvasContent = "";
    if (this._fpLiveViewEnabled && this._data.floorplan?.image_url) {
      // Canvas will be rendered by the FloorplanMixin's internal methods
      // For now, show a placeholder or the actual canvas element
      canvasContent = `
        <div id="fp-canvas-container" style="
          margin-top: 16px;
          border-radius: 8px;
          overflow: hidden;
          background: #000;
          position: relative;
          aspect-ratio: ${this._data.floorplan.width || 1} / ${this._data.floorplan.height || 1};
        ">
          <canvas id="fp-canvas" width="${this._data.floorplan.width || 800}" height="${this._data.floorplan.height || 600}"
            style="display: block; width: 100%; height: 100%;"></canvas>
        </div>
      `;
    }

    return `
      <div style="padding: 16px 0;">
        <!-- Toggle button -->
        <div style="padding: 0 16px; margin-bottom: 16px;">
          <button
            id="fp-live-view-toggle"
            class="sm-button secondary"
            style="
              width: 100%;
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 8px;
              padding: 10px 16px;
              background: ${this._fpLiveViewEnabled ? "rgba(124,58,237,0.2)" : "rgba(107,114,128,0.2)"};
              border: 1px solid ${this._fpLiveViewEnabled ? "rgba(124,58,237,0.4)" : "rgba(107,114,128,0.4)"};
              color: var(--sm-text);
              border-radius: 6px;
              cursor: pointer;
              font-size: 14px;
              font-weight: 500;
              transition: all 0.2s ease;
            "
            title="${toggleLabel}"
          >
            <i class="icon">${this._getIcon(toggleIcon)}</i>
            <span>${toggleLabel}</span>
          </button>
        </div>

        <!-- Canvas (if enabled) -->
        ${canvasContent}

        <!-- Loading state -->
        ${this._fpLiveViewEnabled && !this._data.floorplan?.image_url ? `
          <div style="padding: 16px; text-align: center;">
            <div class="sm-card" style="border: none; background: rgba(107,114,128,0.1);">
              <div style="font-size: 14px; color: var(--sm-text-dim, #999);">
                Etageplan indlæses...
              </div>
            </div>
          </div>
        ` : ""}
      </div>
    `;
  }

  /**
   * Helper to get icon SVG or fallback
   * @param {string} iconName - Icon name (e.g., 'eye', 'eye-off')
   * @returns {string} SVG or placeholder
   */
  _getIcon(iconName) {
    const icons = {
      "eye": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 4C7 4 2.7 7.1 1 11.5c1.7 4.4 6 7.5 11 7.5s9.3-3.1 11-7.5C21.3 7.1 17 4 12 4m0 12.5c-2.8 0-5-2.2-5-5s2.2-5 5-5 5 2.2 5 5-2.2 5-5 5m0-8c-1.7 0-3 1.3-3 3s1.3 3 3 3 3-1.3 3-3-1.3-3-3-3z"/></svg>',
      "eye-off": '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 7c2.8 0 5 2.2 5 5 0 .7-.1 1.3-.3 1.9l3.8 3.8C21.6 15.8 23 14.3 23 12c0-6-4.5-11-11-11-1.8 0-3.5.5-5.1 1.3l3.1 3.1c.6-.2 1.2-.4 1.9-.4m0 1c-2.2 0-4 1.8-4 4 0 .7.2 1.3.5 1.9l5.4-5.4c-.6-.3-1.2-.5-1.9-.5M1 4.3L3.2 6.5c-1.2 1.5-2.2 3.3-2.8 5.2 1.8 3.6 5.2 6 9.1 6 1.5 0 3-.4 4.3-1.1l2.3 2.3c-1.5.5-3.1.8-4.7.8-6.6 0-12.1-4.5-13.6-10.8L1 4.3m10.6 9.1L12 12.2c0 .6.4 1 1 1 .6 0 1-.4 1-1l-.4-2.2z"/></svg>',
    };
    return icons[iconName] || "👁";
  }

  /**
   * Called when the live-view toggle button is clicked
   */
  _handleFpToggleClick(e) {
    e.preventDefault();
    this._toggleFpLiveView();
  }

  /**
   * Update live sensor markers on the canvas (targeted patch).
   * Called from update() when sensor states change during an armed mode.
   *
   * @returns {boolean} true if update was successful, false if canvas not ready
   */
  _fpUpdateLiveState() {
    const canvas = this.shadowRoot?.getElementById("fp-canvas");
    if (!canvas) return false;

    // TODO: Implement canvas rendering with actual sensor state updates
    // For now, return true to indicate canvas is ready
    return true;
  }

  /**
   * Attach floorplan tab event listeners (e.g., toggle button, canvas interactions)
   */
  _attachFloorplanListeners() {
    const root = this.shadowRoot;
    if (!root) return;

    // Live-view toggle button
    const toggleBtn = root.getElementById("fp-live-view-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", (e) => this._handleFpToggleClick(e));
    }

    // TODO: Canvas interaction listeners (room selection, opening editing, etc.)
  }

  /**
   * Detect if floorplan flyout is active (e.g., room editor, settings panel)
   * @returns {boolean}
   */
  _fpFlyoutActive() {
    // TODO: Implement based on actual UI state
    // For now, return false (no flyout active)
    return false;
  }
};
