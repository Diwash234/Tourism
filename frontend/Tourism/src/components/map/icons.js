import L from "leaflet"
import { getPlaceTypeIcon } from "../../utils/placeTypeIcons"
import { LOCATION_PIN_URL } from "../../utils/locationIcons"

/**
 * Leaflet map markers.
 *
 * Place markers are REAL icon pins: a coloured teardrop carrying the
 * place's actual icon artwork (Twemoji — Mozilla, CC-BY 4.0), e.g. a 🏥
 * pin for hospitals, 🏦 for banks, 🏨 for hotels, 🛕 for temples. The pin
 * SVGs are pre-generated (scripts/generate-location-pins.mjs) with the icon
 * embedded as a base64 data URI — Leaflet loads pin icons through <img>,
 * whose document context forbids external resource loads.
 */

const PIN_GEOMETRY = {
  iconSize: [32, 42],
  iconAnchor: [16, 42],
  popupAnchor: [0, -38],
}

const makePinIcon = (key, alt) =>
  new L.Icon({ iconUrl: LOCATION_PIN_URL(key), alt, ...PIN_GEOMETRY })

// Navigation arrow pointer (Google-Maps-style): emerald disc with a white
// directional triangle. Original SVG — no third-party icon assets.
export const makeUserArrowIcon = (deg = 0) => {
  const safeDeg = Number.isFinite(Number(deg)) ? Number(deg) : 0
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
    <circle cx="18" cy="18" r="15" fill="#059669" fill-opacity="0.22"/>
    <circle cx="18" cy="18" r="11.5" fill="#059669" stroke="#FFFFFF" stroke-width="2.5"/>
    <g transform="rotate(${safeDeg} 18 18)">
      <path d="M18 9.5 L24.5 25 L18 21.6 L11.5 25 Z" fill="#FFFFFF"/>
    </g>
  </svg>`
  return L.divIcon({
    className: "",
    html: `<div style="width:36px;height:36px;filter:drop-shadow(0 1px 3px rgba(2,44,34,.45))">${svg}</div>`,
    iconSize: [36, 36], iconAnchor: [18, 18],
  })
}

export const userIcon = makeUserArrowIcon(0)
export const destinationIcon = makePinIcon("destination", "Destination")
export const hospitalIcon = makePinIcon("hospital", "Hospital")
export const policeIcon = makePinIcon("police", "Police")
export const attractionIcon = makePinIcon("attraction", "Attraction")

const pinCache = new Map()

/** Leaflet icon for a destination-shaped object (memoized per type key). */
export const placeTypeIcon = (destination) => {
  const type = getPlaceTypeIcon(destination || {})
  // The generic fallback type is keyed "place" but carries the 📍 pin icon.
  const pinKey = type.key === "place" ? "pin" : type.key
  if (!pinCache.has(pinKey)) {
    pinCache.set(pinKey, makePinIcon(pinKey, type.label))
  }
  return pinCache.get(pinKey)
}
