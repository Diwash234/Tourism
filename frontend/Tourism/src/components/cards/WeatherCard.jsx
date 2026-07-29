import { FiSun, FiCloud, FiCloudRain, FiCloudSnow, FiWind, FiDroplet } from "react-icons/fi"

const CONDITION_ICON = {
  sunny: FiSun,
  clear: FiSun,
  cloudy: FiCloud,
  rain: FiCloudRain,
  snow: FiCloudSnow,
}

/**
 * WeatherCard
 * props: { location, temp_c, condition, humidity, wind_kmh, loading }
 */
const WeatherCard = ({ location, temp_c, condition = "clear", humidity, wind_kmh, loading = false }) => {
  const Icon = CONDITION_ICON[condition?.toLowerCase()] || FiSun

  if (loading) {
    return <div className="card-base p-5 h-32 skeleton" />
  }

  return (
    <div className="card-base p-5 bg-gradient-to-br from-himalaya-500 to-himalaya-700 text-white">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-white/80">{location || "Current location"}</p>
          <p className="text-4xl font-bold mt-1">{temp_c != null ? `${temp_c}°C` : "--"}</p>
          <p className="text-sm text-white/80 capitalize mt-1">{condition}</p>
        </div>
        <Icon size={40} className="text-saffron-300" />
      </div>

      {(humidity != null || wind_kmh != null) && (
        <div className="flex items-center gap-5 mt-4 pt-4 border-t border-white/20 text-sm text-white/90">
          {humidity != null && (
            <span className="flex items-center gap-1">
              <FiDroplet size={14} /> {humidity}%
            </span>
          )}
          {wind_kmh != null && (
            <span className="flex items-center gap-1">
              <FiWind size={14} /> {wind_kmh} km/h
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default WeatherCard