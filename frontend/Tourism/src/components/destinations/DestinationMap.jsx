import { useState, useEffect } from "react"
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet"
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

function RecenterMap({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.setView(center, map.getZoom())
  }, [center, map])
  return null
}

/**
 * Interactive destination map with markers, popups,
 * layer controls, and fullscreen support.
 */
export default function DestinationMap({ destinations = [], center, onMarkerClick, className = "" }) {
  const [mapCenter, setMapCenter] = useState(center || [28.2096, 83.9856])
  const [selectedMarker, setSelectedMarker] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleMarkerClick = (dest) => {
    setSelectedMarker(dest)
    onMarkerClick?.(dest)
  }

  const toggleFullscreen = () => {
    setIsFullscreen(v => !v)
  }

  return (
    <div className={`relative ${isFullscreen ? "fixed inset-0 z-[100]" : "h-[400px] sm:h-[500px]"} rounded-2xl overflow-hidden ${className}`}>
      <MapContainer
        center={mapCenter}
        zoom={8}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <RecenterMap center={mapCenter} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {destinations.map((dest, i) => (
          <Marker
            key={dest.id || i}
            position={[dest.latitude || dest.lat, dest.longitude || dest.lng]}
            eventHandlers={{ click: () => handleMarkerClick(dest) }}
          >
            <Popup>
              <div className="p-1 min-w-[180px]">
                <p className="text-sm font-bold text-gray-900">{dest.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{dest.district || dest.province}</p>
                {dest.description && (
                  <p className="text-xs text-gray-600 mt-1.5 line-clamp-2">{dest.description}</p>
                )}
                <div className="flex items-center gap-2 mt-2">
                  {dest.rating && (
                    <span className="text-xs font-semibold text-amber-600">★ {dest.rating.toFixed(1)}</span>
                  )}
                  <button
                    type="button"
                    onClick={() => onMarkerClick?.(dest)}
                    className="text-xs text-[var(--ny-green)] font-semibold hover:underline"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map Controls */}
      <div className="absolute top-3 right-3 z-[500] flex flex-col gap-2">
        <button
          type="button"
          onClick={toggleFullscreen}
          className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          aria-label="Toggle fullscreen"
          title="Fullscreen"
        >
          <FiMaximize2 size={16} />
        </button>
        <button
          type="button"
          onClick={() => setMapCenter(center || [28.2096, 83.9856])}
          className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-lg text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          aria-label="Reset map"
          title="Reset view"
        >
          <FiLayers size={16} />
        </button>
      </div>

      {/* Selected Destination Info */}
      {selectedMarker && (
        <div className="absolute bottom-3 left-3 right-3 sm:right-auto sm:w-80 z-[500] bg-white dark:bg-slate-800 rounded-xl shadow-xl p-4 border border-[var(--ny-border)]">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h4 className="text-sm font-bold text-gray-900 dark:text-white truncate">{selectedMarker.name}</h4>
              <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5">
                <FiMapPin size={12} />
                {selectedMarker.district || selectedMarker.province}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedMarker(null)}
              className="p-1 rounded text-gray-400 hover:text-gray-600"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
          {selectedMarker.description && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">{selectedMarker.description}</p>
          )}
          <div className="flex items-center gap-2 mt-3">
            <button
              type="button"
              onClick={() => onMarkerClick?.(selectedMarker)}
              className="flex-1 px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
            >
              View Details
            </button>
            <button
              type="button"
              onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${selectedMarker.latitude || selectedMarker.lat},${selectedMarker.longitude || selectedMarker.lng}`, '_blank')}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              <FiNavigation size={12} />
              Directions
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
