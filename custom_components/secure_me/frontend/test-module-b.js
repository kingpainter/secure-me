// TEMPORARY TEST FILE -- safe to delete once the panel.js ES-module split
// feasibility test is done (see chat, 2026-08-23). See test-module-a.js for
// context. If this panel shows the green success message below, native
// ES module import/export between two separately-served static files works
// through Home Assistant's panel_custom module_url loading, without a
// bundler -- meaning panel.js CAN be split into multiple files safely.

import { TEST_MESSAGE, testFunction } from "./test-module-a.js";

class SecureMeModuleTest extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <div style="padding:60px;font-family:sans-serif;text-align:center;">
        <h1 style="color:#22c55e;">${TEST_MESSAGE}</h1>
        <p>${testFunction()}</p>
        <p style="color:#888;margin-top:40px;">
          Denne test-side (og de tilhørende filer) kan slettes, nu hvor du har set denne besked.
        </p>
      </div>
    `;
    // eslint-disable-next-line no-console
    console.log("[SecureMe ES Module Test] SUCCESS:", TEST_MESSAGE, testFunction());
  }
}

if (!customElements.get("secure-me-module-test")) {
  customElements.define("secure-me-module-test", SecureMeModuleTest);
}
