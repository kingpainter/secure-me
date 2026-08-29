/**
 * Secure Me - Panel Floorplan Mixin
 * VERSION: 1.5.5
 *
 * Pilot extraction (2026-08-29) for the ES-module split of
 * secure-me-panel.js -- see instructions_for_claude_secure_me.md.
 * Floorplan tab rendering, canvas drawing, room/opening editing, and
 * live-view sensor pins. Every method here is a class method reading
 * and writing shared panel state via `this` (properties initialized
 * in SecureMePanelCore's constructor, e.g. this._data,
 * this._floorplanEditMode, this._fpUndoStack) -- this mixin adds
 * behaviour only, it never re-initializes or duplicates state.
 *
 * Loaded as a native ES module (no bundler) via the panel_custom
 * module_url mechanism -- see panel.py for the static-path
 * registration this relies on.
 */
import { icon } from "./secure-me-panel-shared.js";

export const FloorplanMixin = (Base) => class extends Base {
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
};
