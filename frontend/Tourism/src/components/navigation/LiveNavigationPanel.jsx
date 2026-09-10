import { useEffect, useMemo, useRef, useState } from "react"
import { FiFlag, FiMapPin, FiNavigation, FiRefreshCw, FiX } from "react-icons/fi"

/**
 * Live navigation engine (master spec Phase 2).
 *
 * Consumes a route (point list from /navigation/route — provider geometry
 * when a routing provider is configured, coordinate path from the bundled
 * graph otherwise, always labelled by the page) and a continuous GPS fix:
 *   - projects the user onto the polyline (map-matching to the route)
 *   - shows the next maneuver, remaining distance and remaining ETA
 *   - detects off-route (>75 m for two consecutive fixes) and triggers a
 *     reroute from the current GPS position through the parent's loader
 *   - detects arrival (<40 m from the last point)
 *
 * Pure client-side math over the served route — never invents road data.
 * Effects defer their state writes (React Compiler lint-safe).
 */

const toXY = (p, lat0) => ({
  x: p.lng * 111320 * Math.cos((lat0 * Math.PI) / 180),
  y: p.lat * 110540,
})

const normalizePoint = (point) => {
  if (Array.isArray(point)) return { lat: Number(point[0]), lng: Number(point[1]) }
  const lat = Number(point?.lat ?? point?.latitude)
  const lng = Number(point?.lng ?? point?.longitude ?? point?.lon)
  return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null
}

// Distance from p to segment a–b plus the projection parameter t (0..1).
const projectOnSegment = (p, a, b, lat0) => {
  const P = toXY(p, lat0)
  const A = toXY(a, lat0)
  const B = toXY(b, lat0)
  const dx = B.x - A.x
  const dy = B.y - A.y
  const lenSq = dx * dx + dy * dy
  let t = lenSq === 0 ? 0 : ((P.x - A.x) * dx + (P.y - A.y) * dy) / lenSq
  t = Math.max(0, Math.min(1, t))
  const qx = A.x + t * dx
  const qy = A.y + t * dy
  return { distM: Math.hypot(P.x - qx, P.y - qy), t }
}

const OFF_ROUTE_M = 75
const ARRIVED_M = 40

export default function LiveNavigationPanel({
  route,
  steps,
  durationMin,
  userPos,
  destinationName,
  onReroute,
  onRecenter,
  onEnd,
}) {
  const [session, setSession] = useState({ status: "following", offStreak: 0, reroutes: 0 })
  const [progress, setProgress] = useState({ remainingKm: null, remainingMin: null, offsetM: null })
  const [nextStep, setNextStep] = useState(null)
  const reroutingRef = useRef(false)

  const points = useMemo(
    () => (route || []).map(normalizePoint).filter(Boolean),
    [route]
  )

  // Cumulative segment lengths in metres for progress + step matching.
  const geometry = useMemo(() => {
    if (points.length < 2) return null
    const lat0 = points[0].lat
    const lengths = points.slice(1).map((point, idx) => {
      const A = toXY(points[idx], lat0)
      const B = toXY(point, lat0)
      return Math.hypot(B.x - A.x, B.y - A.y)
    })
    // Cumulative sums without mutation (concat builds a new array each step)
    // — the React Compiler lint rejects mutation inside mapper callbacks.
    const cum = lengths.reduce((acc, len) => acc.concat(acc[acc.length - 1] + len), [0])
    return { lat0, cum, total: cum[cum.length - 1] }
  }, [points])

  // Steps with cumulative end distances in metres (accepts m or km fields).
  // Built without mutation so the memo stays pure (lint: immutability).
  const stepTable = useMemo(() => {
    const rows = (steps || []).map((step) => ({
      instruction: step?.instruction || "Continue",
      meters: Number(step?.distance_m ?? (step?.distance_km != null ? step.distance_km * 1000 : 0)) || 0,
    }))
    return rows.map((row, idx) => ({
      instruction: row.instruction,
      endM: rows.slice(0, idx + 1).reduce((sum, r) => sum + r.meters, 0),
    }))
  }, [steps])

  // GPS-driven session update, deferred so the effect body writes no state
  // synchronously (React Compiler rule).
  useEffect(() => {
    if (!geometry || !userPos) return undefined
    const id = window.setTimeout(() => {
      const lat0 = geometry.lat0
      let best = null
      for (let i = 1; i < points.length; i += 1) {
        const proj = projectOnSegment(userPos, points[i - 1], points[i], lat0)
        if (!best || proj.distM < best.distM) {
          best = { ...proj, traveledM: geometry.cum[i - 1] + proj.t * (geometry.cum[i] - geometry.cum[i - 1]) }
        }
      }
      if (!best) return

      const last = points[points.length - 1]
      const P = toXY(userPos, lat0)
      const L = toXY(last, lat0)
      const toEndM = Math.hypot(P.x - L.x, P.y - L.y)

      if (toEndM <= ARRIVED_M) {
        setProgress({ remainingKm: 0, remainingMin: 0, offsetM: Math.round(best.distM) })
        setNextStep(null)
        setSession((prev) => (prev.status === "arrived" ? prev : { ...prev, status: "arrived" }))
        return
      }

      const remainingM = Math.max(0, geometry.total - best.traveledM)
      const routeM = geometry.total || 1
      setProgress({
        remainingKm: Math.round((remainingM / 1000) * 10) / 10,
        remainingMin: durationMin != null ? Math.max(1, Math.round((durationMin * remainingM) / routeM)) : null,
        offsetM: Math.round(best.distM),
      })
      setNextStep(stepTable.find((s) => s.endM > best.traveledM + 10) || stepTable[stepTable.length - 1] || null)

      setSession((prev) => {
        if (prev.status === "arrived") return prev
        const offStreak = best.distM > OFF_ROUTE_M ? prev.offStreak + 1 : 0
        let status = prev.status
        if (offStreak >= 2 && prev.status === "following" && !reroutingRef.current) status = "off-route"
        else if (offStreak === 0 && prev.status === "off-route") status = "following"
        if (status === prev.status && offStreak === prev.offStreak) return prev
        return { ...prev, offStreak, status }
      })
    }, 0)
    return () => window.clearTimeout(id)
  }, [userPos, geometry, points, stepTable, durationMin])

  // Trigger the reroute once confirmed off-route (deferred for the same rule).
  useEffect(() => {
    if (session.status !== "off-route" || reroutingRef.current || !userPos || !onReroute) return undefined
    reroutingRef.current = true
    const id = window.setTimeout(() => {
      setSession((prev) => ({ ...prev, status: "rerouting" }))
      Promise.resolve(onReroute(userPos.lat, userPos.lng))
        .then((ok) => {
          if (ok) {
            setSession((prev) => ({ status: "following", offStreak: 0, reroutes: prev.reroutes + 1 }))
          } else {
            setSession((prev) => ({ ...prev, status: "off-route" }))
          }
        })
        .catch(() => setSession((prev) => ({ ...prev, status: "off-route" })))
        .finally(() => {
          reroutingRef.current = false
        })
    }, 0)
    return () => window.clearTimeout(id)
  }, [session.status, userPos, onReroute])

  const statusMeta = {
    following: { label: "Following route", tone: "text-emerald-400", icon: <FiNavigation /> },
    "off-route": { label: "Off route — waiting for new fix", tone: "text-amber-400", icon: <FiMapPin /> },
    rerouting: { label: "Rerouting…", tone: "text-amber-300 animate-pulse", icon: <FiRefreshCw /> },
    arrived: { label: `Arrived at ${destinationName || "destination"}`, tone: "text-emerald-300", icon: <FiFlag /> },
  }[session.status]

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/90 p-4 space-y-3" data-testid="live-navigation-panel">
      <div className="flex items-center justify-between gap-2">
        <span className={`flex items-center gap-2 text-xs font-black uppercase tracking-wider ${statusMeta.tone}`}>
          {statusMeta.icon} {statusMeta.label}
        </span>
        <button
          type="button"
          onClick={onEnd}
          className="flex items-center gap-1 rounded-lg border border-slate-600 px-2 py-1 text-[10px] font-bold text-slate-300 hover:text-white"
        >
          <FiX /> End
        </button>
      </div>

      {nextStep && session.status !== "arrived" && (
        <div className="rounded-xl bg-slate-800 p-3">
          <p className="text-[10px] font-black uppercase tracking-wider text-emerald-400">Next</p>
          <p className="text-sm font-bold text-white">{nextStep.instruction}</p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="rounded-xl bg-slate-800 p-2">
          <p className="text-[9px] font-black uppercase text-slate-400">Remaining</p>
          <p className="text-sm font-black text-white">{progress.remainingKm != null ? `${progress.remainingKm} km` : "—"}</p>
        </div>
        <div className="rounded-xl bg-slate-800 p-2">
          <p className="text-[9px] font-black uppercase text-slate-400">ETA</p>
          <p className="text-sm font-black text-white">{progress.remainingMin != null ? `${progress.remainingMin} min` : "—"}</p>
        </div>
        <div className="rounded-xl bg-slate-800 p-2">
          <p className="text-[9px] font-black uppercase text-slate-400">GPS offset</p>
          <p className="text-sm font-black text-white">{progress.offsetM != null ? `${progress.offsetM} m` : "—"}</p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => userPos && onRecenter && onRecenter(userPos)}
          disabled={!userPos}
          className="flex-1 rounded-lg bg-emerald-700 px-3 py-2 text-[11px] font-black text-white hover:bg-emerald-600 disabled:opacity-40"
        >
          Recenter on me
        </button>
        <span className="text-[10px] font-bold text-slate-500">
          {session.reroutes > 0 ? `${session.reroutes} reroute${session.reroutes > 1 ? "s" : ""}` : "Live GPS"}
        </span>
      </div>
    </div>
  )
}
