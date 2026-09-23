import { useMemo } from "react"
import { Link } from "react-router-dom"
import { FiMapPin, FiNavigation, FiRefreshCw } from "react-icons/fi"
import useGeolocation from "../../hooks/useGeolocation"
import { haversineKm, KATHMANDU_COORDS } from "../../utils/placeUtils"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import PlaceholderImage from "../common/PlaceholderImage"
import { useI18n } from "../../i18n"
import { SlideUp } from "../common/MotionSystem"

/** Distance label with one decimal under 100 km, whole km above. */
function kmLabel(km) {
  if (km == null) return null
  if (km < 1) return "≈ 1 km"
  if (km < 100) return `≈ ${km.toFixed(1)} km`
  return `≈ ${km} km`
}

/**
 * "Near you" — the distance hook of the landing page (pre-login).
 *
 * As soon as the visitor grants (or declines) location, every mapped
 * destination in the featured set is ranked by real distance from their
 * current position. When location is blocked, distances honestly fall back
 * to Kathmandu so the section is never empty.
 */
export default function NearYouSection({ destinations = [] }) {
  const { t } = useI18n()
  const { position, error, locating, retry } = useGeolocation()

  const hasCoords = (d) =>
    d &&
    d.latitude != null && d.longitude != null &&
    !Number.isNaN(parseFloat(d.latitude)) && !Number.isNaN(parseFloat(d.longitude))

  const ranked = useMemo(() => {
    const base = position || KATHMANDU_COORDS
    const list = (destinations || [])
      .filter(hasCoords)
      .map((d) => {
        const km = haversineKm(base.lat, base.lng, parseFloat(d.latitude), parseFloat(d.longitude))
        return { ...d, distanceKm: km }
      })
      .filter((d) => d.distanceKm != null)
      .sort((a, b) => a.distanceKm - b.distanceKm)
    return list.slice(0, 4)
  }, [destinations, position])

  const fromYou = !!position
  const sourceLabel = fromYou ? t("near.you.from_you") : t("near.you.from_kathmandu")

  return (
    <section className="container-app section-space" aria-label={t("near.you.title")}>
      <SlideUp>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 mb-6">
          <div className="text-center sm:text-left max-w-2xl mx-auto sm:mx-0 section-head">
            <span className="px-3.5 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-black uppercase tracking-wider">
              {t("near.you.badge")}
            </span>
            <h2 className="text-3xl font-extrabold text-gray-900 mt-2 tracking-tight">
              {t("near.you.title")}
            </h2>
            <p className="text-gray-500 text-sm mt-1">
              {t("near.you.subtitle")} {sourceLabel}
              {locating && <span className="ml-1 text-emerald-700 font-semibold">{t("near.you.locating")}</span>}
            </p>
          </div>
          {error && (
            <button
              type="button"
              onClick={retry}
              className="shrink-0 inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 hover:text-emerald-900"
            >
              <FiRefreshCw size={13} /> {t("near.you.use_my_location")}
            </button>
          )}
        </div>
      </SlideUp>

      {ranked.length === 0 ? (
        <div className="card-base rounded-2xl p-8 text-center text-sm text-gray-500">
          {t("near.you.no_mapped")}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ranked.map((d, i) => {
            const img = getDestinationImageUrl(d)
            const dest = encodeURIComponent(d.name || "")
            return (
              <div key={d.id || d.slug || d.name} className="card-base rounded-2xl overflow-hidden border border-emerald-100 shadow-sm hover:shadow-xl transition-all flex flex-col">
                <div className="relative h-36 bg-emerald-50">
                  {img ? (
                    <PlaceholderImage src={img} title={d.name} alt={d.name} className="w-full h-full" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl">🏔️</div>
                  )}
                  <span className="absolute top-2 left-2 px-2.5 py-1 rounded-full bg-emerald-950/85 text-white text-[11px] font-black backdrop-blur">
                    {kmLabel(d.distanceKm)}
                  </span>
                  <span className="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/90 text-emerald-900 text-xs font-black flex items-center justify-center shadow">
                    {i + 1}
                  </span>
                </div>
                <div className="p-4 flex-1 flex flex-col">
                  <h3 className="font-bold text-sm text-gray-900 leading-snug">{d.name}</h3>
                  {d.district && <p className="text-[11px] text-gray-500 mt-0.5 flex items-center gap-1"><FiMapPin size={11} /> {d.district}{d.city && d.city !== d.district ? `, ${d.city}` : ""}</p>}
                  <div className="mt-auto pt-3 flex items-center gap-2">
                    <Link
                      to={`/navigation?dest=${dest}`}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-bold transition-colors"
                    >
                      <FiNavigation size={13} /> {t("near.you.navigate")}
                    </Link>
                    <Link
                      to={`/destinations/${d.slug || d.id}`}
                      className="inline-flex items-center justify-center gap-1 px-3 py-2 rounded-lg border border-emerald-200 text-emerald-800 hover:bg-emerald-50 text-xs font-bold transition-colors"
                    >
                      {t("near.you.details")}
                    </Link>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {!fromYou && !locating && (
        <p className="text-[11px] text-gray-400 mt-3 text-center sm:text-left">
          {t("near.you.fallback_note")}
        </p>
      )}
    </section>
  )
}
