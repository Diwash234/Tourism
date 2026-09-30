import { useState, useEffect } from "react"
import { FiSun, FiCloud, FiCloudRain, FiCloudSnow, FiWind, FiDroplets, FiThermometer } from "react-icons/fi"

/**
 * Weather widget showing current conditions for a destination.
 * Uses OpenWeatherMap API when key is configured, otherwise shows placeholder.
 */
export default function WeatherWidget({ lat, lng, destinationName }) {
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!lat || !lng) {
      setLoading(false)
      return
    }

    const apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY
    if (!apiKey) {
      setLoading(false)
      return
    }

    const fetchWeather = async () => {
      try {
        const res = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lng}&appid=${apiKey}&units=metric`
        )
        if (!res.ok) throw new Error("Weather unavailable")
        const data = await res.json()
        setWeather({
          temp: Math.round(data.main.temp),
          feelsLike: Math.round(data.main.feels_like),
          humidity: data.main.humidity,
          windSpeed: data.wind.speed,
          description: data.weather[0]?.description || "",
          icon: data.weather[0]?.icon || "01d",
        })
      } catch (err) {
        console.error("Weather fetch failed:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [lat, lng])

  const getIcon = (iconCode) => {
    if (!iconCode) <FiCloud size={32} />
    if (iconCode.includes("01")) return <FiSun size={32} className="text-amber-400" />
    if (iconCode.includes("02") || iconCode.includes("03") || iconCode.includes("04")) return <FiCloud size={32} className="text-gray-400" />
    if (iconCode.includes("09") || iconCode.includes("10")) return <FiCloudRain size={32} className="text-blue-400" />
    if (iconCode.includes("13")) return <FiCloudSnow size={32} className="text-cyan-200" />
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

  if (!weather) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-2">Weather</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Weather data is not available for {destinationName || "this location"}. Check local conditions before traveling.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Weather</h3>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">{destinationName}</span>
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
