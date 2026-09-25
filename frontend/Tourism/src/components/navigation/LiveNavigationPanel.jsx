import { useEffect, useMemo, useRef, useState } from "react"
import { Circle, MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet"
import L from "leaflet"
import { FiNavigation, FiRotateCcw, FiCheckCircle, FiX, FiMapPin } from "react-icons/fi"
import useTurnByTurn, { NAV_STATES } from "../../hooks/useTurnByTurn"

import { makeUserArrowIcon } from "../map/icons"
// Arrow pointer rotates with the GPS compass heading (flaticon arrow-map
// style, original SVG). Static north-up arrow when heading is unknown.
const destIcon = L.divIcon({
  className: "",
  html: '<div style="font-size:22px;line-height:1">🏁</div>',
  iconSize: [22, 22], iconAnchor: [11, 11],
})

function Recenter({ trigger, position }) {
  // Recenters ONLY when the user presses the button (trigger changes) —
  // the map never fights the user by auto-panning on every GPS fix.
  const map = useMap()
  const first = useRef(true)
  useEffect(() => {
    if (!position) return
    if (first.current) {
      first.current = false
      map.setView([position.latitude, position.longitude], Math.max(map.getZoom(), 15))
      return
    }
    if (trigger > 0) map.setView([position.latitude, position.longitude], Math.max(map.getZoom(), 15))
  }, [trigger, position, map])
  return null
}

const fmtDist = (m) => (m == null ? "—" : m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`)
const fmtDur = (s) => (s == null ? "—" : s >= 60 ? `${Math.max(1, Math.round(s / 60))} min` : `${Math.round(s)} s`)
const fmtEta = (s) => {
  if (s == null) return "—"
  const d = new Date(Date.now() + s * 1000)
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

/**
 * LiveNavigationPanel — real road-routing turn-by-turn navigation.
 * Self-contained: its own map (route line, moving GPS marker, accuracy
 * circle, destination flag) + instruction/ETA cards driven by the
 * useTurnByTurn state machine (road-route + progress endpoints).
 */
const ALT_LABELS = [
  { icon: "⚡", name: "Faster" },
  { icon: "🏔", name: "Alternative" },
]

export default function LiveNavigationPanel({ destination, mode = "driving", stops = null }) {
  const {
    state, position, route, steps, progress, error, connectionLost,
    alternatives, legs, activeLeg, context,
    start, preview, end, selectAlternative, nextStop,
  } = useTurnByTurn({ destination, mode, stops })
  const [recenterTrigger, setRecenterTrigger] = useState(0)

  const line = useMemo(
    () => (route?.geometry || []).map(([la, ln]) => [la, ln]),
    [route],
  )

  // Rotate the arrow with the GPS compass heading when the device provides one.
  const userArrowIcon = useMemo(
    () => makeUserArrowIcon(position?.heading ?? 0),
    [position?.heading],
  )
  const center = position
    ? [position.latitude, position.longitude]
    : destination?.latitude != null && destination?.longitude != null
      ? [destination.latitude, destination.longitude]
      : null

  const busy = state === NAV_STATES.LOADING_ROUTE || state === NAV_STATES.GETTING_LOCATION
  const next = progress?.next_instruction

  return (
    <div className="card-base rounded-3xl border border-[#E5E0D5] overflow-hidden shadow-xl">
      <div className="p-4 flex flex-wrap items-center justify-between gap-2 border-b border-[#E5E0D5] bg-[#F7F8F5]">
        <div className="flex items-center gap-2">
          <FiNavigation className="text-[#1D5146]" />
          <h3 className="font-extrabold text-sm text-gray-900">Live Turn-by-Turn (road routing)</h3>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-[#1D5146]">{state}</span>
        </div>
        <div className="flex gap-2">
          {state === NAV_STATES.IDLE && (
            <>
              <button onClick={preview} disabled={busy}
                className="text-xs font-bold px-3 py-1.5 rounded-xl bg-white border border-gray-200 hover:bg-gray-50">
                Preview route
              </button>
              <button onClick={start}
                disabled={route?.navigation_grade === false}
                title={route?.navigation_grade === false ? "Estimated routes cannot be used for live navigation" : undefined}
                className="text-xs font-bold px-3 py-1.5 rounded-xl bg-[#1D5146] text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed">
                Start navigation
              </button>
            </>
          )}
          {(state === NAV_STATES.NAVIGATING || state === NAV_STATES.REROUTING) && (
            <>
              <button onClick={() => setRecenterTrigger((t) => t + 1)}
                className="text-xs font-bold px-3 py-1.5 rounded-xl bg-white border border-gray-200">
                Recenter
              </button>
              <button onClick={end}
                className="text-xs font-bold px-3 py-1.5 rounded-xl bg-rose-600 text-white flex items-center gap-1">
                <FiX size={12} /> End
              </button>
            </>
          )}
          {(state === NAV_STATES.ROUTE_PREVIEW || state === NAV_STATES.ARRIVED || state === NAV_STATES.ERROR) && (
            <button onClick={state === NAV_STATES.ROUTE_PREVIEW ? start : end}
              className="text-xs font-bold px-3 py-1.5 rounded-xl bg-[#1D5146] text-white">
              {state === NAV_STATES.ROUTE_PREVIEW ? "Start" : "Close"}
            </button>
          )}
        </div>
      </div>

      {error && <p className="px-4 py-2 text-xs font-semibold text-rose-600 bg-rose-50">{error}</p>}
      {connectionLost && state === NAV_STATES.NAVIGATING && (
        <p className="px-4 py-2 text-xs font-bold text-amber-700 bg-amber-50">
          Connection lost — retrying… (navigation continues offline on the current route)
        </p>
      )}
      {context?.safety?.warnings?.length > 0 && (
        <div className="px-4 py-2 bg-orange-50 border-b border-orange-100 space-y-1">
          {context.safety.warnings.slice(0, 3).map((w, i) => (
            <p key={i} className="text-[11px] font-semibold text-orange-700">
              ⚠️ {w.title} — {w.place} ({fmtDist(w.distance_from_route_m)} from route, {w.severity})
            </p>
          ))}
          <p className="text-[10px] text-orange-500">{context.safety.note}</p>
        </div>
      )}
      {context?.weather?.data && (
        <p className="px-4 py-1.5 text-[11px] font-semibold text-sky-700 bg-sky-50 border-b border-sky-100">
          🌤 {context.weather.data.weather?.[0]?.main ?? "Conditions"} ·{" "}
          {Math.round(context.weather.data.main?.temp ?? 0)}°C at route midpoint
        </p>
      )}
      {route && route.navigation_grade === false && (
        <div className="px-4 py-3 bg-amber-50 border-b border-amber-200">
          <p className="text-xs font-extrabold text-amber-800">⚠ Routing service unavailable</p>
          <p className="text-[11px] text-amber-700 mt-0.5">
            This is an estimated route ({route.source}) and is <b>not suitable for
            turn-by-turn navigation</b>. Preview and distances remain available.
          </p>
          <button onClick={preview}
            className="mt-1.5 text-[11px] font-bold px-3 py-1 rounded-lg bg-amber-600 text-white">
            Retry road routing
          </button>
        </div>
      )}
      {route?.note && (
        <p className="px-4 py-2 text-[11px] text-amber-700 bg-amber-50 border-b border-amber-100">{route.note}</p>
      )}

      {state === NAV_STATES.REROUTING && (
        <p className="px-4 py-2 text-xs font-bold text-blue-700 bg-blue-50 flex items-center gap-2">
          <FiRotateCcw className="animate-spin" /> Recalculating route…
        </p>
      )}
      {state === NAV_STATES.ARRIVED && (
        <div className="px-4 py-4 text-center bg-emerald-50">
          <FiCheckCircle className="mx-auto text-emerald-600 text-3xl" />
          <p className="font-extrabold text-emerald-800 mt-1">You arrived</p>
          <p className="text-xs text-emerald-700">{destination?.name}</p>
          <p className="text-[11px] text-emerald-600 mt-1">
            {fmtDist(route?.distance_m)} · {fmtDur(route?.duration_s)}
          </p>
        </div>
      )}

      {(route || position) && center && (
        <div className="h-[320px] relative">
          <MapContainer center={center} zoom={14} className="h-full w-full" scrollWheelZoom>
            <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {line.length > 1 && <Polyline positions={line} pathOptions={{ color: "#1D5146", weight: 5 }} />}
            {destination && <Marker position={[destination.latitude, destination.longitude]} icon={destIcon} />}
            {position && (
              <>
                <Marker position={[position.latitude, position.longitude]} icon={userArrowIcon} />
                {position.accuracy != null && (
                  <Circle center={[position.latitude, position.longitude]} radius={position.accuracy}
                    pathOptions={{ color: "#2563eb", weight: 1, fillOpacity: 0.08 }} />
                )}
                <Recenter trigger={recenterTrigger} position={position} />
              </>
            )}
          </MapContainer>
        </div>
      )}

      {(route || position) && !center && (
        <p className="m-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Map point unavailable. Add a recorded destination coordinate or allow location access to view the route.
        </p>
      )}

      {alternatives.length > 0 && state === NAV_STATES.ROUTE_PREVIEW && (
        <div className="p-4 space-y-2 border-t border-[#E5E0D5]">
          <p className="text-[10px] font-black uppercase text-gray-500">Route options</p>
          <button className="w-full text-left p-2.5 rounded-xl border-2 border-[#1D5146] bg-[#F7F8F5] flex justify-between items-center">
            <span className="text-xs font-bold text-gray-900">⭐ Recommended</span>
            <span className="text-[11px] text-gray-600">{fmtDist(route?.distance_m)} · {fmtDur(route?.duration_s)}</span>
          </button>
          {alternatives.slice(0, 2).map((alt, i) => (
            <button key={i} onClick={() => selectAlternative(i)}
              className="w-full text-left p-2.5 rounded-xl border border-gray-200 hover:border-[#1D5146] hover:bg-[#F7F8F5] flex justify-between items-center">
              <span className="text-xs font-bold text-gray-700">
                {ALT_LABELS[i]?.icon} {alt.duration_s < route?.duration_s ? "Faster" : ALT_LABELS[i]?.name}
              </span>
              <span className="text-[11px] text-gray-600">{fmtDist(alt.distance_m)} · {fmtDur(alt.duration_s)}</span>
            </button>
          ))}
          <p className="text-[10px] text-gray-400">Selecting an option replaces the highlighted route and steps.</p>
        </div>
      )}

      {legs && (
        <div className="px-4 py-2 text-[11px] font-bold text-gray-600 border-t border-[#E5E0D5]">
          Stop {activeLeg + 1} of {legs.length}: {legs[activeLeg]?.from?.name} → {legs[activeLeg]?.to?.name}
          {legs[activeLeg]?.source !== "osrm" && <span className="ml-2 text-amber-600">({legs[activeLeg]?.source})</span>}
        </div>
      )}

      {state === NAV_STATES.ARRIVED && legs && activeLeg < legs.length - 1 && (
        <div className="p-4 border-t border-[#E5E0D5] bg-[#F7F8F5]">
          <p className="text-[10px] font-black uppercase text-gray-500">Next stop</p>
          <p className="text-sm font-extrabold text-gray-900">{legs[activeLeg + 1]?.to?.name}</p>
          <p className="text-[11px] text-gray-600 mb-2">
            {fmtDist(legs[activeLeg + 1]?.distance_m)} · {fmtDur(legs[activeLeg + 1]?.duration_s)}
          </p>
          <button onClick={nextStop}
            className="text-xs font-bold px-3 py-1.5 rounded-xl bg-[#1D5146] text-white">
            Navigate to next stop →
          </button>
        </div>
      )}

      {(route || next) && state !== NAV_STATES.ARRIVED && (
        <div className="p-4 grid sm:grid-cols-2 gap-3">
          <div className="p-3 rounded-2xl bg-[#102A2E] text-white">
            <p className="text-[10px] font-black uppercase text-amber-300 flex items-center gap-1">
              <FiMapPin size={10} /> {next ? `Next in ${fmtDist(next.distance_m)}` : "Next instruction"}
            </p>
            <p className="text-sm font-bold leading-snug mt-1">
              {next?.instruction || steps[0]?.instruction || "Head to destination"}
            </p>
          </div>
          <div className="p-3 rounded-2xl bg-[#F7F8F5] border border-[#E5E0D5]">
            <p className="text-[10px] font-black uppercase text-gray-500">Remaining</p>
            <p className="text-sm font-extrabold text-gray-900">
              {fmtDist(progress?.distance_remaining_m ?? route?.distance_m)} ·{" "}
              {fmtDur(progress?.duration_remaining_s ?? route?.duration_s)}
            </p>
            <p className="text-[11px] text-gray-500 mt-0.5">
              ETA {fmtEta(progress?.duration_remaining_s ?? route?.duration_s)}
              {progress && ` · ${Math.round(progress.progress * 100)}% done`}
              {progress && !progress.on_route && " · off route"}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
