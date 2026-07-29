import { Link } from "react-router-dom"
import { FiMapPin, FiStar, FiHeart, FiThermometer, FiDollarSign } from "react-icons/fi"
import { motion } from "framer-motion"

const RISK_STYLES = {
  low: { label: "Low Risk", dot: "bg-forest-500", className: "badge-risk-low" },
  moderate: { label: "Moderate Risk", dot: "bg-saffron-500", className: "badge-risk-moderate" },
  high: { label: "High Risk", dot: "bg-nepalred-500", className: "badge-risk-high" },
}

/**
 * DestinationCard
 * Backward compatible with the original API (id, name, slug, city, country,
 * cover_image_url, average_rating, entry_fee, distance_km) and additive:
 * pass `weather`, `budget_estimate`, `risk_level`, `recommended_season`,
 * and `category` when the API provides them; sensible fallbacks are shown
 * otherwise so this never breaks existing callers.
 */
const DestinationCard = ({
  destination,
  onToggleFavorite,
  isFavorite = false,
}) => {
  const {
    id,
    name,
    slug,
    city,
    country,
    cover_image_url,
    average_rating,
    entry_fee,
    distance_km,
    category,
    weather, // e.g. { temp_c: 22, condition: "Sunny" }
    budget_estimate, // e.g. 300
    risk_level, // "low" | "moderate" | "high"
    recommended_season, // e.g. "March - May"
  } = destination

  const risk = RISK_STYLES[risk_level] || RISK_STYLES.low

  return (
    <motion.div
      whileHover={{ y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="card-base overflow-hidden group"
    >
      <div className="relative h-48 overflow-hidden">
        <img
          src={
            cover_image_url ||
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"
          }
          alt={name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />

        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/0 to-black/0" />

        <button
          onClick={() => onToggleFavorite?.(id)}
          className="absolute top-3 right-3 bg-white/90 p-2 rounded-full hover:bg-white transition-colors"
        >
          <FiHeart className={isFavorite ? "text-nepalred-500 fill-nepalred-500" : "text-gray-600"} />
        </button>

        <div className="absolute top-3 left-3 flex items-center gap-1 bg-white/95 px-2.5 py-1 rounded-full text-sm font-semibold text-saffron-600">
          <FiStar className="fill-saffron-500 text-saffron-500" size={14} />
          {average_rating || "0"}
        </div>

        {category && (
          <span className="absolute bottom-3 left-3 text-xs font-semibold text-white bg-himalaya-500/90 px-2.5 py-1 rounded-full capitalize">
            {category}
          </span>
        )}
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-3 mb-1">
          <div className="min-w-0">
            <h3 className="font-bold text-dark text-lg truncate">{name}</h3>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <FiMapPin size={14} />
              {city}
              {country ? `, ${country}` : ""}
              {distance_km != null && (
                <span className="text-gray-400">· {distance_km} km away</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 my-3 text-sm text-gray-600">
          {weather && (
            <span className="flex items-center gap-1">
              <FiThermometer className="text-himalaya-500" size={14} />
              {weather.temp_c}°C
            </span>
          )}
          <span className="flex items-center gap-1 font-semibold text-forest-600">
            <FiDollarSign size={14} />
            {budget_estimate != null ? `$${budget_estimate} est.` : `NPR ${entry_fee || 0}`}
          </span>
          <span className={`flex items-center gap-1 ${risk.className}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${risk.dot}`} />
            {risk.label}
          </span>
        </div>

        {recommended_season && (
          <p className="text-xs text-gray-400 mb-3">
            Recommended: <span className="text-gray-600 font-medium">{recommended_season}</span>
          </p>
        )}

        {slug ? (
          <Link
            to={`/destinations/${slug}`}
            className="btn-gradient w-full flex items-center justify-center text-sm"
          >
            Explore Now
          </Link>
        ) : (
          <button
            disabled
            title="This destination is missing a slug from the API — check the backend response"
            className="w-full flex items-center justify-center text-sm font-semibold px-5 py-2.5 rounded-xl bg-gray-100 text-gray-400 cursor-not-allowed"
          >
            Details unavailable
          </button>
        )}
      </div>
    </motion.div>
  )
}

export default DestinationCard