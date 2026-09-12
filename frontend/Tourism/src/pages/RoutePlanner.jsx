import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet"
import L from "leaflet"
import api from "../services/api"

/**
 * RoutePlanner — canonical source→destination routing on a real road network.
 *
 * Data flow (master spec: no fabrication, no substitution):
 *   place search (canonical DB records) → /api/v1/routes/ (Django resolves
 *   canonical ID → coordinates → admin-configured OSRM-protocol provider)
 *   → route geometry + steps → this Leaflet map.
 *
 * If the backend answers ROUTE_UNAVAILABLE we NEVER draw a straight line.
 * The user may opt in to the public OSRM demo server (clearly labelled);
 * if that also fails, we show an honest error and keep both markers visible.
 */

const NEPAL_BOUNDS = [[26.3, 79.9], [30.55, 88.35]]
const sourceIcon = L.divIcon({ className: "", html: '<div style="background:#2563eb;color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)">S</div>', iconSize: [28, 28], iconAnchor: [14, 14] })
const destIcon = L.divIcon({ className: "", html: '<div style="background:#dc2626;color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)">D</div>', iconSize: [28, 28], iconAnchor: [14, 14] })
const youIcon = L.divIcon({ className: "", html: '<div style="background:#0ea5e9;border:3px solid #fff;border-radius:50%;width:16px;height:16px;box-shadow:0 0 0 3px rgba(14,165,233,.35)"></div>', iconSize: [16, 16], iconAnchor: [8, 8] })
const poiIcon = (color) => L.divIcon({ className: "", html: `<div style="background:${color};border:2px solid #fff;border-radius:50%;width:14px;height:14px;box-shadow:0 1px 3px rgba(0,0,0,.4)"></div>`, iconSize: [14, 14], iconAnchor: [7, 7] })

const CATEGORY_COLORS = { hospital: "#dc2626", pharmacy: "#16a34a", atm: "#7c3aed", police: "#1d4ed8", hotel: "#ea580c", restaurant: "#ca8a04", attraction: "#0d9488", fuel: "#57534e", default: "#64748b" }

function FitBounds({ points }) {
  const map = useMap()
  useEffect(() => {
    const pts = (points || []).filter(Boolean)
    if (pts.length === 1) map.setView(pts[0], 13)
    else if (pts.length > 1) map.fitBounds(L.latLngBounds(pts), { padding: [40, 40] })
  }, [points, map])
  return null
}

function PlacePicker({ label, value, onChange, placeholder }) {
  const [q, setQ] = useState("")
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const debounce = useRef(null)

  const search = useCallback((term) => {
    clearTimeout(debounce.current)
    debounce.current = setTimeout(async () => {
      if (!term || term.length < 2) { setResults([]); return }
      try {
        const { data } = await api.get("/places/search/", { params: { q: term } })
        setResults((data.results || []).slice(0, 8))
        setOpen(true)
      } catch { setResults([]) }
    }, 350)
  }, [])

  return (
    <div className="relative" data-testid={`picker-${label}`}>
      <label className="text-xs font-semibold text-slate-500 uppercase">{label}</label>
      <input
        value={value ? `${value.name} (${value.latitude.toFixed(6)}, ${value.longitude.toFixed(6)})` : q}
        onChange={(e) => { setQ(e.target.value); onChange(null); search(e.target.value) }}
        placeholder={placeholder}
        className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
      />
      {value && (
        <div className="text-[11px] text-slate-500 mt-1" data-testid={`${label}-coords`}>
          {value.canonical ? `Canonical ID: ${value.canonical} · ` : ""}
          Lat {value.latitude.toFixed(6)}, Lng {value.longitude.toFixed(6)}
        </div>
      )}
      {open && results.length > 0 && (
        <ul className="absolute z-[1000] w-full bg-white border border-slate-200 rounded-lg shadow-lg mt-1 max-h-64 overflow-auto">
          {results.map((r) => (
            <li key={r.id}>
              <button
                className="w-full text-left px-3 py-2 hover:bg-emerald-50 text-sm"
                onClick={() => {
                  onChange({
                    name: r.name, latitude: r.latitude, longitude: r.longitude,
                    category: r.category, source: r.source, rawId: r.id,
                    canonical: r.destination_id ? `destination:${r.destination_id}` : r.id,
                    routeParams: r.destination_id
                      ? { destination_id: r.destination_id }
                      : r.id?.startsWith("osm-") ? { destination_id: r.id.slice(4), destination_type: "service" } : null,
                  })
                  setOpen(false); setQ("")
                }}
              >
                <span className="font-medium">{r.name}</span>
                <span className="text-slate-400 text-xs block">{r.category} · {r.address} · {r.latitude?.toFixed(5)}, {r.longitude?.toFixed(5)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function RoutePlanner() {
  const [source, setSource] = useState(null)
  const [destination, setDestination] = useState(null)
  const [you, setYou] = useState(null)
  const [route, setRoute] = useState(null)
  const [routeError, setRouteError] = useState(null)
  const [routeEngine, setRouteEngine] = useState(null)
  const [loading, setLoading] = useState(false)
  const [nearby, setNearby] = useState([])
  const [category, setCategory] = useState("")
  const [demoOffer, setDemoOffer] = useState(false)

  const useMyLocation = () => {
    if (!navigator.geolocation) { setRouteError("Geolocation is not supported by this browser; pick a source manually."); return }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const p = { name: "Your Location", latitude: pos.coords.latitude, longitude: pos.coords.longitude }
        setYou(p); setSource(p)
      },
      () => setRouteError("Location permission denied — choose a source place manually. No default location is assumed."),
    )
  }

  const fetchRoute = useCallback(async (src, dst, opts = {}) => {
    if (!src || !dst) return
    setLoading(true); setRouteError(null); setDemoOffer(false)
    try {
      const params = {
        source_lat: src.latitude, source_lng: src.longitude,
        destination_lat: dst.latitude, destination_lng: dst.longitude,
        ...(src.routeParams?.source_id ? { source_id: src.routeParams.source_id } : {}),
        ...(dst.routeParams?.destination_id ? { destination_id: dst.routeParams.destination_id, ...(dst.routeParams.destination_type ? { destination_type: dst.routeParams.destination_type } : {}) } : {}),
      }
      const { data } = await api.get("/routes/", { params })
      // geometry: GeoJSON [lng, lat] pairs → Leaflet [lat, lng]
      setRoute((data.geometry || []).map(([lng, lat]) => [lat, lng]))
      setRouteEngine({ label: "Backend routing provider (OSRM protocol)", info: data, steps: data.steps || [] })
    } catch (err) {
      const data = err?.response?.data
      setRoute(null); setRouteEngine(null)
      if (data?.route_status === "ROUTE_UNAVAILABLE") {
        setRouteError(`Route could not be calculated: ${data.reason} No straight-line route is shown.`)
        if (!opts.triedDemo) setDemoOffer(true)
      } else {
        setRouteError(data?.detail || data?.route_status || "Routing request failed.")
      }
    } finally { setLoading(false) }
  }, [])

  const tryPublicDemo = async () => {
    setLoading(true); setDemoOffer(false); setRouteError(null)
    try {
      const url = `https://router.project-osrm.org/route/v1/driving/${source.longitude},${source.latitude};${destination.longitude},${destination.latitude}?overview=full&geometries=geojson&steps=true`
      const res = await fetch(url)
      const data = await res.json()
      const r = data?.routes?.[0]
      if (!r) throw new Error("no route")
      setRoute((r.geometry.coordinates || []).map(([lng, lat]) => [lat, lng]))
      setRouteEngine({
        label: "Public OSRM demo server (router.project-osrm.org) — external, unverified, for demonstration",
        info: { distance_meters: Math.round(r.distance), duration_seconds: Math.round(r.duration) },
        steps: (r.legs?.[0]?.steps || []).map((s) => ({
          instruction: `${(s.maneuver?.type || "").replace("_", " ")}${s.maneuver?.modifier ? " " + s.maneuver.modifier : ""}${s.name ? " onto " + s.name : ""}`.trim(),
          distance_m: Math.round(s.distance || 0), road: s.name || null,
        })),
      })
    } catch {
      setRouteError("The public OSRM demo server could not calculate this route either. Route unavailable — markers remain visible.")
    } finally { setLoading(false) }
  }

  // Deferred one tick: fetchRoute/loadNearby flip loading/list state
  // synchronously at the start, and doing that inside the effect body
  // triggers a cascading render (react-hooks/set-state-in-effect). A 0ms
  // timeout moves the kick-off off the render pass; behaviour is identical.
  useEffect(() => {
    if (!source || !destination) return
    const t = setTimeout(() => fetchRoute(source, destination), 0)
    return () => clearTimeout(t)
  }, [source, destination, fetchRoute])

  const loadNearby = async (center) => {
    try {
      const { data } = await api.get("/places/nearby/", { params: { lat: center.latitude, lng: center.longitude, radius_km: 10, ...(category ? { category } : {}) } })
      setNearby((data.items || data.results || []).slice(0, 30))
    } catch { setNearby([]) }
  }
  useEffect(() => {
    if (!destination) return
    const t = setTimeout(() => loadNearby(destination), 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [destination, category])

  const points = useMemo(() => {
    const pts = []
    if (route?.length) pts.push(...route)
    else { if (source) pts.push([source.latitude, source.longitude]); if (destination) pts.push([destination.latitude, destination.longitude]) }
    return pts
  }, [route, source, destination])

  const fmtKm = (m) => (m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`)
  const fmtDur = (s) => (s >= 3600 ? `${Math.floor(s / 3600)} h ${Math.round((s % 3600) / 60)} min` : `${Math.round(s / 60)} min`)

  return (
    <div className="max-w-7xl mx-auto p-4">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Route Planner</h1>
      <p className="text-sm text-slate-500 mb-4">Real places from the database · real road routes from the routing engine · coordinates visible · no straight lines, no substitutions.</p>
      <div className="grid lg:grid-cols-[360px_1fr] gap-4">
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow p-4 space-y-3">
            <PlacePicker label="source" value={source} onChange={setSource} placeholder="Search any place in Nepal…" />
            <button onClick={useMyLocation} className="text-xs text-emerald-700 font-semibold hover:underline" data-testid="use-my-location">📍 Use my location (browser GPS)</button>
            <PlacePicker label="destination" value={destination} onChange={setDestination} placeholder="Where to?" />
            {you && <div className="text-[11px] text-sky-700">You are here: {you.latitude.toFixed(6)}, {you.longitude.toFixed(6)}</div>}
          </div>

          {loading && <div className="bg-white rounded-xl shadow p-4 text-sm text-slate-500">Calculating road route…</div>}
          {routeError && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800" data-testid="route-error">
              ⚠️ {routeError}
              {demoOffer && (
                <button onClick={tryPublicDemo} className="block mt-2 text-xs font-semibold text-emerald-700 hover:underline" data-testid="try-demo">
                  Try the public OSRM demo server (external, labelled)
                </button>
              )}
            </div>
          )}
          {routeEngine && (
            <div className="bg-white rounded-xl shadow p-4 space-y-2" data-testid="route-info">
              <div className="text-sm font-semibold text-slate-700">{source?.name} → {destination?.name}</div>
              <div className="text-sm text-slate-600">Distance: <b data-testid="route-distance">{fmtKm(routeEngine.info.distance_meters)}</b> · ETA (estimated): <b data-testid="route-eta">{fmtDur(routeEngine.info.duration_seconds)}</b> · Profile: driving</div>
              <div className="text-[11px] text-slate-400" data-testid="route-engine">{routeEngine.label}</div>
              {routeEngine.steps?.length > 0 && (
                <ol className="text-xs text-slate-600 space-y-1 max-h-48 overflow-auto list-decimal list-inside" data-testid="route-steps">
                  {routeEngine.steps.slice(0, 40).map((s, i) => (
                    <li key={i}>{s.instruction}{s.distance_m ? ` — ${fmtKm(s.distance_m)}` : ""}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          <div className="bg-white rounded-xl shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-slate-700">Nearby destination</span>
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="text-xs border border-slate-300 rounded px-2 py-1" data-testid="category-filter">
                <option value="">All categories</option>
                {["hospital", "pharmacy", "atm", "police", "hotel", "restaurant", "attraction", "fuel"].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <ul className="space-y-1 max-h-64 overflow-auto text-sm" data-testid="nearby-list">
              {nearby.map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-2 px-2 py-1 rounded hover:bg-slate-50">
                  <button className="text-left flex-1" onClick={() => {}}>
                    <span className="font-medium">{p.name}</span>
                    <span className="text-[11px] text-slate-400 block">{p.category} · {p.distance_km != null ? `${p.distance_km.toFixed(1)} km` : ""} · {p.latitude?.toFixed(5)}, {p.longitude?.toFixed(5)}{p.source === "osm_essential_service" ? " · imported/unverified (OSM)" : ""}</span>
                  </button>
                  <button
                    className="text-[11px] font-semibold text-emerald-700 hover:underline shrink-0"
                    onClick={() => setDestination({ name: p.name, latitude: p.latitude, longitude: p.longitude, canonical: p.id, routeParams: p.id?.startsWith("osm-") ? { destination_id: p.id.slice(4), destination_type: "service" } : p.destination_id ? { destination_id: p.destination_id } : null })}
                    data-testid="route-here"
                  >Route here</button>
                </li>
              ))}
              {!nearby.length && destination && <li className="text-xs text-slate-400">No nearby records in this category (absence of data ≠ absence of places).</li>}
            </ul>
          </div>
        </div>

        <div className="rounded-xl overflow-hidden shadow h-[560px]" data-testid="planner-map">
          <MapContainer center={[28.1, 84.1]} zoom={7} className="h-full w-full" maxBounds={NEPAL_BOUNDS} maxBoundsViscosity={0.6}>
            <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <FitBounds points={points} />
            {you && <Marker position={[you.latitude, you.longitude]} icon={youIcon}><Popup>You are here<br />{you.latitude.toFixed(6)}, {you.longitude.toFixed(6)}</Popup></Marker>}
            {source && <Marker position={[source.latitude, source.longitude]} icon={sourceIcon}><Popup><b>SOURCE</b><br />{source.name}<br />{source.latitude.toFixed(6)}, {source.longitude.toFixed(6)}{source.canonical ? <><br />ID: {source.canonical}</> : null}</Popup></Marker>}
            {destination && <Marker position={[destination.latitude, destination.longitude]} icon={destIcon}><Popup><b>DESTINATION</b><br />{destination.name}<br />{destination.latitude.toFixed(6)}, {destination.longitude.toFixed(6)}{destination.canonical ? <><br />ID: {destination.canonical}</> : null}</Popup></Marker>}
            {route && route.length > 1 && <Polyline positions={route} pathOptions={{ color: "#059669", weight: 5, opacity: 0.85 }} />}
            {nearby.map((p) => (
              <Marker key={p.id} position={[p.latitude, p.longitude]} icon={poiIcon(CATEGORY_COLORS[p.category?.toLowerCase()?.split(" ")[0]] || CATEGORY_COLORS.default)}>
                <Popup>
                  <b>{p.name}</b><br />Category: {p.category}<br />Location: {p.address}<br />Coordinates: {p.latitude?.toFixed(6)}, {p.longitude?.toFixed(6)}
                  {p.distance_km != null && <>Distance: {p.distance_km.toFixed(1)} km<br /></>}
                  Verification: {p.source === "osm_essential_service" ? "Imported / unverified" : "Database record"}<br />Source: {p.source}
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  )
}
