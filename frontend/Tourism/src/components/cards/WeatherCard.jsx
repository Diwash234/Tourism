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
const WeatherCard = ({ location, temp_c, condition, humidity, wind_kmh, loading = false }) => {
  const Icon = CONDITION_ICON[condition?.toLowerCase()] || FiCloud
  const hasWeather = temp_c != null || condition

  if (loading) {
    return <div className="ny-card h-36 overflow-hidden p-5" aria-label="Loading weather"><div className="ny-skeleton h-full w-full" /></div>
  }

  return (
    <div className="ny-card overflow-hidden p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-[var(--ny-text-secondary)]">{location || "Weather unavailable"}</p>
          <p className="mt-1 text-4xl font-bold text-[var(--ny-text)]">{hasWeather && temp_c != null ? `${temp_c}°C` : "—"}</p>
          <p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{hasWeather ? condition : "Enable location to load local weather"}</p>
        </div>
        <Icon size={36} className="shrink-0 text-[var(--ny-green)]" aria-hidden="true" />
      </div>

      {(humidity != null || wind_kmh != null) && (
        <div className="mt-4 flex items-center gap-5 border-t border-[var(--ny-border)] pt-4 text-sm text-[var(--ny-text-secondary)]">
          {humidity != null && <span className="flex items-center gap-1"><FiDroplet size={14} aria-hidden="true" />{humidity}%</span>}
          {wind_kmh != null && <span className="flex items-center gap-1"><FiWind size={14} aria-hidden="true" />{wind_kmh} km/h</span>}
        </div>
      )}
    </div>
  )
}

export default WeatherCard