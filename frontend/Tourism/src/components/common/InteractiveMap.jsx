import { useState, useEffect, useCallback } from "react"
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from "react-leaflet"
import { FiNavigation, FiMapPin, FiLayers, FiMaximize2 } from "react-icons/fi"
import "leaflet/dist/leaflet.css"

// Fix Leaflet default marker icons
import L from "leaflet"
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
})

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => onMapClick?.(e.latlng),
  })
  return null
}

function RecenterMap({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.setView(center, map.getZoom())
  }, [center, map])
  return null
}

/**
 * Interactive map component with:
 * - Click to select location
 * - Custom markers
 * - Layer toggle (street/satellite)
 * - Fullscreen support
 * - User location button
 */
export default function InteractiveMap({
  destinations = [],
  center = [28.2096, 83.9856],
  zoom = 8,
  onLocationSelect,
  onMarkerClick,
  height = "400px",
  showControls = true,
  className = "",
}) {
  const [mapCenter, setMapCenter] = useState(center)
  const [userLocation, setUserLocation] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [layer, setLayer] = useState("street")
  const [mapInstance, setMapInstance] = useState(null)

  const handleMapClick = useCallback((latlng) => {
    setMapCenter([latlng.lat, latlng.lng])
    onLocationSelect?.(latlng)
  }, [onLocationSelect])

  const handleUserLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser")
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = [pos.coords.latitude, pos.coords.longitude]
        setUserLocation(loc)
        setMapCenter(loc)
      },
      () => alert("Unable to retrieve your location")
    )
  }

  const toggleFullscreen = () => {
    setIsFullscreen(v => !v)
  }

  const layers = {
    street: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  }

  return (
    <div className={`relative ${isFullscreen ? "fixed inset-0 z-[100]" : ""} ${className}`}>
      {showControls && (
        <div className="absolute top-3 right-3 z-[500] flex flex-col gap-2">
          <button
            type="button"
            onClick={handleUserLocation}
            className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg text-gray-600 dark:text-gray-400 hover:text-[var(--ny-green)] transition-colors"
            aria-label="Use my location"
            title="My location"
          >
            <FiNavigation size={18} />
          </button>
          <button
            type="button"
            onClick={() => setLayer(l => l === "street" ? "satellite" : "street")}
            className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg text-gray-600 dark:text-gray-400 hover:text-[var(--ny-green)] transition-colors"
            aria-label="Toggle map layer"
            title="Toggle layer"
          >
            <FiLayers size={18} />
          </button>
          <button
            type="button"
            onClick={toggleFullscreen}
            className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg text-gray-600 dark:text-gray-400 hover:text-[var(--ny-green)] transition-colors"
            aria-label="Toggle fullscreen"
            title="Fullscreen"
          >
            <FiMaximize2 size={18} />
          </button>
        </div>
      )}

      <MapContainer
        center={mapCenter}
        zoom={zoom}
        className="w-full"
        style={{ height: isFullscreen ? "100vh" : height }}
        ref={setMapInstance}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url={layers[layer]}
        />
        <MapClickHandler onMapClick={handleMapClick} />
        <RecenterMap center={mapCenter} />

        {userLocation && (
          <Marker position={userLocation} icon={L.divIcon({ className: "bg-blue-500 w-4 h-4 rounded-full border-2 border-white shadow-lg", iconSize: [16, 16] })}>
            <Popup>You are here</Popup>
          </Marker>
        )}

        {destinations.map((dest, i) => (
          <Marker
            key={dest.id || i}
            position={[dest.latitude || dest.lat, dest.longitude || dest.lng]}
            eventHandlers={{ click: () => onMarkerClick?.(dest) }}
          >
            <Popup>
              <div className="p-1 min-w-[160px]">
                <p className="text-sm font-bold text-gray-900">{dest.name}</p>
                {dest.description && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">{dest.description}</p>
                )}
                {dest.rating && (
                  <p className="text-xs text-amber-600 mt-1">★ {dest.rating.toFixed(1)}</p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
