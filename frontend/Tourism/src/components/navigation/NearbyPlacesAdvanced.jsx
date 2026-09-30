import { useState, useEffect, useCallback } from "react"
import { FiMapPin, FiNavigation, FiRefreshCw, FiAlertTriangle, FiClock, FiStar } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { useAuth } from "../../hooks/useAuth"
import { nearbyApi } from "../../api/nearbyApi"
import DestinationMap from "../destinations/DestinationMap"
import Badge from "../common/Badge"

/**
 * Advanced nearby places explorer with:
 * - GPS-based or manual location selection
 * - Multiple result types (destinations, POIs, hotels, hospitals)
 * - Radius selection
 * - Map integration
 * - Sort by distance/rating
 * - Safety alerts display
 */
export default function NearbyPlacesAdvanced() {
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const [location, setLocation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState("destinations")
  const [radius, setRadius] = useState(25)
  const [results, setResults] = useState({ destinations: [], hotels: [], hospitals: [], pois: [] })
  const [sortBy, setSortBy] = useState("distance")

  const tabs = [
    { key: "destinations", label: "Destinations" },
    { key: "pois", label: "Real-world Places" },
    { key: "hotels", label: "Hotels" },
    { key: "hospitals", label: "Hospitals" },
  ]

  const fetchNearby = useCallback(async (lat, lng) => {
    setLoading(true)
    setError(null)
    try {
      const data = await nearbyApi.getNearbyPlaces(lat, lng, radius)
      setResults(data)
    } catch (err) {
      setError(err.message || "Failed to fetch nearby places")
    } finally {
      setLoading(false)
    }
  }, [radius])

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser")
      return
    }
    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        setLocation(loc)
        fetchNearby(loc.lat, loc.lng)
      },
      (err) => {
        setError("Unable to get your location. Please check browser permissions.")
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }

  const handleMapClick = (lat, lng) => {
    const loc = { lat, lng }
    setLocation(loc)
    fetchNearby(lat, lng)
  }

  const currentResults = results[activeTab] || []
  const sortedResults = [...currentResults].sort((a, b) => {
    if (sortBy === "distance") return (a.distance_km || 0) - (b.distance_km || 0)
    if (sortBy === "rating") return (b.rating || 0) - (a.rating || 0)
    return 0
  })

  return (
    <div className="space-y-6">
      {/* Location Controls */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <FiMapPin className="text-[var(--ny-green)]" />
              {t("nearby.page_title")}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {location
                ? `${t("nearby.searching_from")}: ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`
                : t("nearby.location_not_set")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              className="text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300"
            >
              <option value={5}>5 km</option>
              <option value={10}>10 km</option>
              <option value={25}>25 km</option>
              <option value={50}>50 km</option>
              <option value={100}>100 km</option>
            </select>
            <button
              type="button"
              onClick={handleUseLocation}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors disabled:opacity-50"
            >
              {loading ? <FiRefreshCw className="animate-spin" size={16} /> : <FiNavigation size={16} />}
              {t("nearby.use_my_location")}
            </button>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-xl p-4 flex items-start gap-3">
          <FiAlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <div>
            <p className="text-sm font-semibold text-red-800 dark:text-red-200">{error}</p>
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
              You can still click on the map to select a starting point.
            </p>
          </div>
        </div>
      )}

      {/* Map */}
      <DestinationMap
        destinations={sortedResults}
        center={location}
        onMapClick={handleMapClick}
        height="400px"
      />

      {/* Tabs & Results */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between border-b border-[var(--ny-border)] px-4">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? "border-[var(--ny-green)] text-[var(--ny-green)]"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}
              >
                {tab.label}
                {results[tab.key]?.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
                    {results[tab.key].length}
                  </span>
                )}
              </button>
            ))}
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 hidden sm:block"
          >
            <option value="distance">Sort by Distance</option>
            <option value="rating">Sort by Rating</option>
          </select>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <FiRefreshCw className="animate-spin text-[var(--ny-green)]" size={24} />
              <span className="ml-2 text-sm text-gray-500">{t("nearby.finding")}</span>
            </div>
          ) : sortedResults.length === 0 ? (
            <div className="text-center py-12">
              <FiMapPin className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {location ? t("nearby.nothing_title") : t("nearby.location_not_set")}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sortedResults.map((place, i) => (
                <div
                  key={place.id || i}
                  className="flex items-center justify-between p-4 rounded-xl border border-[var(--ny-border)] hover:border-[var(--ny-green)] hover:shadow-sm transition-all"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--ny-soft-green)] text-[var(--ny-green)] shrink-0">
                      <FiMapPin size={18} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{place.name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {place.distance_km?.toFixed(1)} km
                        </span>
                        {place.rating && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-600">
                            <FiStar size={10} className="fill-amber-400" />
                            {place.rating.toFixed(1)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${place.latitude || place.lat},${place.longitude || place.lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
                    >
                      <FiNavigation size={12} />
                      Directions
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
