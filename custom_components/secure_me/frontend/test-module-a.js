// TEMPORARY TEST FILE -- safe to delete once the panel.js ES-module split
// feasibility test is done (see chat, 2026-08-23). Exports a constant and a
// function for test-module-b.js to import, to check whether Home Assistant's
// panel_custom module_url loading supports native ES module import/export
// between two separately-served static files, without a bundler.

export const TEST_MESSAGE = "ES module import chain works! Splitting panel.js is safe.";

export function testFunction() {
  return "...and function imports work too.";
}
