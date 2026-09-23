#!/usr/bin/env node
/**
 * Generate Leaflet map pins with real location icons embedded.
 *
 * Why a generated file: Leaflet loads pin icons via <img src>, so the SVG
 * lives in an image context where Browsers forbid loading *external*
 * resources — the icon must be embedded as a base64 data URI inside the
 * pin SVG itself. We pre-generate one pin per place type at build/commit
 * time instead of doing this in the browser.
 *
 * Sources : public/icons/locations/*.png  (Twemoji — Mozilla, CC-BY 4.0)
 * Output  : public/icons/pins/pin-<key>.svg
 *
 * Run: node scripts/generate-location-pins.mjs
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const root = join(dirname(fileURLToPath(import.meta.url)), "..")
const ICON_DIR = join(root, "public/icons/locations")
const OUT_DIR = join(root, "public/icons/pins")

/**
 * Teardrop map pin (32x42) with a white circle carrying the place icon.
 * `pin` = the type's pin colour, `label` = accessible description.
 */
const pinSvg = (iconDataUrl, pin, label) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 42" width="32" height="42">
  <ellipse cx="16" cy="40" rx="10" ry="2.5" fill="#000000" fill-opacity="0.22"/>
  <path fill="${pin}" stroke="#FFFFFF" stroke-width="2" d="M16 1C7.716 1 1 7.716 1 16c0 11.4 15 25 15 25s15-13.6 15-25C31 7.716 24.284 1 16 1z"/>
  <circle cx="16" cy="15" r="9" fill="#FFFFFF"/>
  <image href="${iconDataUrl}" x="8.5" y="7.5" width="15" height="15"/>
  <title>${label}</title>
</svg>`

const PIN_COLORS = {
  waterfall: "#0891B2", lake: "#0284C7", hot_springs: "#E11D48",
  temple_hindu: "#EA580C", stupa: "#D97706", monastery: "#4F46E5",
  church: "#2563EB", heritage: "#B45309", museum: "#7C3AED",
  mountain: "#334155", viewpoint: "#059669", trekking: "#65A30D",
  hills: "#16A34A", cave: "#57534E", park: "#15803D",
  wildlife: "#CA8A04", forest: "#166534", river: "#0E7490",
  water_sports: "#0284C7", camping: "#4D7C0F", food: "#C2410C",
  tea_coffee: "#16A34A", orchard: "#E11D48", hotel: "#0369A1",
  village: "#78716C", festival: "#DB2777", market: "#BE185D",
  shopping: "#BE185D", snow: "#0EA5E9", sunset: "#F59E0B",
  rain_water: "#0284C7", walking: "#047857", family: "#E11D48",
  celebration: "#9333EA", money: "#15803D", hospital: "#DC2626",
  pharmacy: "#0D9488", police: "#4338CA", ambulance: "#B91C1C",
  attraction: "#D97706", compass: "#0F766E",
}

let count = 0
for (const file of readdirSync(ICON_DIR)) {
  if (!file.endsWith(".png")) continue
  const key = file.replace(/\.png$/, "")
  const b64 = readFileSync(join(ICON_DIR, file)).toString("base64")
  const dataUrl = `data:image/png;base64,${b64}`
  const color = PIN_COLORS[key] || "#D97706"
  writeFileSync(join(OUT_DIR, `pin-${key}.svg`), pinSvg(dataUrl, color, key))
  count += 1
}

// Special: the destination marker — same 📍 glyph, red (matches the old
// red "D" destination pin).
const destB64 = readFileSync(join(ICON_DIR, "pin.png")).toString("base64")
writeFileSync(
  join(OUT_DIR, "pin-destination.svg"),
  pinSvg(`data:image/png;base64,${destB64}`, "#DC2626", "destination")
)
count += 1
console.log(`Generated ${count} location pins in public/icons/pins/`)
