import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import L from "leaflet"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { useI18n } from "../i18n"
import useGeolocation from "../hooks/useGeolocation"
import destinationApi from "../api/destinationApi"
import travelApi from "../api/travelApi"
import TurnByTurnNav from "../components/navigation/TurnByTurnNav"
import { PlaceTypeIconImg } from "../utils/placeTypeIcons"
import {
  haversineKmPrecise, compassPoint, compassArrow, formatDistanceKm,
  KATHMANDU_COORDS, hasValidCoords,
} from "../utils/placeUtils"
import { userIcon, destinationIcon } from "../components/map/icons"

const NEPAL_BOUNDS = L.latLngBounds([26.35, 80.0], [30.55, 88.25])
const LIST_CHUNK = 300

// Honest road-route quality label from the travel-plan grade.
const gradeBadge = (grade) => {
  const g = String(grade || "")
  if (/osrm|street|road/i.test(g)) return { label: "Road-verified (OSRM)", cls: "bg-emerald-100 text-emerald-800" }
  if (/corridor/i.test(g)) return { label: "Corridor estimate", cls: "bg-amber-100 text-amber-800" }
  if (/straight/i.test(g)) return { label: "Straight-line only", cls: "bg-stone-200 text-stone-700" }
  return { label: "Estimate", cls: "bg-stone-200 text-stone-700" }
}

export default function DistancesExplorer() {
  const { t } = useI18n()
  const { position, error: geoError, locating, retry: requestLocation } = useGeolocation({ auto: false })

  const [points, setPoints] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)

  // Origin: my GPS location, a chosen destination, or Kathmandu (assumed).
  const [origin, setOrigin] = useState({
    kind: "kathmandu",
    lat: KATHMANDU_COORDS.lat,
    lng: KATHMANDU_COORDS.lng,
    label: t("dx.kathmandu_assumed"),
  })
  const [originQuery, setOriginQuery] = useState("")
  const [showOriginSuggest, setShowOriginSuggest] = useState(false)

  const [query, setQuery] = useState("")
  const [selected, setSelected] = useState(null)
  const [visible, setVisible] = useState(LIST_CHUNK)

  const [route, setRoute] = useState(null)
  const [routeFor, setRouteFor] = useState(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState(null)

  const mapRef = useRef(null)
  const mapElRef = useRef(null)
  const pointsLayerRef = useRef(null)
  const overlayRef = useRef(null)

  // ------------------------------------------------------------- data load
  useEffect(() => {
    let ignore = false
    destinationApi
      .getMapPoints()
      .then(({ data }) => {
        if (ignore) return
        setPoints(data.points || [])
        setLoadError(null)
      })
      .catch((err) => {
        if (!ignore) setLoadError(err?.response?.data?.detail || "Could not load destinations.")
      })
      .finally(() => !ignore && setLoading(false))
    return () => { ignore = true }
  }, [])

  // --------------------------------------------------- distance + bearing
  const enriched = useMemo(() => {
    if (!hasValidCoords(origin.lat, origin.lng)) return []
    return points
      .map((p) => {
        const km = haversineKmPrecise(origin.lat, origin.lng, p.latitude, p.longitude)
        return { ...p, km, dir: compassPoint(origin.lat, origin.lng, p.latitude, p.longitude) }
      })
      .filter((p) => p.km != null)
      .sort((a, b) => a.km - b.km)
  }, [points, origin.lat, origin.lng])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return enriched
    return enriched.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.district || "").toLowerCase().includes(q) ||
        (p.province || "").toLowerCase().includes(q)
    )
  }, [enriched, query])

  // Origin suggestions (top 8 matches of the typed name).
  const originSuggestions = useMemo(() => {
    const q = originQuery.trim().toLowerCase()
    if (!q) return []
    const hits = []
    for (const p of points) {
      if (p.name.toLowerCase().includes(q) || (p.district || "").toLowerCase().includes(q)) {
        hits.push(p)
        if (hits.length >= 8) break
      }
    }
    return hits
  }, [points, originQuery])

  // -------------------------------------------------------------- select
  const selectPoint = useCallback((p) => {
    setSelected(p)
  }, [])

  const selectOriginFromSuggestion = useCallback((p) => {
    setOrigin({ kind: "dest", lat: p.latitude, lng: p.longitude, label: p.name, point: p })
    setOriginQuery("")
    setShowOriginSuggest(false)
    setVisible(LIST_CHUNK)
  }, [])

  // Consent-gated GPS: the browser permission prompt only fires after this
  // explicit click (brief §location consent). The fix is adopted the moment
  // it arrives; a denied/unavailable fix leaves the assumed origin in place
  // and the UI explains that.
  const pendingGps = useRef(false)
  const requestGps = useCallback(() => {
    if (position && hasValidCoords(position.lat, position.lng)) {
      setOrigin({ kind: "gps", lat: position.lat, lng: position.lng, label: t("dx.origin_here") })
      setVisible(LIST_CHUNK)
      return
    }
    pendingGps.current = true
    requestLocation()
  }, [position, requestLocation, t])

  useEffect(() => {
    if (pendingGps.current && position && hasValidCoords(position.lat, position.lng)) {
      pendingGps.current = false
      setOrigin({ kind: "gps", lat: position.lat, lng: position.lng, label: t("dx.origin_here") })
      setVisible(LIST_CHUNK)
    }
  }, [position, t])

  // ---------------------------------------------------------------- map
  useEffect(() => {
    if (!mapElRef.current || mapRef.current) return
    const map = L.map(mapElRef.current, { zoomControl: true, attributionControl: true })
    map.fitBounds(NEPAL_BOUNDS)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map)
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      pointsLayerRef.current = null
      overlayRef.current = null
    }
  }, [])

  // All destination markers (canvas renderer — thousands of points stay smooth).
  useEffect(() => {
    const map = mapRef.current
    if (!map || !points.length) return
    if (pointsLayerRef.current) pointsLayerRef.current.remove()
    const renderer = L.canvas({ padding: 0.3 })
    const layer = L.layerGroup(
      points.map((p) =>
        L.circleMarker([p.latitude, p.longitude], {
          renderer,
          radius: 3,
          weight: 1,
          color: "#ffffff",
          fillColor: "#166534",
          fillOpacity: 0.85,
        }).on("click", () => selectPoint(p))
      )
    )
    layer.addTo(map)
    pointsLayerRef.current = layer
  }, [points, selectPoint])

  // Origin + selected destination overlay (pin, distance label, straight line, road route).
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (overlayRef.current) {
      overlayRef.current.remove()
      overlayRef.current = null
    }
    if (!hasValidCoords(origin.lat, origin.lng)) return
    const overlay = L.layerGroup().addTo(map)
    L.marker([origin.lat, origin.lng], {
      icon: origin.kind === "gps" ? userIcon : destinationIcon,
      zIndexOffset: 1000,
    }).addTo(overlay).bindTooltip(origin.label, { direction: "top", offset: L.point(0, -38) })
    if (selected) {
      L.marker([selected.latitude, selected.longitude], {
        icon: destinationIcon,
        zIndexOffset: 900,
      }).addTo(overlay).bindTooltip(`${selected.name} — ${formatDistanceKm(selected.km)} ${t("dx.straight_line")}`, {
        direction: "top",
        offset: L.point(0, -38),
      })
      L.polyline([[origin.lat, origin.lng], [selected.latitude, selected.longitude]], {
        color: "#0f766e",
        weight: 2,
        dashArray: "6 8",
        opacity: 0.9,
      }).addTo(overlay)
      if (selected.km != null) {
        const label = L.divIcon({
          className: "",
          html: `<div style="background:#1D5146;color:#fff;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:700;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,.3)">${formatDistanceKm(selected.km)} ${t("dx.straight_line")}</div>`,
          iconSize: null,
          iconAnchor: [45, 10],
        })
        L.marker([(origin.lat + selected.latitude) / 2, (origin.lng + selected.longitude) / 2], {
          icon: label,
          interactive: false,
          zIndexOffset: 500,
        }).addTo(overlay)
      }
      const zoom = selected.km == null ? 10 : selected.km < 10 ? 14 : selected.km < 100 ? 11 : 9
      map.flyTo([selected.latitude, selected.longitude], Math.max(zoom, map.getZoom() < zoom ? zoom : map.getZoom()), { duration: 0.8 })
    }
    overlayRef.current = overlay
  }, [origin, selected, t])

  // Road route drawn on the map once the plan resolves.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (routeRef.current) {
      routeRef.current.remove()
      routeRef.current = null
    }
    const geom = route?.primary?.geometry || route?.geometry
    if (geom && geom.length >= 2) {
      const line = L.polyline(geom, { color: "#b45309", weight: 4, opacity: 0.9 })
      line.addTo(map)
      map.fitBounds(line.getBounds().pad(0.15))
      routeRef.current = line
    }
  }, [route])
  const routeRef = useRef(null)

  // ------------------------------------------------------ directions call
  const getDirections = useCallback(async (dest) => {
    if (!dest) return
    setSelected(dest)
    setRouteFor(dest)
    setRoute(null)
    setRouteError(null)
    setRouteLoading(true)
    try {
      const params = { destination: dest.slug, mode: "driving" }
      if (origin.kind === "dest" && origin.point?.slug) params.origin = origin.point.slug
      else {
        params.origin_lat = origin.lat
        params.origin_lng = origin.lng
      }
      const { data } = await travelApi.plan(params)
      setRoute(data)
    } catch (err) {
      setRouteError(err?.response?.data?.detail || t("dx.road_unavailable"))
    } finally {
      setRouteLoading(false)
    }
  }, [origin, t])

  const primary = route?.primary || null
  const badge = primary ? gradeBadge(primary.grade) : null

  return (
    <div className="space-y-6">
      <CMSPageIntro pageKey="distances" />
      <PageHeader
        title={t("dx.title")}
        subtitle={t("dx.subtitle")}
        theme="forest"
        actions={
          <span className="text-xs font-bold bg-white/15 border border-white/25 rounded-full px-3 py-1.5">
            {loading ? t("dx.loading") : t("dx.total").replace("{n}", points.length.toLocaleString("en-US"))}
          </span>
        }
      />

      {/* Origin + search controls */}
      <div className="card-base rounded-3xl border border-[#E5E0D5] p-4 sm:p-5 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <img src="/icons/ui/navigate.svg" alt="" aria-hidden="true" className="w-9 h-9 shrink-0" />
            <div className="min-w-0">
              <p className="text-[11px] font-extrabold uppercase tracking-wide text-gray-400">{t("dx.origin")}</p>
              <p className="font-bold text-gray-900 truncate">
                {origin.label}
                {origin.kind === "kathmandu" && <span className="text-xs text-gray-400 font-semibold"> ({t("dx.kathmandu_assumed")})</span>}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={requestGps}
              disabled={locating}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#1D5146] text-white text-xs font-bold hover:bg-[#143b2c] disabled:opacity-60 transition-colors"
            >
              <img src="/icons/ui/waypoint.svg" alt="" aria-hidden="true" className="w-4 h-4" />
              {locating ? "…" : t("dx.use_my_location")}
            </button>
            <div className="relative">
              <input
                type="text"
                value={originQuery}
                onChange={(e) => { setOriginQuery(e.target.value); setShowOriginSuggest(true) }}
                onFocus={() => setShowOriginSuggest(true)}
                onBlur={() => setTimeout(() => setShowOriginSuggest(false), 150)}
                placeholder="Or start from a place…"
                className="w-56 px-3.5 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[#1D5146]/40"
              />
              {showOriginSuggest && originSuggestions.length > 0 && (
                <ul className="absolute z-50 mt-1 w-72 max-h-64 overflow-y-auto bg-white rounded-xl shadow-xl border border-gray-100 py-1">
                  {originSuggestions.map((p) => (
                    <li key={p.id}>
                      <button
                        type="button"
                        onMouseDown={() => selectOriginFromSuggestion(p)}
                        className="w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center gap-2.5"
                      >
                        <PlaceTypeIconImg destination={p} className="w-5 h-5 shrink-0" />
                        <span className="min-w-0">
                          <span className="block text-xs font-bold text-gray-800 truncate">{p.name}</span>
                          <span className="block text-[10px] text-gray-400 truncate">{p.district || "—"}{p.province ? ` · ${p.province}` : ""}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {geoError && origin.kind !== "gps" && (
          <p className="text-xs text-red-700 bg-red-50 border border-red-100 rounded-xl px-3 py-2">{t("dx.location_denied")}</p>
        )}

        <div className="flex items-center gap-3 border-t border-gray-100 pt-4">
          <img src="/icons/ui/distance.svg" alt="" aria-hidden="true" className="w-7 h-7" />
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setVisible(LIST_CHUNK) }}
              placeholder={t("dx.search_placeholder")}
              className="w-full px-4 py-3 rounded-2xl border border-gray-200 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#1D5146]/40"
            />
          </div>
          <span className="hidden sm:inline text-[11px] font-bold text-gray-400 whitespace-nowrap">
            {t("dx.nearest_first")}
          </span>
        </div>
      </div>

      {loadError && (
        <div className="card-base rounded-3xl border border-red-200 bg-red-50 p-5 text-sm font-semibold text-red-800">
          {loadError}
        </div>
      )}

      {/* Map + ranked list */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_400px] gap-6 items-stretch">
        <div className="card-base rounded-3xl border border-[#E5E0D5] overflow-hidden flex flex-col">
          <div className="px-5 pt-4 pb-3 flex items-center justify-between gap-3">
            <h3 className="font-bold text-sm text-gray-900">{t("dx.title")}</h3>
            <span className="text-[11px] text-gray-400 font-semibold hidden sm:block">{t("dx.map_hint")}</span>
          </div>
          <div ref={mapElRef} className="flex-1 min-h-[420px] xl:min-h-[520px] w-full" />
        </div>

        <div className="card-base rounded-3xl border border-[#E5E0D5] flex flex-col min-h-[420px] xl:min-h-[520px] overflow-hidden">
          <div className="px-5 pt-4 pb-3 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-bold text-sm text-gray-900">
              {query ? `${filtered.length.toLocaleString("en-US")} ${t("dx.total").replace("{n}", "")}` : t("dx.nearest_first")}
            </h3>
            <span className="text-[11px] font-bold text-[#1D5146] bg-emerald-50 rounded-full px-2.5 py-1">
              {formatDistanceKm(filtered[0]?.km)} – {formatDistanceKm(filtered[Math.min(visible, filtered.length) - 1]?.km)}
            </span>
          </div>
          <ol className="flex-1 overflow-y-auto divide-y divide-gray-50">
            {loading && <li className="p-5 text-sm text-gray-400 font-semibold">{t("dx.loading")}</li>}
            {!loading && filtered.length === 0 && (
              <li className="p-5 text-sm text-gray-400 font-semibold">{t("dx.no_results")}</li>
            )}
            {!loading && filtered.slice(0, visible).map((p) => {
              const isSel = selected?.id === p.id
              return (
                <li
                  key={p.id}
                  onClick={() => selectPoint(p)}
                  className={`px-4 py-3 cursor-pointer flex items-center gap-3 transition-colors ${
                    isSel ? "bg-emerald-50/70" : "hover:bg-gray-50"
                  }`}
                >
                  <PlaceTypeIconImg destination={p} className="w-7 h-7 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-gray-900 truncate">{p.name}</p>
                    <p className="text-[10px] text-gray-400 truncate">
                      {p.district || "—"}{p.province ? ` · ${p.province}` : ""}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs font-extrabold text-[#1D5146] tabular-nums">{formatDistanceKm(p.km)}</p>
                    <p className="text-[10px] font-bold text-gray-400 tabular-nums" title={t("dx.bearing")}>
                      {p.dir} {compassArrow(p.dir)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); getDirections(p) }}
                    className="shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-gray-100 hover:bg-[#1D5146] hover:text-white text-gray-600 text-[10px] font-extrabold transition-colors"
                    title={t("dx.get_directions")}
                  >
                    <img src="/icons/ui/turn-right.svg" alt="" aria-hidden="true" className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{t("dx.get_directions")}</span>
                  </button>
                </li>
              )
            })}
          </ol>
          {!loading && filtered.length > visible && (
            <button
              type="button"
              onClick={() => setVisible((v) => v + LIST_CHUNK)}
              className="w-full py-3 text-xs font-extrabold text-[#1D5146] border-t border-gray-100 hover:bg-gray-50 transition-colors"
            >
              Show more ({(filtered.length - visible).toLocaleString("en-US")} more)
            </button>
          )}
        </div>
      </div>

      {/* Road route + turn-by-turn for the chosen destination */}
      {(routeLoading || primary || routeError) && (
        <div className="card-base rounded-3xl border border-[#E5E0D5] p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-3">
            <img src="/icons/ui/route.svg" alt="" aria-hidden="true" className="w-8 h-8" />
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-base text-gray-900">{t("dx.directions")}</h3>
              <p className="text-xs text-gray-400 truncate">
                {origin.label} → {routeFor?.name}
              </p>
            </div>
            {badge && !routeLoading && (
              <span className={`text-[11px] font-extrabold rounded-full px-3 py-1 ${badge.cls}`}>{badge.label}</span>
            )}
          </div>

          {routeLoading && <p className="text-sm text-gray-400 font-semibold">Planning the road route…</p>}

          {routeError && !routeLoading && (
            <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3">{routeError}</p>
          )}

          {primary && !routeLoading && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="rounded-2xl bg-gray-50 border border-gray-100 p-3">
                  <p className="text-[10px] font-extrabold uppercase text-gray-400">{t("dx.road")}</p>
                  <p className="text-lg font-black text-gray-900">{(primary.distance_km ?? 0).toLocaleString("en-US")} km</p>
                </div>
                <div className="rounded-2xl bg-gray-50 border border-gray-100 p-3">
                  <p className="text-[10px] font-extrabold uppercase text-gray-400">{t("dx.eta")}</p>
                  <p className="text-lg font-black text-gray-900">
                    {Math.floor((primary.duration_min ?? 0) / 60)}h {Math.round((primary.duration_min ?? 0) % 60)}m
                  </p>
                </div>
                <div className="rounded-2xl bg-gray-50 border border-gray-100 p-3 col-span-2 sm:col-span-1">
                  <p className="text-[10px] font-extrabold uppercase text-gray-400">{t("dx.straight_line")}</p>
                  <p className="text-lg font-black text-gray-900">{formatDistanceKm(selected?.km ?? routeFor?.km)}</p>
                </div>
              </div>
              {primary.note && <p className="text-xs text-gray-500 italic">{primary.note}</p>}
              {Array.isArray(primary.steps) && primary.steps.length > 0 && (
                <TurnByTurnNav steps={primary.steps} currentIdx={0} />
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
