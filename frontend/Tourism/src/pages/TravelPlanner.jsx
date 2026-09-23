import { useEffect, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import {
  BsArrowLeftRight, BsGeoAltFill, BsSpeedometer2,
  BsListCheck, BsSignpost2, BsPencil, BsPersonWalking, BsBicycle,
  BsCheckCircleFill, BsExclamationTriangle,
} from "react-icons/bs"
import { motion } from "framer-motion"
import MapView from "../components/map/MapView"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import useGeolocation from "../hooks/useGeolocation"
import { useI18n } from "../i18n"
import useAuth from "../hooks/useAuth"
import destinationApi from "../api/destinationApi"
import travelApi from "../api/travelApi"
import { savedRoutesApi } from "../services/api"
import { formatDistance, formatDuration } from "../utils/formatDistance"
import { getPlaceTypeIcon } from "../utils/placeTypeIcons"

const MODES = [
  { id: "driving", labelKey: "tp.mode.drive", icon: BsSpeedometer2 },
  { id: "walking", labelKey: "tp.mode.walk", icon: BsPersonWalking },
  { id: "cycling", labelKey: "tp.mode.cycle", icon: BsBicycle },
]

const MODE_EMOJI = { driving: "🚗", walking: "🚶", cycling: "🚴", flight: "✈️", hiking: "🥾", motorcycle: "🏍️" }

function gradeBadge(grade, t) {
  if (grade === "real-road") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 px-2.5 py-0.5 text-[11px] font-bold">
        <BsCheckCircleFill className="text-[11px]" /> {t("tp.grade.real_road")}
      </span>
    )
  }
  if (grade === "corridor-estimate") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-0.5 text-[11px] font-bold">
        <BsExclamationTriangle className="text-[11px]" /> {t("tp.grade.corridor")}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 text-slate-600 border border-slate-300 px-2.5 py-0.5 text-[11px] font-bold">
      {t("tp.grade.estimate")}
    </span>
  )
}

function EndpointField({ id, label, icon, value, onChange, onPickLocation, pickLabel, loading }) {
  const { t } = useI18n()
  return (
    <div className="relative">
      <label htmlFor={id} className="block text-[11px] font-black uppercase tracking-wider mb-1.5 text-slate-500 dark:text-slate-400">
        {label}
      </label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">{icon}</span>
        <input
          id={id}
          type="text"
          value={value}
          placeholder={t("tp.endpoint.placeholder")}
          onChange={(e) => onChange(e.target.value)}
          autoComplete="off"
          className="w-full rounded-xl border pl-10 pr-3 py-3 text-sm font-semibold outline-none transition
            bg-white border-slate-300 text-slate-900 placeholder-slate-400 focus:border-emerald-600
            dark:bg-slate-800 dark:border-slate-600 dark:text-white dark:placeholder-slate-400"
        />
      </div>
      <div className="flex items-center gap-2 mt-1.5">
        {onPickLocation && (
          <button
            type="button"
            onClick={onPickLocation}
            className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-lg border transition
              border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <BsGeoAltFill className="text-[11px]" /> {pickLabel}
          </button>
        )}
        {loading && <span className="text-[11px] font-semibold text-slate-400">…</span>}
      </div>
    </div>
  )
}

export default function TravelPlanner() {
  const { t } = useI18n()
  const { isAuthenticated } = useAuth() || {}
  // auto: false — /travel is a public page; GPS is only requested when the
  // traveller explicitly presses "Use my location" (privacy/consent §22/58).
  const { position, error: geoError, locating, retry: retryGeo } = useGeolocation({ auto: false })
  const [searchParams] = useSearchParams()

  const [originText, setOriginText] = useState(searchParams.get("origin") || "")
  const [destinationText, setDestinationText] = useState(searchParams.get("dest") || "")
  const [originPick, setOriginPick] = useState(null)   // {name, slug|lat,lng...}
  const [destPick, setDestPick] = useState(null)
  const [gpsUsed, setGpsUsed] = useState(false)
  const [mode, setMode] = useState("driving")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [activeAlt, setActiveAlt] = useState(null)     // index into results.alternatives
  const [showSteps, setShowSteps] = useState(true)
  const [between, setBetween] = useState(null)
  const [betweenLoading, setBetweenLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  // ---- destination autocomplete (real records only) ----------------------
  const useAutocomplete = (text, onPick) => {
    const [items, setItems] = useState([])
    const [open, setOpen] = useState(false)
    useEffect(() => {
      const q = text.trim()
      if (q.length < 2) { setItems([]); setOpen(false); return undefined }
      const timer = setTimeout(() => {
        destinationApi.getAll({ search: q, page_size: 7 })
          .then(({ data }) => {
            const rows = (data.results || data || []).slice(0, 7)
            setItems(rows)
            setOpen(rows.length > 0)
          })
          .catch(() => { setItems([]); setOpen(false) })
      }, 250)
      return () => clearTimeout(timer)
    }, [text])
    const pick = (row) => { onPick(row); setOpen(false) }
    const dropdown = (keyPrefix) => (
      open && (
        <ul className={`absolute z-30 mt-1 w-full max-h-64 overflow-auto rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 shadow-xl ${keyPrefix}`}>
          {items.map((row) => (
            <li key={row.id}>
              <button
                type="button"
                onClick={() => pick(row)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-emerald-50 dark:hover:bg-slate-700"
              >
                <span className="text-base">{getPlaceTypeIcon(row) || "📍"}</span>
                <span className="flex-1 truncate font-semibold text-slate-800 dark:text-slate-100">{row.name}</span>
                {(row.district || row.province) && (
                  <span className="text-[10px] text-slate-400 shrink-0">{row.district || row.province}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )
    )
    return { dropdown }
  }
  const originAc = useAutocomplete(originText, (row) => {
    setOriginText(row.name)
    setOriginPick({ kind: "destination", slug: row.slug, name: row.name, latitude: row.latitude, longitude: row.longitude })
    setGpsUsed(false)
  })
  const destAc = useAutocomplete(destinationText, (row) => {
    setDestinationText(row.name)
    setDestPick({ kind: "destination", slug: row.slug, name: row.name, latitude: row.latitude, longitude: row.longitude })
    loadBetween(row.slug)
  })

  // ---- "travel from here" data (event-driven: loaded when a destination is
  //      chosen, not in an effect, to avoid cascading renders) -------------
  const loadBetween = (slug) => {
    if (!slug) { setBetween(null); return }
    setBetweenLoading(true)
    travelApi.travelBetween(slug, 12)
      .then(({ data }) => setBetween(data))
      .catch(() => setBetween(null))
      .finally(() => setBetweenLoading(false))
  }

  const planRoute = async (m = mode) => {
    const dest = destPick || (destinationText.trim() ? { kind: "name", name: destinationText.trim() } : null)
    if (!dest) { setError(t("tp.error.need_destination")); return }
    if (gpsUsed && !position) {
      if (!locating) retryGeo()
      setError(locating ? t("tp.gps_pending") : t("tp.gps_pending"))
      return
    }
    setLoading(true)
    setError("")
    setActiveAlt(null)
    try {
      const params = { mode: m, alternatives: 1 }
      if (destPick?.slug) params.destination = destPick.slug
      else params.destination = dest.name
      if (gpsUsed && position) {
        params.origin_lat = position.lat
        params.origin_lng = position.lng
        params.origin_name = "Current Location"
      } else if (originPick?.slug) {
        params.origin = originPick.slug
      } else if (originText.trim()) {
        params.origin = originText.trim()
      }
      const { data } = await travelApi.plan(params)
      setResults(data)
      if (data?.destination?.slug) {
        setDestPick({ kind: "destination", slug: data.destination.slug, name: data.destination.name, latitude: data.destination.latitude, longitude: data.destination.longitude })
        setDestinationText(data.destination.name)
        loadBetween(data.destination.slug)
      }
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(detail || t("tp.error.generic"))
    } finally {
      setLoading(false)
    }
  }

  const useMyLocation = () => {
    if (position) {
      setGpsUsed(true)
      setOriginPick(null)
      setOriginText(t("tp.origin.my_location"))
    } else {
      retryGeo()
      setGpsUsed(true)
      setOriginPick(null)
      setOriginText(t("tp.origin.my_location"))
    }
  }

  const swap = () => {
    setOriginText(destinationText)
    setDestinationText(originText)
    setOriginPick(destPick)
    setDestPick(originPick)
  }

  const saveRoute = () => {
    if (!results || !isAuthenticated) return
    savedRoutesApi.create({
      origin_name: results.origin?.name || "Current Location",
      origin_latitude: results.origin?.latitude ?? null,
      origin_longitude: results.origin?.longitude ?? null,
      destination_name: results.destination?.name || "",
      destination_latitude: results.destination?.latitude ?? null,
      destination_longitude: results.destination?.longitude ?? null,
      transport_mode: mode,
      distance_km: results.primary?.distance_km ?? null,
      duration_min: results.primary?.duration_min ?? null,
      duration_source: results.primary?.source || "",
    }).then(() => setSaved(true)).catch(() => {})
  }

  const displayed = activeAlt != null && results?.alternatives?.[activeAlt]
    ? {
        ...results.primary,
        distance_m: results.alternatives[activeAlt].distance_m,
        distance_km: results.alternatives[activeAlt].distance_km,
        duration_min: results.alternatives[activeAlt].duration_min,
        geometry: results.alternatives[activeAlt].geometry,
        isAlt: true,
      }
    : results?.primary

  const mapCenter = useMemo(() => {
    const geom = displayed?.geometry || []
    if (geom.length >= 2) {
      const mid = geom[Math.floor(geom.length / 2)]
      return { lat: mid[0], lng: mid[1] }
    }
    if (results?.destination?.latitude != null) {
      return { lat: results.destination.latitude, lng: results.destination.longitude }
    }
    return null
  }, [displayed?.geometry, results])

  const navHref = results
    ? `/navigation?dest=${encodeURIComponent(results.destination?.name || destinationText)}` +
      (gpsUsed ? `&origin=${encodeURIComponent(t("tp.origin.my_location"))}` : "")
    : "/navigation"

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* ---------- header ---------- */}
      <div className="bg-emerald-950 text-white">
        <div className="max-w-6xl mx-auto px-4 py-10">
          <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-3xl md:text-4xl font-black flex items-center gap-3">
            <BsSignpost2 className="text-amber-400" /> {t("tp.title")}
          </motion.h1>
          <p className="mt-2 text-emerald-200 text-sm md:text-base max-w-3xl">{t("tp.subtitle")}</p>
        </div>
      </div>

      {/* Admin-editable intro / extra sections (renders nothing until written) */}
      <CMSPageIntro pageKey="travel" />

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* ---------- planner form ---------- */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card p-5 md:p-6">
          <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 items-start">
            <div className="relative">
              <EndpointField
                id="tp-origin"
                label={t("tp.from")}
                icon={<span aria-hidden>📍</span>}
                value={originText}
                onChange={(v) => { setOriginText(v); setOriginPick(null); setGpsUsed(false) }}
                onPickLocation={useMyLocation}
                pickLabel={t("tp.origin.my_location")}
              />
              {originAc.dropdown("origin-suggest")}
            </div>
            <div className="flex md:flex-col items-center justify-center gap-2 md:pt-8">
              <button
                type="button"
                onClick={swap}
                title={t("tp.swap")}
                className="rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200 p-2.5 hover:bg-emerald-200 dark:hover:bg-emerald-800 border border-emerald-300 dark:border-emerald-700"
              >
                <BsArrowLeftRight />
              </button>
            </div>
            <div className="relative">
              <EndpointField
                id="tp-destination"
                label={t("tp.to")}
                icon={<span aria-hidden>🏔️</span>}
                value={destinationText}
                onChange={(v) => { setDestinationText(v); setDestPick(null) }}
              />
              {destAc.dropdown("dest-suggest")}
            </div>
          </div>

          {/* mode chips */}
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMode(m.id)}
                className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-bold border transition
                  ${mode === m.id
                    ? "bg-emerald-700 text-white border-emerald-700 shadow"
                    : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-emerald-500"}`}
              >
                <m.icon /> {t(m.labelKey)}
              </button>
            ))}
            <button
              type="button"
              onClick={() => planRoute()}
              disabled={loading || !destinationText.trim()}
              className="ml-auto inline-flex items-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-black px-6 py-3 text-sm shadow transition"
            >
              {loading ? (
                <><span className="inline-block w-4 h-4 border-2 border-slate-900/40 border-t-slate-900 rounded-full animate-spin" /> {t("tp.loading")}</>
              ) : (
                <>🧭 {t("tp.get_route")}</>
              )}
            </button>
          </div>

          {geoError && (
            <p className="mt-3 text-[12px] font-semibold text-amber-700 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-300 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
              {t("tp.gps_unavailable")}
            </p>
          )}
          {error && (
            <p className="mt-3 text-[13px] font-bold text-red-700 bg-red-50 dark:bg-red-900/30 dark:text-red-300 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </div>

        {/* ---------- results ---------- */}
        {results && displayed && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* best-route hero */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card p-5 md:p-6">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-black text-slate-900 dark:text-white">{t("tp.best_route")}</h2>
                {gradeBadge(displayed.isAlt ? "estimate" : results.primary.grade, t)}
                {displayed.isAlt && (
                  <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400">({t("tp.alternative_selected")})</span>
                )}
              </div>
              <div className="mt-3 flex flex-wrap items-end gap-x-8 gap-y-3">
                <div>
                  <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">{t("tp.distance")}</div>
                  <div className="text-3xl font-black text-emerald-700 dark:text-emerald-400">{formatDistance(displayed.distance_km)}</div>
                </div>
                <div>
                  <div className="text-[11px] font-black uppercase tracking-wider text-slate-400">{t("tp.travel_time")}</div>
                  <div className="text-3xl font-black text-slate-900 dark:text-white">{formatDuration(displayed.duration_min)}</div>
                </div>
                <div className="text-[13px] font-semibold text-slate-500 dark:text-slate-400">
                  {t("tp.straight_line")}: <span className="text-slate-800 dark:text-slate-200 font-black">{formatDistance(results.straight_line_km)}</span>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link to={navHref} className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white font-bold px-5 py-2.5 text-sm shadow">
                  <BsSignpost2 /> {t("tp.start_navigation")}
                </Link>
                {isAuthenticated && (
                  <button
                    type="button"
                    onClick={saveRoute}
                    className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 font-bold px-5 py-2.5 text-sm hover:bg-emerald-50 dark:hover:bg-emerald-900/40"
                  >
                    {saved ? <BsCheckCircleFill /> : <BsPencil />} {saved ? t("tp.saved") : t("tp.save_route")}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowSteps((s) => !s)}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-bold px-5 py-2.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <BsListCheck /> {t("tp.turn_by_turn")} {showSteps ? "▴" : "▾"}
                </button>
              </div>
              {results.primary.note && <p className="mt-3 text-[12px] text-slate-500 dark:text-slate-400">{results.primary.note}</p>}
            </div>

            {/* map + steps + alternatives */}
            <div className="grid lg:grid-cols-2 gap-6">
              <div>
                <MapView
                  center={mapCenter}
                  destination={results.destination ? { lat: results.destination.latitude, lng: results.destination.longitude, name: results.destination.name } : null}
                  userLocation={gpsUsed && position ? { lat: position.lat, lng: position.lng } : null}
                  route={displayed.geometry || []}
                  height="420px"
                />
              </div>
              <div className="space-y-4">
                {showSteps && displayed && !displayed.isAlt && results.primary.steps?.length > 0 && (
                  <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
                    <div className="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 text-[12px] font-black uppercase tracking-wider text-slate-600 dark:text-slate-300">
                      {t("tp.turn_by_turn")}
                    </div>
                    <ol className="max-h-96 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
                      {results.primary.steps.map((s, i) => (
                        <li key={i} className="flex items-start gap-3 px-4 py-2.5">
                          <span className="shrink-0 w-7 h-7 rounded-full bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200 text-[12px] font-black flex items-center justify-center">
                            {i + 1}
                          </span>
                          <div className="min-w-0">
                            <div className="text-[13px] font-semibold text-slate-800 dark:text-slate-200">{s.instruction}</div>
                            {s.distance_m > 1 && (
                              <div className="text-[11px] text-slate-400">{formatDistance(s.distance_m / 1000)}</div>
                            )}
                          </div>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
                {displayed?.isAlt && (
                  <p className="text-[12px] font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
                    {t("tp.alt_steps_note")}
                  </p>
                )}

                {/* alternatives */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
                  <div className="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 text-[12px] font-black uppercase tracking-wider text-slate-600 dark:text-slate-300">
                    {t("tp.alternatives")} ({(results.alternatives || []).length})
                  </div>
                  {(results.alternatives || []).length === 0 ? (
                    <p className="px-4 py-4 text-[12px] text-slate-500 dark:text-slate-400">{t("tp.no_alternatives")}</p>
                  ) : (
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {results.alternatives.map((a, i) => (
                        <li key={i}>
                          <button
                            type="button"
                            onClick={() => setActiveAlt(activeAlt === i ? null : i)}
                            className={`w-full flex items-center gap-3 px-4 py-3 text-left transition ${activeAlt === i ? "bg-emerald-50 dark:bg-emerald-900/40" : "hover:bg-slate-50 dark:hover:bg-slate-800/60"}`}
                          >
                            <span className="text-lg">{MODE_EMOJI[mode] || "🚗"}</span>
                            <span className="flex-1">
                              <span className="block text-[13px] font-bold text-slate-800 dark:text-slate-200">
                                {t("tp.route_option", { n: i + 2 })}
                              </span>
                              <span className="block text-[11px] text-slate-400">
                                +{Math.max(0, Math.round(((a.distance_m - results.primary.distance_m) / Math.max(1, results.primary.distance_m)) * 100))}% {t("tp.longer")}
                              </span>
                            </span>
                            <span className="text-right">
                              <span className="block text-[13px] font-black text-slate-800 dark:text-slate-200">{formatDistance(a.distance_km)}</span>
                              <span className="block text-[11px] text-slate-400">{formatDuration(a.duration_min)}</span>
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            {/* mode comparison */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
              <div className="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 text-[12px] font-black uppercase tracking-wider text-slate-600 dark:text-slate-300">
                {t("tp.modes_compare")}
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-slate-400">
                    <th className="px-4 py-2 font-black">{t("tp.mode_col")}</th>
                    <th className="px-4 py-2 font-black">{t("tp.distance")}</th>
                    <th className="px-4 py-2 font-black">{t("tp.travel_time")}</th>
                    <th className="px-4 py-2 font-black">{t("tp.how_measured")}</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {(results.modes || []).map((m) => (
                    <tr key={m.mode} className={m.mode === mode ? "bg-emerald-50/60 dark:bg-emerald-900/20" : ""}>
                      <td className="px-4 py-2.5 font-bold text-slate-800 dark:text-slate-200">
                        {MODE_EMOJI[m.mode] || "🚗"} {m.label}
                      </td>
                      <td className="px-4 py-2.5 font-black text-slate-900 dark:text-white">{formatDistance(m.distance_m / 1000)}</td>
                      <td className="px-4 py-2.5 font-semibold text-slate-700 dark:text-slate-300">{formatDuration(m.duration_s / 60)}</td>
                      <td className="px-4 py-2.5">{gradeBadge(m.grade, t)}</td>
                      <td className="px-4 py-2.5 text-right">
                        {m.grade !== "real-road" && m.real_available && (
                          <button
                            type="button"
                            onClick={() => { setMode(m.mode); planRoute(m.mode) }}
                            className="text-[11px] font-black text-emerald-700 dark:text-emerald-300 hover:underline"
                          >
                            {t("tp.get_real")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {results.modes?.some((m) => m.estimate_note) && (
                <p className="px-4 py-3 text-[11px] text-slate-400 border-t border-slate-100 dark:border-slate-800">
                  {results.modes.find((m) => m.estimate_note).estimate_note}
                </p>
              )}
            </div>
          </motion.div>
        )}

        {/* ---------- travel from here ---------- */}
        {destPick?.slug && (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-card overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800">
              <h2 className="text-base font-black text-slate-900 dark:text-white flex items-center gap-2">
                <BsGlobeIcon /> {t("tp.travel_from_here", { name: destPick.name })}
              </h2>
              <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">{t("tp.travel_from_here_note")}</p>
            </div>
            {betweenLoading ? (
              <div className="px-5 py-8 text-center text-slate-400 text-sm font-semibold">…</div>
            ) : between ? (
              <div className="grid md:grid-cols-2 gap-x-6 px-5 py-4">
                <div>
                  <div className="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-2">{t("tp.provinces")}</div>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(between.provinces || {}).map(([p, v]) => (
                      <span key={p} className="rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2.5 py-1 text-[11px] font-bold">
                        {p} · {v.count}
                      </span>
                    ))}
                  </div>
                  <div className="mt-4 text-[12px] text-slate-500 dark:text-slate-400">
                    {t("tp.destinations_with_coords", { n: between.count_with_coordinates })}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-2">{t("tp.nearest")}</div>
                  <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                    {(between.nearest || []).map((n) => (
                      <li key={n.id} className="flex items-center gap-3 py-2">
                        <span className="text-base">{getPlaceTypeIcon({ name: n.name, category: n.category }) || "📍"}</span>
                        <span className="flex-1 min-w-0">
                          <span className="block truncate text-[13px] font-bold text-slate-800 dark:text-slate-200">{n.name}</span>
                          <span className="block text-[11px] text-slate-400">{n.province}{n.district ? ` · ${n.district}` : ""}</span>
                        </span>
                        <span className="text-right shrink-0">
                          <span className="block text-[13px] font-black text-emerald-700 dark:text-emerald-400">{formatDistance(n.straight_line_km)}</span>
                          <span className="block text-[11px] text-slate-400">~{formatDuration(n.drive_estimate_min)}</span>
                        </span>
                        <button
                          type="button"
                          title={t("tp.plan_route")}
                          onClick={() => {
                            setOriginPick(destPick)
                            setOriginText(destPick.name)
                            setGpsUsed(false)
                            setDestPick({ kind: "destination", slug: n.slug, name: n.name, latitude: null, longitude: null })
                            setDestinationText(n.name)
                            setTimeout(() => planRoute(mode), 0)
                          }}
                          className="shrink-0 rounded-lg bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200 px-2.5 py-1.5 text-[11px] font-black hover:bg-emerald-200 dark:hover:bg-emerald-800"
                        >
                          {t("tp.plan")}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="px-5 py-8 text-center text-slate-400 text-sm font-semibold">—</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function BsGlobeIcon() {
  return <span aria-hidden>🌐</span>
}
