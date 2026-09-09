// Spec wording: when data genuinely cannot be obtained, the UI says
// "Information unavailable" (never "not recorded", and never a fabricated
// value). Calculable values must be derived instead — see haversineKm /
// straightLineFromKathmandu below.
export const NOT_RECORDED = "Information unavailable"
export const UPDATE_SOON = "We will update soon"

const EMPTY_TOKENS = new Set(["", "undefined", "null", "nan", "none", "n/a", "—", "-"])

export function recordedText(value, empty = NOT_RECORDED) {
  if (value == null) return empty
  const text = String(value).trim()
  if (!text || EMPTY_TOKENS.has(text.toLowerCase())) return empty
  return text
}

export function isRecorded(value) {
  return recordedText(value, "") !== ""
}

export function hasValidCoords(lat, lng) {
  const latitude = Number(lat)
  const longitude = Number(lng)
  return Number.isFinite(latitude) && Number.isFinite(longitude)
    && latitude >= 26 && latitude <= 31
    && longitude >= 80 && longitude <= 89
}

export function formatCoords(lat, lng) {
  if (!hasValidCoords(lat, lng)) return null
  const latitude = Number(lat)
  const longitude = Number(lng)
  const ns = latitude >= 0 ? "N" : "S"
  const ew = longitude >= 0 ? "E" : "W"
  return `${Math.abs(latitude).toFixed(6)}° ${ns}, ${Math.abs(longitude).toFixed(6)}° ${ew}`
}

export function recordedCity(place = {}) {
  const city = recordedText(place.display_city || "", "")
  return city
}

export function placeLocationLabel(place = {}) {
  const city = recordedCity(place)
  const parts = [place.address, city || null, place.municipality, place.district, place.province]
    .map((value) => String(value || "").trim())
    .filter((value, index, all) => value && !EMPTY_TOKENS.has(value.toLowerCase()) && all.indexOf(value) === index)
  return parts.join(", ") || NOT_RECORDED
}

export function displayName(user) {
  if (!user) return "Traveler"
  return user.full_name || [user.first_name, user.last_name].filter(Boolean).join(" ").trim() || user.email || "Traveler"
}

export function unwrapFavoriteDestination(row) {
  if (!row) return null
  if (row.destination_detail && typeof row.destination_detail === "object") return row.destination_detail
  if (row.destination && typeof row.destination === "object" && row.destination.name) return row.destination
  return row.name ? row : null
}

// --- Golden-rule helpers (spec: never say "not recorded" when the value can
// be calculated/retrieved/derived; "Information unavailable" only when the
// data genuinely cannot be obtained) ------------------------------------------
export const INFO_UNAVAILABLE = "Information unavailable"

// Kathmandu Metropolitan City reference point (matches the internal geocoder
// index) used to DERIVE straight-line distances when no curated road distance
// is stored.
export const KATHMANDU_COORDS = { lat: 27.7172, lng: 85.324 }

export function haversineKm(lat1, lon1, lat2, lon2) {
  if (!hasValidCoords(lat1, lon1) || !hasValidCoords(lat2, lon2)) return null
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2
  return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)))
}

// Labelled straight-line distance from Kathmandu, or null when coordinates
// are missing (caller then falls back to INFO_UNAVAILABLE).
export function straightLineFromKathmandu(lat, lng) {
  const km = haversineKm(KATHMANDU_COORDS.lat, KATHMANDU_COORDS.lng, lat, lng)
  return km == null ? null : `≈ ${km} km (straight line)`
}

// --- Sidebar / header identity helpers (spec item 12) ------------------------
// The visible username must be a real display name — the email is a fallback
// of last resort — and the role must be a human label, never a raw enum.
const ROLE_LABELS = {
  tourist: "Traveller",
  traveller: "Traveller",
  guide: "Local Guide",
  local_guide: "Local Guide",
  admin: "Administrator",
  super_admin: "Administrator",
  tourism_admin: "Tourism Admin",
  content_moderator: "Content Moderator",
  district_manager: "District Manager",
  hotel_manager: "Hotel Manager",
  staff: "Staff",
  tourist_police: "Tourist Police",
  police: "Police",
  hospital_staff: "Hospital Staff",
  rescue_team: "Rescue Team",
  emergency_operator: "Emergency Operator",
  qa_tester: "QA Tester",
}

export function userDisplayName(user) {
  if (!user) return ""
  const full = [user.first_name, user.last_name].filter(Boolean).join(" ").trim()
  if (full) return full
  if (user.full_name && !String(user.full_name).includes("@")) return String(user.full_name).trim()
  if (user.username && !String(user.username).includes("@")) return String(user.username).trim()
  // Email of last resort: show only the local part, never the full address.
  if (user.email) return String(user.email).split("@")[0]
  return "Traveller"
}

export function userRoleLabel(user) {
  const raw = String(user?.role || "").toLowerCase()
  return ROLE_LABELS[raw] || (raw ? raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "Traveller")
}

/**
 * Minimum distance (km) from a point to a polyline of {lat, lng} waypoints.
 * Uses a local equirectangular projection per segment so the result is a
 * true point-to-segment distance, not just nearest-vertex distance.
 * Returns null when inputs are unusable — never a fabricated 0.
 */
export function minDistanceToPathKm(lat, lng, path) {
  if (!hasValidCoords(lat, lng)) return null
  if (!Array.isArray(path) || path.length === 0) return null
  const R = 6371
  const lat0 = Number(lat)
  const cosLat0 = Math.cos((lat0 * Math.PI) / 180)
  const toXY = (la, ln) => [
    (Number(ln) * Math.PI / 180) * R * cosLat0,
    (Number(la) * Math.PI / 180) * R,
  ]
  const pts = path
    .map((p) => {
      const la = p?.lat ?? (Array.isArray(p) ? p[0] : null)
      const ln = p?.lng ?? (Array.isArray(p) ? p[1] : null)
      return hasValidCoords(la, ln) ? toXY(la, ln) : null
    })
    .filter(Boolean)
  if (pts.length === 0) return null
  const [px, py] = toXY(lat, lng)
  if (pts.length === 1) return Math.hypot(px - pts[0][0], py - pts[0][1])
  let best = null
  for (let i = 0; i < pts.length - 1; i += 1) {
    const [ax, ay] = pts[i]
    const [bx, by] = pts[i + 1]
    const dx = bx - ax
    const dy = by - ay
    const len2 = dx * dx + dy * dy
    let t = len2 > 0 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0
    t = Math.max(0, Math.min(1, t))
    const d = Math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    if (best === null || d < best) best = d
  }
  return best
}
