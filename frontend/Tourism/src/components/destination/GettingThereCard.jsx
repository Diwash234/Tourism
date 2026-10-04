import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import useGeolocation from "../../hooks/useGeolocation"
import { useI18n } from "../../i18n"
import useAuth from "../../hooks/useAuth"
import travelApi from "../../api/travelApi"
import destinationApi from "../../api/destinationApi"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import { formatDistance, formatDuration } from "../../utils/formatDistance"

/**
 * "Getting there" ÔÇö real route FROM your location (or any other destination)
 * TO this destination. On-demand: the route is computed when the traveller
 * picks an origin, so the detail page stays fast ÔÇö but when the page already
 * resolved your position, the route plans itself.
 */
export default function GettingThereCard({ destination, userPosition }) {
  const { t } = useI18n()
  const { isAuthenticated } = useAuth() || {}
  // auto: false ÔÇö destination pages are public; GPS is only requested when
  // the traveller presses "Use my location" (privacy/consent ┬º22/58).
  const { position, locating, retry: retryGeo } = useGeolocation({ auto: false })
  const [gpsMode, setGpsMode] = useState(true)
  const [originQuery, setOriginQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [originPick, setOriginPick] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  // The detail page resolves the position once (shared cache/consent prompt)
  // and hands it over; this card's own hook covers every other entry point.
  const effectivePosition = position || userPosition

  useEffect(() => {
    const q = originQuery.trim()
    if (q.length < 2) return undefined
    let cancelled = false
    const timer = setTimeout(() => {
      destinationApi.getAll({ search: q, page_size: 5 })
        .then(({ data }) => { if (!cancelled) setSuggestions((data.results || data || []).slice(0, 5)) })
        .catch(() => { if (!cancelled) setSuggestions([]) })
    }, 250)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [originQuery])

  const plan = async () => {
    if (!destination?.slug) return
    if (gpsMode && !effectivePosition) {
      if (locating) { setError(t("tp.gps_pending")); return }
      retryGeo()
      setError(t("tp.gps_pending"))
      return
    }
    if (!gpsMode && !originPick?.slug && originQuery.trim().length < 2) return
    setLoading(true)
    setError("")
    try {
      const params = { destination: destination.slug, mode: "driving", alternatives: 1 }
      if (gpsMode) {
        params.origin_lat = effectivePosition.lat
        params.origin_lng = effectivePosition.lng
        params.origin_name = "Current Location"
      } else if (originPick?.slug) {
        params.origin = originPick.slug
      } else {
        params.origin = originQuery.trim()
      }
      const { data } = await travelApi.plan(params)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || t("tp.error.generic"))
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  // Once a position is known, show the route without a second button press ÔÇö
  // "how do I get there" is the first question on a destination page. The ref
  // key makes this once per origin; a failed plan is not retried in a loop.
  const autoPlannedRef = useRef(null)
  useEffect(() => {
    if (!gpsMode || !effectivePosition || loading || result) return
    const key = `${destination?.slug || ""}:${Number(effectivePosition.lat).toFixed(4)},${Number(effectivePosition.lng).toFixed(4)}`
    if (autoPlannedRef.current === key) return
    autoPlannedRef.current = key
    plan()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gpsMode, effectivePosition, loading, result, destination?.slug])

  if (!hasCoords(destination)) return null

  const badge = (grade) => {
    if (grade === "real-road") {
      return <span className="rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 px-2 py-0.5 text-xs font-bold">Ô£ô {t("tp.grade.real_road")}</span>
    }
    if (grade === "corridor-estimate") {
      return <span className="rounded-full bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 text-xs font-bold">ÔÜá {t("tp.grade.corridor")}</span>
    }
    return <span className="rounded-full bg-slate-100 text-slate-600 border border-slate-300 px-2 py-0.5 text-xs font-bold">{t("tp.grade.estimate")}</span>
  }

  return (
    <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/60 dark:bg-emerald-950/40 dark:border-emerald-800 p-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
          {t("tp.title")} ÔÇö {t("tp.get_route")}
        </h4>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => { setGpsMode(true); setOriginPick(null); setResult(null) }}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold border transition ${gpsMode ? "bg-emerald-700 text-white border-emerald-700" : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700"}`}
          >
            {t("tp.origin.my_location")}
          </button>
          <button
            type="button"
            onClick={() => { setGpsMode(false); setResult(null) }}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold border transition ${!gpsMode ? "bg-emerald-700 text-white border-emerald-700" : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700"}`}
          >
            {t("tp.from")}
          </button>
        </div>
      </div>

      {!gpsMode && (
        <div className="relative mt-3">
          <input
            type="text"
            value={originQuery}
            onChange={(e) => { setOriginQuery(e.target.value); setOriginPick(null); setResult(null); if (e.target.value.trim().length < 2) setSuggestions([]) }}
            placeholder={t("tp.endpoint.placeholder")}
            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-sm outline-none focus:border-emerald-600"
          />
          {suggestions.length > 0 && (
            <ul className="absolute z-30 mt-1 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-xl max-h-52 overflow-auto">
              {suggestions.map((row) => (
                <li key={row.id}>
                  <button
                    type="button"
                    onClick={() => { setOriginPick(row); setOriginQuery(row.name); setResult(null) }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-emerald-50 dark:hover:bg-slate-800 font-semibold text-slate-800 dark:text-slate-200"
                  >
                    {row.name} <span className="text-xs text-slate-500 dark:text-slate-400">{row.district || row.province}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={plan}
          disabled={loading}
          className="rounded-xl bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold px-4 py-2 text-xs shadow"
        >
          {loading ? "ÔÇª" : t("tp.get_route")}
        </button>
        {error && <span className="text-xs font-bold text-red-700 dark:text-red-300">{error}</span>}
      </div>

      {result && (
        <div className="mt-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-3">
          <div className="flex items-center gap-3 flex-wrap">
            <img
              src={getDestinationImageUrl(destination)}
              alt={destination.name}
              loading="lazy"
              onError={(event) => { event.currentTarget.style.display = "none" }}
              className="h-14 w-14 rounded-xl object-cover shrink-0 border border-emerald-200 dark:border-emerald-800"
            />
            <div className="text-lg font-black text-emerald-700 dark:text-emerald-400">{formatDistance(result.primary.distance_km)}</div>
            <div className="text-lg font-black text-slate-900 dark:text-white">{formatDuration(result.primary.duration_min)}</div>
            {badge(result.primary.grade)}
            <span className="text-xs text-slate-400">
              {t("tp.straight_line")}: {formatDistance(result.straight_line_km)}
            </span>
            {(result.alternatives || []).length > 0 && (
              <span className="text-xs font-bold text-slate-500 dark:text-slate-400">
                +{(result.alternatives || []).length} {t("tp.alternatives").toLowerCase()}
              </span>
            )}
          </div>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <a
              href={`https://www.google.com/maps/dir/?api=1&destination=${destination.latitude},${destination.longitude}${
                gpsMode && effectivePosition ? `&origin=${effectivePosition.lat},${effectivePosition.lng}` : ""
              }&travelmode=driving`}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold px-3 py-1.5 text-xs"
            >
              Open road map &amp; turns Ôåù
            </a>
            <Link
              to={`/travel?dest=${encodeURIComponent(destination.slug)}`}
              className="rounded-lg border border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 font-bold px-3 py-1.5 text-xs hover:bg-emerald-50 dark:hover:bg-slate-800"
            >
              {t("tp.title")} Ô×ö
            </Link>
            <Link
              to={isAuthenticated ? `/navigation?dest=${encodeURIComponent(destination.name)}` : `/login?next=${encodeURIComponent(`/navigation?dest=${encodeURIComponent(destination.name)}`)}`}
              className="rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1.5 text-xs"
            >
              {isAuthenticated ? t("tp.start_navigation") : "Sign in to navigate"}
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

function hasCoords(destination) {
  return Number(destination?.latitude) && Number(destination?.longitude)
}
