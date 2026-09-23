import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import useGeolocation from "../../hooks/useGeolocation"
import { useI18n } from "../../i18n"
import travelApi from "../../api/travelApi"
import destinationApi from "../../api/destinationApi"
import { formatDistance, formatDuration } from "../../utils/formatDistance"

/**
 * "Getting there" — real route FROM your location (or any other destination)
 * TO this destination. On-demand: the route is computed when the traveller
 * picks an origin, so the detail page stays fast.
 */
export default function GettingThereCard({ destination }) {
  const { t } = useI18n()
  const { position, retry: retryGeo } = useGeolocation()
  const [gpsMode, setGpsMode] = useState(true)
  const [originQuery, setOriginQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [originPick, setOriginPick] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

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
    if (gpsMode && !position) { retryGeo(); setError(t("tp.gps_unavailable")); return }
    if (!gpsMode && !originPick?.slug && originQuery.trim().length < 2) return
    setLoading(true)
    setError("")
    try {
      const params = { destination: destination.slug, mode: "driving", alternatives: 1 }
      if (gpsMode) {
        params.origin_lat = position.lat
        params.origin_lng = position.lng
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

  if (!hasCoords(destination)) return null

  const badge = (grade) => {
    if (grade === "real-road") {
      return <span className="rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 px-2 py-0.5 text-[10px] font-bold">✓ {t("tp.grade.real_road")}</span>
    }
    if (grade === "corridor-estimate") {
      return <span className="rounded-full bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 text-[10px] font-bold">⚠ {t("tp.grade.corridor")}</span>
    }
    return <span className="rounded-full bg-slate-100 text-slate-600 border border-slate-300 px-2 py-0.5 text-[10px] font-bold">{t("tp.grade.estimate")}</span>
  }

  return (
    <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50/60 dark:bg-emerald-950/40 dark:border-emerald-800 p-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h4 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
          <span aria-hidden>🧭</span> {t("tp.title")} — {t("tp.get_route")}
        </h4>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => { setGpsMode(true); setOriginPick(null); setResult(null) }}
            className={`rounded-lg px-3 py-1.5 text-[11px] font-bold border transition ${gpsMode ? "bg-emerald-700 text-white border-emerald-700" : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700"}`}
          >
            📍 {t("tp.origin.my_location")}
          </button>
          <button
            type="button"
            onClick={() => { setGpsMode(false); setResult(null) }}
            className={`rounded-lg px-3 py-1.5 text-[11px] font-bold border transition ${!gpsMode ? "bg-emerald-700 text-white border-emerald-700" : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-700"}`}
          >
            🏛️ {t("tp.from")}
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
                    {row.name} <span className="text-[10px] text-slate-400">{row.district || row.province}</span>
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
          {loading ? "…" : t("tp.get_route")}
        </button>
        {error && <span className="text-[11px] font-bold text-red-700 dark:text-red-300">{error}</span>}
      </div>

      {result && (
        <div className="mt-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-3">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="text-lg font-black text-emerald-700 dark:text-emerald-400">{formatDistance(result.primary.distance_km)}</div>
            <div className="text-lg font-black text-slate-900 dark:text-white">{formatDuration(result.primary.duration_min)}</div>
            {badge(result.primary.grade)}
            <span className="text-[11px] text-slate-400">
              {t("tp.straight_line")}: {formatDistance(result.straight_line_km)}
            </span>
            {(result.alternatives || []).length > 0 && (
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400">
                +{(result.alternatives || []).length} {t("tp.alternatives").toLowerCase()}
              </span>
            )}
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Link
              to={`/travel?dest=${encodeURIComponent(destination.slug)}`}
              className="rounded-lg border border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300 font-bold px-3 py-1.5 text-[11px] hover:bg-emerald-50 dark:hover:bg-slate-800"
            >
              {t("tp.title")} ➔
            </Link>
            <Link
              to={`/navigation?dest=${encodeURIComponent(destination.name)}`}
              className="rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1.5 text-[11px]"
            >
              {t("tp.start_navigation")}
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
