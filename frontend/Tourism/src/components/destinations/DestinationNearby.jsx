import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiMapPin, FiNavigation, FiStar } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { destinationApi } from "../../services/destinationService"
import LazyImage from "../common/LazyImage"
import Badge from "../common/Badge"

/**
 * Nearby destinations component - shows places close to the current destination.
 * Includes distance, rating, and quick navigation links.
 */
export default function DestinationNearby({ destination, radius = 50 }) {
  const { t: _t } = useTranslation()
  const [nearby, setNearby] = useState([])
  // Start in the loading state only when there is something to fetch, so the
  // effect below never has to set state synchronously.
  const [loading, setLoading] = useState(
    () => Boolean(destination?.latitude) && Boolean(destination?.longitude)
  )

  useEffect(() => {
    if (!destination?.latitude || !destination?.longitude) {
      return
    }

    const fetchNearby = async () => {
      try {
        const data = await destinationApi.getNearby(
          destination.latitude,
          destination.longitude,
          radius
        )
        setNearby(data.filter(d => d.id !== destination.id).slice(0, 6))
      } catch (err) {
        console.error("Failed to fetch nearby destinations:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchNearby()
  }, [destination, radius])

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 animate-pulse">
            <div className="h-16 w-16 rounded-lg bg-gray-200 dark:bg-slate-600" />
            <div className="flex-1 space-y-2">
              <div className="h-3 bg-gray-200 dark:bg-slate-600 rounded w-2/3" />
              <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded w-1/3" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (nearby.length === 0) return null

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FiMapPin size={16} className="text-[var(--ny-green)]" />
          Nearby Places
        </h3>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">Within {radius} km</span>
      </div>

      <div className="space-y-3">
        {nearby.map((place) => (
          <Link
            key={place.id}
            to={`/destinations/${place.slug || place.id}`}
            className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors group"
          >
            <div className="h-16 w-16 rounded-lg overflow-hidden bg-gray-100 dark:bg-slate-700 shrink-0">
              <LazyImage
                src={place.image_url || place.images?.[0]?.src || "/placeholder-destination.jpg"}
                alt={place.name}
                className="w-full h-full group-hover:scale-105 transition-transform duration-300"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 dark:text-white truncate group-hover:text-[var(--ny-green)] transition-colors">
                {place.name}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <FiNavigation size={10} />
                  {place.distance_km?.toFixed(1)} km
                </span>
                {place.rating && (
                  <span className="text-xs text-amber-600 flex items-center gap-0.5">
                    <FiStar size={10} className="fill-amber-400" />
                    {place.rating.toFixed(1)}
                  </span>
                )}
              </div>
              {place.category && (
                <Badge variant="primary" size="sm" className="mt-1.5">{place.category}</Badge>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
