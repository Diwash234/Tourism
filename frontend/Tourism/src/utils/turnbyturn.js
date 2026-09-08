// Real turn-by-turn directions computed from the route's actual
// coordinate list (see route_engine.py's best_route() — route is a real
// list of {lat, lng} graph nodes along the shortest path, not a
// straight line). This is the standard technique GPS nav apps use:
// compute the compass bearing of each segment, then classify the
// change in bearing between consecutive segments as a turn.

function toRad(deg) {
  return (deg * Math.PI) / 180
}
function toDeg(rad) {
  return (rad * 180) / Math.PI
}

function bearing(a, b) {
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const dLng = toRad(b.lng - a.lng)
  const y = Math.sin(dLng) * Math.cos(lat2)
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng)
  return (toDeg(Math.atan2(y, x)) + 360) % 360
}

function haversineKm(a, b) {
  const R = 6371
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))
}

function classifyTurn(angleDelta) {
  // angleDelta normalized to -180..180, positive = turning right
  const abs = Math.abs(angleDelta)
  if (abs < 15) return { label: "Continue straight", icon: "straight" }
  if (abs < 45) return angleDelta > 0 ? { label: "Slight right", icon: "slight-right" } : { label: "Slight left", icon: "slight-left" }
  if (abs < 120) return angleDelta > 0 ? { label: "Turn right", icon: "right" } : { label: "Turn left", icon: "left" }
  return angleDelta > 0 ? { label: "Sharp right", icon: "sharp-right" } : { label: "Sharp left", icon: "sharp-left" }
}

/**
 * getTurnByTurnDirections(routeCoords)
 * routeCoords: [{lat, lng}, ...] — exactly what /navigation/route already
 * returns in response.data.route.
 * Returns: [{ instruction, distanceKm, icon }]
 */
export function getTurnByTurnDirections(routeCoords) {
  if (!Array.isArray(routeCoords) || routeCoords.length < 2) return []

  const steps = [{ instruction: "Start", distanceKm: 0, icon: "start" }]

  for (let i = 1; i < routeCoords.length - 1; i++) {
    const prev = routeCoords[i - 1]
    const curr = routeCoords[i]
    const next = routeCoords[i + 1]

    const bearingIn = bearing(prev, curr)
    const bearingOut = bearing(curr, next)
    let delta = bearingOut - bearingIn
    if (delta > 180) delta -= 360
    if (delta < -180) delta += 360

    const turn = classifyTurn(delta)
    const distanceKm = haversineKm(prev, curr)

    // Skip near-zero-distance duplicate nodes rather than emitting a
    // meaningless "continue straight for 0.00 km" step.
    if (distanceKm < 0.01) continue

    steps.push({ instruction: turn.label, distanceKm, icon: turn.icon })
  }

  const last = routeCoords[routeCoords.length - 2]
  const dest = routeCoords[routeCoords.length - 1]
  steps.push({
    instruction: "Arrive acd t destination",
    distanceKm: last ? haversineKm(last, dest) : 0,
    icon: "finish",
  })

  return steps
}