import { Link } from "react-router-dom"
import { FiArrowRight, FiHeart, FiMapPin, FiNavigation, FiShield, FiStar } from "react-icons/fi"
import { motion } from "framer-motion"
import PlaceholderImage from "../common/PlaceholderImage"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import { placeLocationLabel } from "../../utils/placeUtils"

const RISK_LABELS = { low: "Low risk", moderate: "Moderate risk", high: "High risk", critical: "Critical risk" }

const DestinationCard = ({ destination = {}, onToggleFavorite, isFavorite = false }) => {
  const {
    id,
    name = "Unnamed destination",
    slug,
    city,
    average_rating,
    entry_fee,
    budget_estimate,
    category_name,
    district,
    province,
    latitude,
    longitude,
    risk_level,
    recommended_season,
    distance_km,
    distance,
  } = destination
  const imageUrl = getDestinationImageUrl(destination)
  const location = placeLocationLabel({ display_city: destination.display_city, city, district, municipality: destination.municipality, province })
  const hasCoordinates = latitude != null && longitude != null && Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude))
  const distanceValue = Number(distance_km ?? distance)

  return (
    <motion.article
      layout
      whileHover={{ y: -3 }}
      transition={{ duration: 0.18 }}
      className="ny-card group flex h-full flex-col overflow-hidden"
      data-testid="destination-card"
    >
      <div className="relative h-48 overflow-hidden bg-[#EAF1EE]">
        <PlaceholderImage src={imageUrl} title={name} alt={name} className="h-full w-full transition-transform duration-300 group-hover:scale-[1.03]" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-black/5 to-transparent" aria-hidden="true" />
        {category_name && <span className="absolute bottom-3 left-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold text-[var(--ny-green)]">{category_name}</span>}
        {average_rating != null && (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-1 text-xs font-semibold text-[var(--ny-text)]">
            <FiStar size={13} className="fill-[var(--ny-gold)] text-[var(--ny-warm-gold)]" aria-hidden="true" />
            {average_rating}
          </span>
        )}
        {onToggleFavorite && (
          <button
            type="button"
            onClick={() => onToggleFavorite(id)}
            className="absolute right-3 top-3 grid h-11 w-11 place-items-center rounded-full bg-white/95 text-[var(--ny-text-secondary)] transition hover:bg-white hover:text-[var(--ny-green)]"
            aria-label={isFavorite ? `Remove ${name} from saved places` : `Save ${name}`}
            title={isFavorite ? "Remove from saved places" : "Save place"}
          >
            <FiHeart size={18} className={isFavorite ? "fill-[var(--ny-danger)] text-[var(--ny-danger)]" : ""} aria-hidden="true" />
          </button>
        )}
      </div>

      <div className="flex flex-1 flex-col p-5">
        <h3 className="truncate text-lg font-bold text-[var(--ny-text)]" title={name}>{name}</h3>
        {location && <p className="mt-1 flex items-center gap-1.5 text-sm text-[var(--ny-text-secondary)]"><FiMapPin size={14} className="shrink-0 text-[var(--ny-green)]" aria-hidden="true" /><span className="truncate">{location}</span></p>}

        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm text-[var(--ny-text-secondary)]">
          {Number.isFinite(distanceValue) && <span className="inline-flex items-center gap-1.5 text-[var(--ny-green)]"><FiNavigation size={14} aria-hidden="true" />{distanceValue.toFixed(1)} km away</span>}
          {recommended_season && <span className="inline-flex items-center gap-1.5"><span className="text-[var(--ny-text-muted)]">Best time</span><strong className="font-semibold text-[var(--ny-text)]">{recommended_season}</strong></span>}
          {risk_level && <span className="inline-flex items-center gap-1.5"><FiShield size={14} className="text-[var(--ny-green)]" aria-hidden="true" />{RISK_LABELS[risk_level] || risk_level}</span>}
          {(budget_estimate != null || entry_fee != null) && <span className="font-semibold text-[var(--ny-green)]">{budget_estimate != null ? `NPR ${budget_estimate}` : `NPR ${entry_fee}`}</span>}
        </div>

        <div className="mt-auto pt-5">
          {slug ? (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <Link to={`/destinations/${slug}`} className="ny-btn ny-btn-primary min-h-11 px-3 text-sm">Explore <FiArrowRight size={15} aria-hidden="true" /></Link>
              {hasCoordinates && <Link to={`/navigation?dest=${encodeURIComponent(name)}`} className="ny-btn ny-btn-secondary min-h-11 px-3 text-sm"><FiNavigation size={15} aria-hidden="true" />Directions</Link>}
            </div>
          ) : (
            <p className="rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] px-3 py-2 text-sm text-[var(--ny-text-secondary)]">Details are not available yet.</p>
          )}
        </div>
      </div>
    </motion.article>
  )
}

export default DestinationCard
