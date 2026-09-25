import { useMemo } from "react"
import { Link } from "react-router-dom"
import { FiMapPin, FiNavigation, FiRefreshCw, FiCompass } from "react-icons/fi"
import useGeolocation from "../../hooks/useGeolocation"
import { haversineKm } from "../../utils/placeUtils"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import { useI18n } from "../../i18n"
import { SlideUp } from "../common/MotionSystem"
import PlaceholderImage from "../common/PlaceholderImage"

/** Distance label with one decimal under 100 km, whole km above. */
function kmLabel(km) {
  if (km == null) return null
  if (km < 1) return "≈ 1 km"
  if (km < 100) return `≈ ${km.toFixed(1)} km`
  return `≈ ${km} km`
}

/**
 * Nearby destinations for the landing page.
 *
 * Location is explicitly opt-in here. Without a browser position we do not
 * substitute Kathmandu (or any other guessed origin), because doing so makes
 * a real distance label misleading. Visitors can still browse the complete
 * destination catalogue.
 */
export default function NearYouSection({ destinations = [] }) {
  const { t } = useI18n()
  const { position, error, locating, retry } = useGeolocation({ auto: false })

  const ranked = useMemo(() => {
    if (!position) return []
    return (destinations || [])
      .filter((destination) => destination && destination.latitude != null && destination.longitude != null)
      .map((destination) => ({
        ...destination,
        distanceKm: haversineKm(position.lat, position.lng, parseFloat(destination.latitude), parseFloat(destination.longitude)),
      }))
      .filter((destination) => Number.isFinite(destination.distanceKm))
      .sort((a, b) => a.distanceKm - b.distanceKm)
      .slice(0, 4)
  }, [destinations, position])

  const showLocationState = !position && !locating

  return (
    <section className="container-app section-space" aria-label={t("near.you.title")}>
      <SlideUp>
        <div className="mb-6 flex flex-col justify-center gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="section-head mx-auto max-w-2xl text-center sm:mx-0 sm:text-left">
            <span className="inline-flex rounded-full bg-[var(--ny-soft-green)] px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-[var(--ny-green)]">
              {t("near.you.badge")}
            </span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-[var(--ny-text)]">{t("near.you.title")}</h2>
            <p className="mt-1 text-sm text-[var(--ny-text-secondary)]">
              {t("near.you.subtitle")} {position ? t("near.you.from_you") : "when you choose to share your location"}
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap items-center justify-center gap-2 sm:justify-end">
            {locating && <span className="inline-flex min-h-10 items-center gap-2 text-sm text-[var(--ny-text-secondary)]"><FiRefreshCw className="animate-spin" size={15} aria-hidden="true" />{t("near.you.locating")}</span>}
            {showLocationState && <button type="button" onClick={retry} className="ny-btn ny-btn-secondary min-h-10 text-sm"><FiMapPin size={15} aria-hidden="true" />{t("near.you.use_my_location")}</button>}
            {error && showLocationState && <span className="w-full text-center text-xs text-[var(--ny-text-muted)] sm:w-auto">Location was not shared. You can browse all destinations instead.</span>}
          </div>
        </div>
      </SlideUp>

      {locating ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Loading nearby destinations">
          {Array.from({ length: 4 }, (_, index) => <div key={index} className="ny-card overflow-hidden"><div className="ny-skeleton h-36 w-full" /><div className="space-y-3 p-4"><div className="ny-skeleton h-4 w-2/3" /><div className="ny-skeleton h-3 w-1/2" /><div className="ny-skeleton mt-5 h-9 w-full" /></div></div>)}
        </div>
      ) : ranked.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {ranked.map((destination, index) => {
            const image = getDestinationImageUrl(destination)
            const slug = destination.slug || destination.id
            return (
              <article key={destination.id || destination.slug || destination.name} className="ny-card flex h-full flex-col overflow-hidden transition-transform hover:-translate-y-1">
                <div className="relative h-36 bg-[var(--ny-soft-green)]">
                  <PlaceholderImage src={image} title={destination.name || "Destination"} alt={destination.name || "Destination"} className="h-full w-full" />
                  <span className="absolute left-2 top-2 rounded-full bg-[var(--ny-green-deepest)] px-2.5 py-1 text-[11px] font-bold text-white backdrop-blur">{kmLabel(destination.distanceKm)}</span>
                  <span className="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-full bg-white/90 text-xs font-bold text-[var(--ny-green)] shadow-sm" aria-label={`Nearby destination ${index + 1}`}>{index + 1}</span>
                </div>
                <div className="flex flex-1 flex-col p-4">
                  <h3 className="text-sm font-bold leading-snug text-[var(--ny-text)]">{destination.name}</h3>
                  {destination.district && <p className="mt-1 flex items-center gap-1 text-xs text-[var(--ny-text-secondary)]"><FiMapPin size={12} aria-hidden="true" />{destination.district}{destination.city && destination.city !== destination.district ? `, ${destination.city}` : ""}</p>}
                  <div className="mt-auto flex gap-2 pt-4">
                    <Link to={`/navigation?dest=${encodeURIComponent(destination.name || "")}`} className="ny-btn ny-btn-primary min-h-10 flex-1 px-2 text-xs"><FiNavigation size={13} aria-hidden="true" />{t("near.you.navigate")}</Link>
                    {slug && <Link to={`/destinations/${slug}`} className="ny-btn ny-btn-secondary min-h-10 px-3 text-xs">{t("near.you.details")}</Link>}
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      ) : (
        <div className="ny-panel flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between" role="status">
          <div className="flex min-w-0 items-start gap-3">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] text-[var(--ny-green)]"><FiMapPin size={20} aria-hidden="true" /></span>
            <div className="min-w-0"><h3 className="text-base font-bold">{error ? "Location is unavailable" : "Explore places near you"}</h3><p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--ny-text-secondary)]">{error ? "We could not access your location. Browse the catalogue or try again when you are ready." : "Share your location to rank mapped destinations by real distance, or browse all destinations to start exploring Nepal."}</p></div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2"><Link to="/destinations" className="ny-btn ny-btn-primary"><FiCompass size={16} aria-hidden="true" />Browse destinations</Link>{showLocationState && <button type="button" onClick={retry} className="ny-btn ny-btn-secondary"><FiRefreshCw size={15} aria-hidden="true" />Try again</button>}</div>
        </div>
      )}
    </section>
  )
}
