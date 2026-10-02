import { useState, useEffect } from "react"
import axiosClient from "../../api/axiosClient"
import { FiSun, FiCloud, FiCloudRain, FiCloudSnow, FiWind, FiDroplets, FiThermometer } from "react-icons/fi"

/**
 * Weather widget showing current conditions for a destination.
 * Uses OpenWeatherMap API when key is configured, otherwise shows placeholder.
 */
export default function DestinationWeather({ lat, lng, destinationName: _destinationName }) {
  const [weather, setWeather] = useState(null)
  // Start in the loading state only when there is something to fetch, so the
  // effect below never has to set state synchronously.
  const [loading, setLoading] = useState(Boolean(lat && lng))
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!lat || !lng) {
      return
    }

    const fetchWeather = async () => {
      try {
        const { data } = await axiosClient.get("/weather/", { params: { lat, lon: lng, days: 3 } })
        if (!data?.available || !data?.current) throw new Error(data?.reason || "Weather unavailable")
        const code = Number(data.current.weather_code)
        const icon = code === 0 ? "01d" : code <= 3 ? "03d" : code >= 71 && code <= 86 ? "13d" : code >= 51 && code <= 82 ? "10d" : code >= 95 ? "11d" : "02d"
        setWeather({
          temp: Math.round(Number(data.current.temperature_c)),
          feelsLike: Math.round(Number(data.current.apparent_temperature_c)),
          humidity: Number(data.current.relative_humidity_pct),
          windSpeed: Number(data.current.wind_speed_kmh) / 3.6,
          description: data.current.description || "Current conditions",
          icon,
          city: data.coordinates?.timezone || "Nepal",
        })
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [lat, lng])

  const getIcon = (iconCode) => {
    if (!iconCode) return <FiCloud size={32} />
    if (iconCode.includes("01")) return <FiSun size={32} className="text-amber-400" />
    if (iconCode.includes("02") || iconCode.includes("03") || iconCode.includes("04")) return <FiCloud size={32} className="text-gray-400" />
    if (iconCode.includes("09") || iconCode.includes("10")) return <FiCloudRain size={32} className="text-blue-400" />
    if (iconCode.includes("13")) return <FiCloudSnow size={32} className="text-blue-200" />
    return <FiCloud size={32} />
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5 animate-pulse">
        <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mb-3" />
        <div className="h-8 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mb-2" />
        <div className="h-3 bg-gray-200 dark:bg-slate-700 rounded w-2/3" />
      </div>
    )
  }

  if (error || !weather) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-2">Weather</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Weather data is not available for this location. Check local conditions before traveling.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Weather</h3>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">{weather.city}</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex-shrink-0">{getIcon(weather.icon)}</div>
        <div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{weather.temp}°C</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{weather.description}</p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-[var(--ny-border)]">
        <div className="text-center">
          <FiThermometer size={14} className="mx-auto text-gray-400 mb-1" />
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">{weather.feelsLike}°</p>
          <p className="text-[10px] text-gray-400">Feels like</p>
        </div>
        <div className="text-center">
          <FiDroplets size={14} className="mx-auto text-blue-400 mb-1" />
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">{weather.humidity}%</p>
          <p className="text-[10px] text-gray-400">Humidity</p>
        </div>
        <div className="text-center">
          <FiWind size={14} className="mx-auto text-gray-400 mb-1" />
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">{weather.windSpeed} m/s</p>
          <p className="text-[10px] text-gray-400">Wind</p>
        </div>
      </div>
    </div>
  )
}
