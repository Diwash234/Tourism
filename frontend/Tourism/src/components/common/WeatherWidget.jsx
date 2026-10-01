import { useState, useEffect } from "react"
import { FiSun, FiCloud, FiCloudRain, FiCloudSnow, FiCloudDrizzle, FiWind } from "react-icons/fi"

/**
 * Weather widget showing current conditions for a destination.
 * Uses OpenWeatherMap API when key is configured, otherwise shows placeholder.
 */
export default function WeatherWidget({ lat, lng, destinationName }) {
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!lat || !lng) {
      setLoading(false)
      return
    }

    const fetchWeather = async () => {
      try {
        const apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY
        if (!apiKey) {
          setWeather({
            temp: 22,
            condition: "Sunny",
            humidity: 45,
            windSpeed: 5,
            icon: "sunny",
          })
          setLoading(false)
          return
        }

        const res = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lng}&appid=${apiKey}&units=metric`
        )
        if (!res.ok) throw new Error("Weather unavailable")
        const data = await res.json()

        const conditionMap = {
          "Clear": { icon: "sunny", label: "Sunny" },
          "Clouds": { icon: "cloudy", label: "Cloudy" },
          "Rain": { icon: "rain", label: "Rainy" },
          "Drizzle": { icon: "drizzle", label: "Drizzly" },
          "Thunderstorm": { icon: "rain", label: "Stormy" },
          "Snow": { icon: "snow", label: "Snowy" },
          "Mist": { icon: "cloudy", label: "Misty" },
          "Fog": { icon: "cloudy", label: "Foggy" },
        }

        const condition = conditionMap[data.weather[0].main] || { icon: "cloudy", label: data.weather[0].main }

        setWeather({
          temp: Math.round(data.main.temp),
          condition: condition.label,
          humidity: data.main.humidity,
          windSpeed: Math.round(data.wind.speed),
          icon: condition.icon,
        })
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [lat, lng])

  const getIcon = () => {
    if (!weather) return <FiCloud size={28} />
    switch (weather.icon) {
      case "sunny": return <FiSun size={28} className="text-amber-400" />
      case "cloudy": return <FiCloud size={28} className="text-gray-400" />
      case "rain": return <FiCloudRain size={28} className="text-blue-400" />
      case "drizzle": return <FiCloudDrizzle size={28} className="text-blue-300" />
      case "snow": return <FiCloudSnow size={28} className="text-cyan-200" />
      default: return <FiCloud size={28} />
    }
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-[var(--ny-border)] animate-pulse">
        <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mb-3" />
        <div className="h-8 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mb-2" />
        <div className="h-3 bg-gray-200 dark:bg-slate-700 rounded w-2/3" />
      </div>
    )
  }

  if (error || !weather) return null

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-[var(--ny-border)]">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Weather — {destinationName}
        </h4>
        {getIcon()}
      </div>
      <div className="flex items-end gap-2 mb-3">
        <span className="text-3xl font-bold text-gray-900 dark:text-white">{weather.temp}°C</span>
        <span className="text-sm text-gray-500 dark:text-gray-400 mb-1">{weather.condition}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex items-center gap-2">
          <FiCloud size={14} className="text-gray-400" />
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Humidity</p>
            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">{weather.humidity}%</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <FiWind size={14} className="text-gray-400" />
          <div>
            <p className="text-[10px] text-gray-400 uppercase">Wind</p>
            <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">{weather.windSpeed} m/s</p>
          </div>
        </div>
      </div>
    </div>
  )
}
