/**
 * Format a distance in km as a Google-Maps-style string:
 *   - under 1 km  -> meters ("850 m")
 *   - otherwise   -> km with 1 decimal ("12.3 km")
 * Accepts numbers or numeric strings. Returns "—" for invalid input.
 */
export function formatDistance(km) {
  const value = Number(km)
  if (value === null || value === undefined || Number.isNaN(value)) return "—"
  if (value < 1) {
    return `${Math.max(1, Math.round(value * 1000))} m`
  }
  return `${value.toFixed(1)} km`
}

/**
 * Format a duration in minutes as "3 hr 20 min" or "45 min".
 */
export function formatDuration(min) {
  const m = Number(min)
  if (m === null || m === undefined || Number.isNaN(m)) return "—"
  if (m < 60) return `${Math.round(m)} min`
  const h = Math.floor(m / 60)
  const rem = Math.round(m % 60)
  return rem ? `${h} hr ${rem} min` : `${h} hr`
}
