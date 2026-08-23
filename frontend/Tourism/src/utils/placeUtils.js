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

export function placeLocationLabel(place = {}) {
  const parts = [place.address, place.city, place.municipality, place.district, place.province]
    .map((value) => String(value || "").trim())
    .filter((value, index, all) => value && value.toLowerCase() !== "undefined" && value.toLowerCase() !== "null" && all.indexOf(value) === index)
  return parts.join(", ") || "Nepal"
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
