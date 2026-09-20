import { useMemo } from "react"
import { Circle, MapContainer, Marker, Polyline, TileLayer, useMap } from "react-leaflet"
import L from "leaflet"
import { FiNavigation, FiRotateCcw, FiCheckCircle, FiX, FiMapPin } from "react-icons/fi"
import useTurnByTurn, { NAV_STATES } from "../../hooks/useTurnByTurn"

const userIcon = L.divIcon({
  className: "",
  html: '<div style="width:18px;height:18px;border-radius:50%;background:#2563eb;border:3px solid #fff;box-shadow:0 0 8px rgba(37,99,235,.8)"></div>',
  iconSize: [18, 18], iconAnchor: [9, 9],
})
const destIcon = L.divIcon({
  className: "",
  html: '<div style="font-size:22px;line-height:1">🏁</div>',
  iconSize: [22, 22], iconAnchor: [11, 11],
})

function Recenter({ position }) {
  const map = useMap()
  if (position) map.setView([position.latitude, position.longitude], Math.max(map.getZoom(), 15))
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
export default function LiveNavigationPanel({ destination, mode = "driving" }) {
  const { state, position, route, steps, progress, error, start, preview, end } =
    useTurnByTurn({ destination, mode })

  const line = useMemo(
    () => (route?.geometry || []).map(([la, ln]) => [la, ln]),
    [route],
  )
  const center = position
    ? [position.latitude, position.longitude]
    : destination
      ? [destination.latitude, destination.longitude]
      : [28.2096, 83.9856]

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
                className="text-xs font-bold px-3 py-1.5 rounded-xl bg-[#1D5146] text-white hover:opacity-90">
                Start navigation
              </button>
            </>
          )}
          {(state === NAV_STATES.NAVIGATING || state === NAV_STATES.REROUTING) && (
            <button onClick={end}
              className="text-xs font-bold px-3 py-1.5 rounded-xl bg-rose-600 text-white flex items-center gap-1">
              <FiX size={12} /> End
            </button>
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

      {(route || position) && (
        <div className="h-[320px] relative">
          <MapContainer center={center} zoom={14} className="h-full w-full" scrollWheelZoom>
            <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {line.length > 1 && <Polyline positions={line} pathOptions={{ color: "#1D5146", weight: 5 }} />}
            {destination && <Marker position={[destination.latitude, destination.longitude]} icon={destIcon} />}
            {position && (
              <>
                <Marker position={[position.latitude, position.longitude]} icon={userIcon} />
                {position.accuracy != null && (
                  <Circle center={[position.latitude, position.longitude]} radius={position.accuracy}
                    pathOptions={{ color: "#2563eb", weight: 1, fillOpacity: 0.08 }} />
                )}
                <Recenter position={position} />
              </>
            )}
          </MapContainer>
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
