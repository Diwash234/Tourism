#!/usr/bin/env node
/**
 * Generate the site's real UI icon set (professional duotone pictograms).
 *
 * These are original vector assets (no third-party license needed) in a
 * consistent style: soft tinted rounded square + bold glyph, matching the
 * app's Nepal-green palette. They replace the bare line icons for every
 * surface the owner asked about: sidebar, directions (turn-by-turn),
 * distance, route, navigation.
 *
 * Output:
 *   public/icons/ui/<name>.svg      — 24x24 sidebar/function icons
 *   public/icons/ui/turn-<key>.svg  — 48x48 turn-by-turn maneuver icons
 *
 * Run: node scripts/generate-ui-icons.mjs
 */
import { writeFileSync, mkdirSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const root = join(dirname(fileURLToPath(import.meta.url)), "..")
const OUT = join(root, "public/icons/ui")
mkdirSync(OUT, { recursive: true })

// Palette: {bg, fg} pairs matching the sidebar colour tokens.
const P = {
  forest: { bg: "#DCEDE4", fg: "#1D5146" },
  emerald: { bg: "#D7F2E6", fg: "#047857" },
  pink: { bg: "#FCE1EE", fg: "#BE185D" },
  orange: { bg: "#FDE8D7", fg: "#C2410C" },
  himalaya: { bg: "#E0E3FB", fg: "#4338CA" },
  saffron: { bg: "#FBEED3", fg: "#B45309" },
  red: { bg: "#FDE0E0", fg: "#B91C1C" },
  nepalred: { bg: "#FDE3E9", fg: "#BE123C" },
  sky: { bg: "#DBF1FC", fg: "#0369A1" },
  amber: { bg: "#FBF0D2", fg: "#92400E" },
  teal: { bg: "#D2F0EA", fg: "#0F766E" },
}

const dot = (x, y, r = 0.8, fill) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}"/>`

/** 24x24 duotone icon: tinted rounded square + glyph. */
const icon = (name, palette, glyph) => {
  const { bg, fg } = P[palette]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="6.5" fill="${bg}"/>
  <g fill="${fg}">${glyph(fg, bg)}</g>
</svg>`
  writeFileSync(join(OUT, `${name}.svg`), svg)
}

/** 48x48 maneuver icon: transparent background + bold arrow. */
const turn = (key, color, arrow) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <g fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">${arrow}</g>
</svg>`
  writeFileSync(join(OUT, `turn-${key}.svg`), svg)
}

// ---------------------------------------------------------------- sidebar
icon("house", "forest", (fg, bg) => `
  <path d="M6 11.8 12 6.8l6 5v6.4a1.3 1.3 0 0 1-1.3 1.3H7.3A1.3 1.3 0 0 1 6 18.2z" fill="${fg}"/>
  <rect x="10.4" y="13.6" width="3.2" height="5.9" rx="0.8" fill="${bg}"/>`)
icon("person", "himalaya", (fg) => `
  <circle cx="12" cy="9.6" r="3.1" fill="${fg}"/>
  <path d="M6.3 18.9c0-3.1 2.6-4.8 5.7-4.8s5.7 1.7 5.7 4.8v.4H6.3z" fill="${fg}"/>`)
icon("pin", "forest", (fg, bg) => `
  <path d="M12 5.2c-3.1 0-5.6 2.5-5.6 5.4 0 4 5.6 8.6 5.6 8.6s5.6-4.6 5.6-8.6c0-2.9-2.5-5.4-5.6-5.4z" fill="${fg}"/>
  <circle cx="12" cy="10.6" r="2.1" fill="${bg}"/>`)
icon("star", "saffron", (fg) => `
  <path d="M12 5.6l1.9 3.9 4.3.6-3.1 3 .7 4.3-3.8-2-3.8 2 .7-4.3-3.1-3 4.3-.6z" fill="${fg}"/>`)
icon("image", "pink", (fg, bg) => `
  <rect x="6" y="7.4" width="12" height="9.6" rx="1.6" fill="${fg}"/>
  <circle cx="9.4" cy="10.7" r="1.15" fill="${bg}"/>
  <path d="M6.6 16.2l3-3.5 2.3 2.5 2-2.2 3 3.2z" fill="${bg}"/>`)
icon("bar-chart", "orange", (fg) => `
  <rect x="6.4" y="12" width="2.9" height="6" rx="1" fill="${fg}"/>
  <rect x="10.6" y="8.4" width="2.9" height="9.6" rx="1" fill="${fg}"/>
  <rect x="14.8" y="10.4" width="2.9" height="7.6" rx="1" fill="${fg}"/>`)
icon("compass", "teal", (fg) => `
  <circle cx="12" cy="12" r="6.6" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M15 9l-1.8 4.2L9 15l1.8-4.2z" fill="${fg}"/>`)
icon("route", "emerald", (fg) => `
  <circle cx="7.6" cy="16.4" r="2.3" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <circle cx="16.4" cy="7.6" r="2.3" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M7.6 13.4v-2.6c0-2 1.6-3.6 3.6-3.6h2.4" fill="none" stroke="${fg}" stroke-width="1.7" stroke-dasharray="2.6 2.1" stroke-linecap="round"/>`)
icon("map", "forest", (fg) => `
  <path d="M6 8.1l4-1.6 4 1.6 4-1.6v9.4l-4 1.6-4-1.6-4 1.6z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M10 6.5v9.4M14 8.1v9.4" fill="none" stroke="${fg}" stroke-width="1.2"/>`)
icon("book", "himalaya", (fg) => `
  <path d="M12 7.6c-1.6-1.3-3.7-1.6-5.7-1.3v10.5c2-.3 4.1 0 5.7 1.3 1.6-1.3 3.7-1.6 5.7-1.3V6.3c-2-.3-4.1 0-5.7 1.3z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M12 7.6v10.5" fill="none" stroke="${fg}" stroke-width="1.4"/>`)
icon("calendar", "emerald", (fg) => `
  <rect x="6" y="7.4" width="12" height="10.6" rx="1.9" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M6 11h12M9.5 5.7v3M14.5 5.7v3" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linecap="round"/>
  ${dot(9.3, 14.2, 0.95, fg)}${dot(12, 14.2, 0.95, fg)}${dot(14.7, 14.2, 0.95, fg)}`)
icon("wallet", "emerald", (fg) => `
  <rect x="5.7" y="8.4" width="12.6" height="9.2" rx="2.1" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M14.6 11.8h3.7v3.4h-3.7a1.7 1.7 0 0 1 0-3.4z" fill="${fg}"/>`)
icon("calculator", "orange", (fg) => `
  <rect x="7" y="5.7" width="10" height="12.6" rx="1.9" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <rect x="9" y="7.9" width="6" height="2.7" rx="0.7" fill="${fg}"/>
  ${dot(9.9, 13.2, 0.8, fg)}${dot(12.1, 13.2, 0.8, fg)}${dot(14.3, 13.2, 0.8, fg)}
  ${dot(9.9, 15.9, 0.8, fg)}${dot(12.1, 15.9, 0.8, fg)}${dot(14.3, 15.9, 0.8, fg)}`)
icon("heart", "pink", (fg) => `
  <path d="M12 18.1c0 0-6.4-4.3-6.4-8.1 0-2.1 1.7-3.8 3.8-3.8 1.2 0 2.2.6 2.6 1.5.4-.9 1.4-1.5 2.6-1.5 2.1 0 3.8 1.7 3.8 3.8 0 3.8-6.4 8.1-6.4 8.1z" fill="${fg}"/>`)
icon("ticket", "saffron", (fg, bg) => `
  <rect x="4.8" y="8.8" width="14.4" height="7.4" rx="1.7" fill="none" stroke="${fg}" stroke-width="1.6"/>
  <circle cx="4.8" cy="12.5" r="1.3" fill="${bg}"/>
  <circle cx="19.2" cy="12.5" r="1.3" fill="${bg}"/>
  <path d="M13 9.2v6.6" fill="none" stroke="${fg}" stroke-width="1.3" stroke-dasharray="1.9 1.5"/>`)
icon("briefcase", "orange", (fg) => `
  <rect x="8.6" y="7.4" width="6.8" height="3" rx="1" fill="none" stroke="${fg}" stroke-width="1.5"/>
  <rect x="5.7" y="10.2" width="12.6" height="8.2" rx="1.9" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M5.7 14.1h12.6" fill="none" stroke="${fg}" stroke-width="1.3"/>`)
icon("building", "saffron", (fg) => `
  <rect x="7.4" y="5.8" width="9.2" height="12.8" rx="1.3" fill="none" stroke="${fg}" stroke-width="1.7"/>
  ${dot(9.9, 9, 0.75, fg)}${dot(12.1, 9, 0.75, fg)}${dot(14.3, 9, 0.75, fg)}
  ${dot(9.9, 11.6, 0.75, fg)}${dot(12.1, 11.6, 0.75, fg)}${dot(14.3, 11.6, 0.75, fg)}
  ${dot(9.9, 14.2, 0.75, fg)}${dot(14.3, 14.2, 0.75, fg)}
  <rect x="11.1" y="14.6" width="1.8" height="4" fill="${fg}"/>`)
icon("houses", "saffron", (fg) => `
  <path d="M4.8 13.2 8 10.6l3.2 2.6v4.2H4.8z" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M12.8 11.8 16 9.2l3.2 2.6v5H12.8z" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linejoin="round"/>`)
icon("warning", "red", (fg) => `
  <path d="M12 5.6 19.1 17.6H4.9z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M12 10.2v3.1" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linecap="round"/>
  ${dot(12, 15.4, 1, fg)}`)
icon("bell", "nepalred", (fg) => `
  <path d="M12 6a4.6 4.6 0 0 0-4.6 4.6c0 3-1.5 4.3-1.5 4.3h12.2s-1.5-1.3-1.5-4.3A4.6 4.6 0 0 0 12 6z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M10.4 16.9a1.6 1.6 0 0 0 3.2 0" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linecap="round"/>`)
icon("people", "emerald", (fg) => `
  <circle cx="9" cy="9.9" r="2.7" fill="none" stroke="${fg}" stroke-width="1.6"/>
  <path d="M4.7 18.1c0-2.5 2-4 4.3-4 1.1 0 2.2.3 3 1" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linecap="round"/>
  <circle cx="15.7" cy="9.4" r="2.2" fill="none" stroke="${fg}" stroke-width="1.5"/>
  <path d="M14.2 14.5c.5-.2 1-.3 1.5-.3 2.4 0 4.4 1.4 4.4 3.9" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linecap="round"/>`)
icon("signpost", "sky", (fg) => `
  <path d="M10.6 5.4v13.4" fill="none" stroke="${fg}" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M10.6 6.8h7a1 1 0 0 1 1 1v1.6a1 1 0 0 1-1 1h-7z" fill="none" stroke="${fg}" stroke-width="1.5"/>
  <path d="M10.6 11.4h-7a0 0 0 0 0 0 0v3.4h7z" fill="none" stroke="${fg}" stroke-width="1.5"/>`)
icon("clock", "himalaya", (fg) => `
  <circle cx="12" cy="12" r="6.6" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M12 8.4V12l2.6 1.9" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linecap="round"/>`)
icon("gear", "sky", (fg) => `
  <circle cx="12" cy="12" r="3.1" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <g fill="none" stroke="${fg}" stroke-width="2" stroke-linecap="round">
    <path d="M12 5.4v2M12 16.6v2M5.4 12h2M16.6 12h2M7.3 7.3l1.5 1.5M15.2 15.2l1.5 1.5M16.7 7.3l-1.5 1.5M8.8 15.2l-1.5 1.5"/>
  </g>`)
icon("shield", "emerald", (fg) => `
  <path d="M12 5.3l5.6 2.1v4.1c0 3.6-2.4 6.2-5.6 7.5-3.2-1.3-5.6-3.9-5.6-7.5V7.4z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>
  <path d="M9.7 12l1.7 1.7 3-3.3" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("translate", "himalaya", (fg) => `
  <path d="M4.8 14.2V7.4a1.6 1.6 0 0 1 1.6-1.6h8.2a1.6 1.6 0 0 1 1.6 1.6v4.6a1.6 1.6 0 0 1-1.6 1.6H9.4z" fill="none" stroke="${fg}" stroke-width="1.5"/>
  <path d="M9.4 13.6l-2.3 2.7" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linecap="round"/>
  <path d="M13.6 12.4l2 4.8 2-4.8M14.4 14.8h2.4" fill="none" stroke="${fg}" stroke-width="1.4" stroke-linecap="round"/>`)
icon("chat", "himalaya", (fg) => `
  <rect x="5" y="6.4" width="14" height="10" rx="3.1" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M9 16.4l-1.6 3 3.9-3" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linejoin="round"/>
  ${dot(9, 11.4, 1, fg)}${dot(12, 11.4, 1, fg)}${dot(15, 11.4, 1, fg)}`)
icon("bookmark", "saffron", (fg) => `
  <path d="M8 5.4h8a1.1 1.1 0 0 1 1.1 1.1V19l-5.1-3.3L6.9 19V6.5A1.1 1.1 0 0 1 8 5.4z" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linejoin="round"/>`)
icon("inbox", "sky", (fg) => `
  <path d="M5 13.1l2.2-5.6a1.6 1.6 0 0 1 1.5-1h8.6a1.6 1.6 0 0 1 1.5 1l2.2 5.6v3.4a1.6 1.6 0 0 1-1.6 1.6H6.6A1.6 1.6 0 0 1 5 16.5z" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linejoin="round"/>
  <path d="M5 13.1h4.1l1 2.1h3.8l1-2.1H19" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linejoin="round"/>`)
icon("robot", "himalaya", (fg) => `
  <rect x="6.4" y="9" width="11.2" height="8.6" rx="2.1" fill="none" stroke="${fg}" stroke-width="1.6"/>
  <path d="M12 9V6.6" fill="none" stroke="${fg}" stroke-width="1.5" stroke-linecap="round"/>
  ${dot(12, 5.3, 1.1, fg)}${dot(9.8, 12.7, 1.2, fg)}${dot(14.2, 12.7, 1.2, fg)}
  <path d="M9.6 15.4h4.8" fill="none" stroke="${fg}" stroke-width="1.3" stroke-linecap="round"/>`)
icon("card", "emerald", (fg) => `
  <rect x="5" y="7.4" width="14" height="9.2" rx="1.9" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M5 11h14" fill="none" stroke="${fg}" stroke-width="1.5"/>
  <path d="M7.6 14.1h4" fill="none" stroke="${fg}" stroke-width="1.4" stroke-linecap="round"/>`)
icon("list", "sky", (fg) => `
  <g fill="none" stroke="${fg}" stroke-width="1.7" stroke-linecap="round">
    <path d="M9.6 7.9h8.2M9.6 12h8.2M9.6 16.1h8.2"/>
  </g>
  ${dot(6.3, 7.9, 1, fg)}${dot(6.3, 12, 1, fg)}${dot(6.3, 16.1, 1, fg)}`)
icon("activity", "emerald", (fg) => `
  <path d="M5 12.2h3l2-4.6 3 9.2 2-4.6h4" fill="none" stroke="${fg}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("plus", "emerald", (fg) => `
  <path d="M12 7.4v9.2M7.4 12h9.2" fill="none" stroke="${fg}" stroke-width="2.1" stroke-linecap="round"/>`)
icon("check-square", "emerald", (fg) => `
  <rect x="5.4" y="5.4" width="13.2" height="13.2" rx="3.2" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M9 12.3l2.2 2.2 4-4.5" fill="none" stroke="${fg}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("x", "red", (fg) => `
  <path d="M8 8l8 8M16 8l-8 8" fill="none" stroke="${fg}" stroke-width="2.1" stroke-linecap="round"/>`)
icon("login", "forest", (fg) => `
  <path d="M14.3 7.4h3.1a1.6 1.6 0 0 1 1.6 1.6v6a1.6 1.6 0 0 1-1.6 1.6h-3.1" fill="none" stroke="${fg}" stroke-width="1.7" stroke-linecap="round"/>
  <path d="M5.4 12h9.2M11.4 8.9l3.1 3.1-3.1 3.1" fill="none" stroke="${fg}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("person-plus", "emerald", (fg) => `
  <circle cx="10" cy="9.9" r="2.9" fill="none" stroke="${fg}" stroke-width="1.6"/>
  <path d="M5.4 18.4c0-2.8 2.1-4.4 4.6-4.4 1.3 0 2.6.4 3.5 1.1" fill="none" stroke="${fg}" stroke-width="1.6" stroke-linecap="round"/>
  <path d="M17 6.4v5.2M14.4 9h5.2" fill="none" stroke="${fg}" stroke-width="1.8" stroke-linecap="round"/>`)
icon("chevron-down", "sky", (fg) => `
  <path d="M7 9.8l5 5 5-5" fill="none" stroke="${fg}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("chevron-right", "sky", (fg) => `
  <path d="M9.8 7l5 5-5 5" fill="none" stroke="${fg}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>`)
icon("quote", "pink", (fg) => `
  <path d="M7.2 8.3c-1.6.9-2.6 2.4-2.6 4.4v3.5h4.4v-5.2H6.7c0-1 .7-1.9 1.9-2.4z" fill="${fg}"/>
  <path d="M14.9 8.3c-1.6.9-2.6 2.4-2.6 4.4v3.5h4.4v-5.2h-2.3c0-1 .7-1.9 1.9-2.4z" fill="${fg}"/>`)
icon("hospital", "red", (fg) => `
  <rect x="6" y="6.2" width="12" height="11.6" rx="1.6" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <path d="M12 9.3v5.4M9.3 12h5.4" fill="none" stroke="${fg}" stroke-width="1.9" stroke-linecap="round"/>`)

// ------------------------------------------------- function / map icons
icon("distance", "amber", (fg) => `
  <rect x="4.4" y="9.4" width="15.2" height="5.6" rx="1.3" fill="none" stroke="${fg}" stroke-width="1.6"/>
  <g fill="none" stroke="${fg}" stroke-width="1.2">
    <path d="M7.6 9.4v2.4M10.4 9.4v3.4M13.2 9.4v2.4M16 9.4v3.4M18.8 9.4v2.4"/>
  </g>`)
icon("navigate", "sky", (fg) => `
  <path d="M12 5.2l6.8 13.4L12 15.1 5.2 18.6z" fill="${fg}"/>`)
icon("waypoint", "himalaya", (fg) => `
  <circle cx="12" cy="12" r="6.2" fill="none" stroke="${fg}" stroke-width="1.7"/>
  <circle cx="12" cy="12" r="2.3" fill="${fg}"/>`)

// ----------------------------------------------------- turn-by-turn set
const GREEN = "#047857"
const ORANGE = "#C2410C"
const RED = "#B91C1C"
const EMERALD = "#059669"

turn("start", GREEN, `
  <path d="M24 40V14"/>
  <path d="M14 22l10-10 10 10" fill="none"/>`)
turn("straight", GREEN, `
  <path d="M24 40V14"/>
  <path d="M14 22l10-10 10 10" fill="none"/>`)
turn("left", GREEN, `
  <path d="M30 42V26c0-3.9-3.1-7-7-7h-4"/>
  <path d="M8 19l13-8v16z" fill="${GREEN}" stroke="none"/>`)
turn("right", GREEN, `
  <path d="M18 42V26c0-3.9 3.1-7 7-7h4"/>
  <path d="M40 19L27 11v16z" fill="${GREEN}" stroke="none"/>`)
turn("sharp-left", ORANGE, `
  <path d="M33 42V34l-6.5-8"/>
  <path d="M16.5 12.4L30 18.3 19 26.9z" fill="${ORANGE}" stroke="none"/>`)
turn("sharp-right", ORANGE, `
  <path d="M15 42V34l6.5-8"/>
  <path d="M31.5 12.4L18 18.3 29 26.9z" fill="${ORANGE}" stroke="none"/>`)
turn("uturn", RED, `
  <path d="M31 42V22a7 7 0 0 0-14 0v12"/>
  <path d="M5 31l8 11 8-11z" fill="${RED}" stroke="none"/>`)
turn("arrive", EMERALD, `
  <path d="M15 42V8" stroke-width="4"/>
  <path d="M15 8h19l-5 6.5 5 6.5H15z" fill="${EMERALD}" stroke="none"/>`)

const files = new Set()
import { readdirSync } from "node:fs"
for (const f of readdirSync(OUT)) files.add(f)
console.log(`Generated ${files.size} UI icons in public/icons/ui/`)
