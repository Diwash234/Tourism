import { useEffect, useMemo, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  FiMapPin,
  FiNavigation,
  FiHeart,
  FiClock,
  FiSun,
  FiCompass,
  FiShield,
  FiAlertCircle,
} from "react-icons/fi"
import { placeLocationLabel, INFO_UNAVAILABLE } from "../../utils/placeUtils"

const FOCAL_CENTER = "center center"

// Keep the image treatment readable over any destination photograph while
// staying inside the shared Nepal Yatra green/gold visual language.
const scrim = {
  background: [
    "linear-gradient(to top, rgba(4, 42, 36, 0.97) 0%, rgba(4, 42, 36, 0.78) 42%, rgba(4, 42, 36, 0.32) 76%, rgba(4, 42, 36, 0.12) 100%)",
    "linear-gradient(to right, rgba(4, 42, 36, 0.86) 0%, rgba(4, 42, 36, 0.42) 56%, rgba(4, 42, 36, 0.08) 100%)",
    "radial-gradient(120% 90% at 50% 8%, rgba(99, 230, 190, 0.05) 0%, rgba(4, 42, 36, 0.38) 100%)",
  ].join(", "),
}

const isHttp = (value) => typeof value === "string" && /^https?:\/\//i.test(value)
const isRenderableImage = (value) =>
  isHttp(value) || (typeof value === "string" && (value.startsWith("/media/") || value.startsWith("/images/")))

export default function DestinationHero({
  destination,
  isFavorite = false,
  onToggleFavorite,
  onOpenReportModal,
  onOpenOfflineKit,
}) {
  const navigate = useNavigate()
  const reduced = useRef(false)
  const [bgIdx, setBgIdx] = useState(0)

  // Rotate through the destination's own photographs. Do not substitute a
  // different destination's image when the record has no verified media.
  const bgImages = useMemo(() => {
    if (!destination) return []
    const list = []
    const push = (value) => {
      if (isRenderableImage(value) && !list.includes(value)) list.push(value)
    }
    push(destination.cover_image_url || destination.cover_image)
    ;(destination.images || []).forEach(push)
    return list
  }, [destination])

  useEffect(() => {
    reduced.current = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false
  }, [])

  useEffect(() => {
    if (reduced.current || bgImages.length < 2) return undefined
    const timer = setInterval(() => setBgIdx((previous) => (previous + 1) % bgImages.length), 8000)
    return () => clearInterval(timer)
  }, [bgImages.length])

  if (!destination) return null

  const category = destination.category_name || destination.category?.name || "Nepal destination"
  const risk = destination.risk_analysis?.risk_category || destination.active_alert?.severity || INFO_UNAVAILABLE
  const stay = destination.recommended_days ? `${destination.recommended_days} days` : INFO_UNAVAILABLE
  const distance = destination.distance_from_kathmandu_km != null
    ? `${destination.distance_from_kathmandu_km} km`
    : INFO_UNAVAILABLE
  const location = placeLocationLabel(destination)
  const description = destination.short_description || destination.description || "Recorded destination information is available on this page."

  return (
    <section
      className="relative mb-8 flex min-h-[440px] w-full flex-col justify-end overflow-hidden rounded-[var(--ny-radius-lg)] bg-[var(--ny-green-deepest)] p-5 text-white shadow-[var(--ny-shadow-elevated)] sm:min-h-[520px] sm:p-8 lg:min-h-[560px] lg:p-10"
      aria-labelledby="destination-hero-title"
    >
      {bgImages.length > 0 && bgImages.map((src, index) => (
        <img
          key={src}
          src={src}
          alt={index === bgIdx ? destination.name : ""}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-1000 ${index === bgIdx ? "opacity-100" : "opacity-0"}`}
          style={{ objectPosition: FOCAL_CENTER }}
          loading={index === 0 ? "eager" : "lazy"}
          onError={(event) => { event.currentTarget.style.visibility = "hidden" }}
          aria-hidden={index !== bgIdx}
        />
      ))}

      {/* A quiet branded fallback remains useful when the record has no image. */}
      {bgImages.length === 0 && (
        <div className="pointer-events-none absolute inset-0 opacity-70" aria-hidden="true" style={{ background: "radial-gradient(circle at 75% 20%, rgba(99,230,190,.18), transparent 30%), linear-gradient(135deg, #063b32, #042a24 65%, #075b48)" }} />
      )}
      <div className="absolute inset-0" style={scrim} aria-hidden="true" />

      <div className="relative z-10 max-w-5xl space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex min-h-7 items-center rounded-full bg-[var(--ny-gold)] px-3 text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-green-deepest)]">
            {category}
          </span>
          {destination.province && (
            <span className="inline-flex items-center gap-1 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-white/90 backdrop-blur">
              <FiMapPin size={13} aria-hidden="true" /> {destination.province} Province
            </span>
          )}
          {destination.altitude && (
            <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-[var(--ny-gold)] backdrop-blur">
              {destination.altitude}
            </span>
          )}
        </div>

        <h1 id="destination-hero-title" className="!m-0 max-w-4xl !text-3xl !font-bold !text-white sm:!text-5xl">
          {destination.name}
        </h1>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-medium text-white/90">
          <span className="flex items-center gap-1.5 font-bold text-[var(--ny-mint)]">
            <FiMapPin size={15} aria-hidden="true" /> {location}
          </span>
          {destination.district && <span>District: <strong className="text-white">{destination.district}</strong></span>}
        </div>

        <p className="line-clamp-3 max-w-3xl text-sm leading-6 text-white/90 sm:text-base">{description}</p>

        <div className="grid grid-cols-2 gap-2 pt-2 sm:gap-3 lg:grid-cols-4">
          {[
            { label: "Recommended stay", value: stay, icon: FiClock },
            { label: "Best season", value: destination.best_time_to_visit || INFO_UNAVAILABLE, icon: FiSun },
            { label: "Distance from Kathmandu", value: distance, icon: FiCompass },
            { label: "Safety / risk", value: risk, icon: FiShield },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="min-w-0 rounded-[var(--ny-radius-md)] border border-white/15 bg-black/20 p-3 backdrop-blur">
              <span className="block text-[0.7rem] font-bold uppercase tracking-[0.08em] text-white/70">{label}</span>
              <span className="mt-1 flex items-center gap-1.5 text-sm font-bold text-white">
                <Icon className="h-4 w-4 shrink-0 text-[var(--ny-mint)]" aria-hidden="true" />
                <span className="truncate">{value}</span>
              </span>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t border-white/15 pt-4">
          <button
            type="button"
            onClick={() => navigate(`/itinerary?dest=${encodeURIComponent(destination.slug || destination.name)}`)}
            className="ny-btn ny-btn-accent"
          >
            <FiCompass size={17} aria-hidden="true" /> Plan this journey
          </button>
          <button
            type="button"
            onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)}
            className="ny-btn border-white/70 bg-white text-[var(--ny-green-deepest)] hover:border-white hover:bg-white/90"
          >
            <FiNavigation size={17} aria-hidden="true" /> Get road route
          </button>
          {onOpenOfflineKit && (
            <button type="button" onClick={onOpenOfflineKit} className="ny-btn border-white/25 bg-white/10 text-white hover:bg-white/20">
              Offline kit
            </button>
          )}
          {onOpenReportModal && (
            <button type="button" onClick={onOpenReportModal} className="ny-btn border-white/25 bg-white/10 text-white hover:bg-white/20">
              <FiAlertCircle size={16} aria-hidden="true" /> Report an issue
            </button>
          )}
          {onToggleFavorite && (
            <button
              type="button"
              onClick={onToggleFavorite}
              className={`ny-btn w-11 px-0 ${isFavorite ? "border-rose-300 bg-rose-500 text-white" : "border-white/25 bg-white/10 text-white hover:bg-white/20"}`}
              title={isFavorite ? "Remove from favourites" : "Save to favourites"}
              aria-label={isFavorite ? "Remove from favourites" : "Save to favourites"}
              aria-pressed={isFavorite}
            >
              <FiHeart size={19} className={isFavorite ? "fill-current" : ""} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
