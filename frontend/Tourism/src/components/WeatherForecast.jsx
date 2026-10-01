import { useState, useEffect, useCallback, useRef } from "react"
import {
  FiSun,
  FiCloud,
  FiCloudRain,
  FiCloudSnow,
  FiCloudDrizzle,
  FiCloudLightning,
  FiWind,
  FiDroplet,
  FiThermometer,
  FiRefreshCw,
  FiMapPin,
  FiAlertCircle,
} from "react-icons/fi"
import axiosClient from "../api/axiosClient"

const REFRESH_INTERVAL = 30 * 60 * 1000 // 30 minutes

const CONDITION_ICONS = {
  clear: FiSun,
  sunny: FiSun,
  "partly-cloudy": FiCloud,
  cloudy: FiCloud,
  overcast: FiCloud,
  rain: FiCloudRain,
  "light-rain": FiCloudDrizzle,
  drizzle: FiCloudDrizzle,
  snow: FiCloudSnow,
  thunderstorm: FiCloudLightning,
  wind: FiWind,
}

const CONDITION_LABELS = {
  clear: "Clear",
  sunny: "Sunny",
  "partly-cloudy": "Partly Cloudy",
  cloudy: "Cloudy",
  overcast: "Overcast",
  rain: "Rain",
  "light-rain": "Light Rain",
  drizzle: "Drizzle",
  snow: "Snow",
  thunderstorm: "Thunderstorm",
  wind: "Windy",
}

/**
 * 5-day weather forecast component for a destination.
 * Uses /api/v1/weather/forecast/ endpoint.
 * Auto-refreshes every 30 minutes.
 */
const WeatherForecast = ({ destinationSlug, destinationName, compact = false }) => {
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const intervalRef = useRef(null)

  const fetchForecast = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axiosClient.get("/weather/forecast/", {
        params: { destination: destinationSlug },
      })
      setForecast(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError(
        err?.response?.data?.message || "Unable to load weather forecast. Please try again later."
      )
    } finally {
      setLoading(false)
    }
  }, [destinationSlug])

  useEffect(() => {
    if (!destinationSlug) return undefined
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchForecast(), 0)
    intervalRef.current = setInterval(fetchForecast, REFRESH_INTERVAL)
    return () => {
      clearTimeout(t)
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [destinationSlug, fetchForecast])

  if (loading && !forecast) {
    return (
      <div className="ny-card p-5" role="status" aria-label="Loading weather forecast">
        <div className="ny-skeleton h-6 w-1/2 mb-4" />
        <div className="grid grid-cols-5 gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div className="ny-skeleton h-4 w-12" />
              <div className="ny-skeleton h-10 w-10 rounded-full" />
              <div className="ny-skeleton h-4 w-8" />
              <div className="ny-skeleton h-4 w-8" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="ny-card p-5" role="alert">
        <div className="flex items-center gap-2 text-ny-danger mb-3">
          <FiAlertCircle size={18} />
          <span className="font-semibold text-sm">Weather unavailable</span>
        </div>
        <p className="text-sm text-ny-text-secondary mb-3">{error}</p>
        <button
          onClick={fetchForecast}
          className="ny-btn ny-btn-secondary ny-btn-sm"
          type="button"
        >
          <FiRefreshCw size={14} /> Retry
        </button>
      </div>
    )
  }

  if (!forecast || !forecast.daily || forecast.daily.length === 0) {
    return (
      <div className="ny-card p-5">
        <div className="flex items-center gap-2 text-ny-text-secondary">
          <FiMapPin size={16} />
          <span className="text-sm">No forecast data available for this destination.</span>
        </div>
      </div>
    )
  }

  const daily = compact ? forecast.daily.slice(0, 3) : forecast.daily.slice(0, 5)

  return (
    <div className="ny-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-ny-text flex items-center gap-2">
            <FiThermometer size={18} className="text-ny-green" />
            {compact ? "Weather" : "5-Day Forecast"}
          </h3>
          {destinationName && (
            <p className="text-xs text-ny-text-muted mt-0.5 flex items-center gap-1">
              <FiMapPin size={12} /> {destinationName}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="text-xs text-ny-text-muted">
              Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
          <button
            onClick={fetchForecast}
            className="ny-btn ny-btn-ghost ny-btn-sm"
            type="button"
            aria-label="Refresh forecast"
            disabled={loading}
          >
            <FiRefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <div className={`grid gap-3 ${compact ? "grid-cols-3" : "grid-cols-2 sm:grid-cols-3 md:grid-cols-5"}`}>
        {daily.map((day, i) => {
          const Icon = CONDITION_ICONS[day.condition] || FiCloud
          const label = CONDITION_LABELS[day.condition] || day.condition || "Unknown"
          return (
            <div
              key={i}
              className="flex flex-col items-center gap-2 p-3 rounded-xl bg-ny-soft-green/50 border border-ny-border"
            >
              <span className="text-xs font-semibold text-ny-text-secondary">
                {new Date(day.date).toLocaleDateString("en-US", { weekday: "short" })}
              </span>
              <Icon size={compact ? 24 : 28} className="text-ny-green" />
              <div className="text-center">
                <span className="text-sm font-bold text-ny-text">{day.max_temp}°</span>
                <span className="text-xs text-ny-text-muted ml-1">{day.min_temp}°</span>
              </div>
              {!compact && (
                <div className="flex items-center gap-1 text-xs text-ny-text-muted">
                  <FiDroplet size={10} />
                  <span>{day.precipitation || 0}%</span>
                </div>
              )}
              <span className="text-xs text-ny-text-muted text-center">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default WeatherForecast
