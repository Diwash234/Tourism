import { useState, useEffect, useCallback, useRef } from "react"
import {
  FiMapPin,
  FiClock,
  FiTrash2,
  FiRefreshCw,
  FiNavigation,
  FiAlertCircle,
  FiCheckCircle,
} from "react-icons/fi"
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet"
import axiosClient from "../api/axiosClient"

/**
 * Location history component showing user's recent locations on a map
 * with a timeline view. Uses /api/v1/location-history/ endpoint.
 */
const LocationHistory = ({ maxItems = 20, showMap = true }) => {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [clearing, setClearing] = useState(false)
  const mapRef = useRef(null)

  const fetchHistory = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axiosClient.get("/location-history/", {
        params: { limit: maxItems },
      })
      setHistory(data?.results || data || [])
    } catch (err) {
      setError(
        err?.response?.data?.message || "Unable to load location history. Please try again later."
      )
    } finally {
      setLoading(false)
    }
  }, [maxItems])

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory])

  const clearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all location history?")) return
    setClearing(true)
    try {
      await axiosClient.delete("/location-history/clear/")
      setHistory([])
      setSelectedId(null)
    } catch (err) {
      setError(
        err?.response?.data?.message || "Failed to clear history. Please try again."
      )
    } finally {
      setClearing(false)
    }
  }

  const getAccuracyColor = (accuracy) => {
    if (!accuracy) return "text-ny-text-muted"
    if (accuracy <= 50) return "text-green-600"
    if (accuracy <= 200) return "text-amber-600"
    return "text-red-600"
  }

  const getAccuracyIcon = (accuracy) => {
    if (!accuracy) return null
    if (accuracy <= 50) return <FiCheckCircle size={12} />
    return <FiAlertCircle size={12} />
  }

  const formatTimestamp = (ts) => {
    if (!ts) return "Unknown"
    const d = new Date(ts)
    const now = new Date()
    const diffMs = now - d
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  }

  if (loading) {
    return (
      <div className="ny-card p-5" role="status" aria-label="Loading location history">
        <div className="ny-skeleton h-6 w-1/3 mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="ny-skeleton h-8 w-8 rounded-full" />
              <div className="flex-1">
                <div className="ny-skeleton h-4 w-1/2 mb-1" />
                <div className="ny-skeleton h-3 w-1/3" />
              </div>
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
          <span className="font-semibold text-sm">Error loading history</span>
        </div>
        <p className="text-sm text-ny-text-secondary mb-3">{error}</p>
        <button onClick={fetchHistory} className="ny-btn ny-btn-secondary ny-btn-sm" type="button">
          <FiRefreshCw size={14} /> Retry
        </button>
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="ny-card p-5">
        <div className="ny-empty">
          <span className="ny-empty-icon"><FiMapPin size={24} /></span>
          <h3>No location history</h3>
          <p>Your visited locations will appear here as you explore.</p>
        </div>
      </div>
    )
  }

  const selectedItem = history.find((h) => h.id === selectedId)
  const mapCenter = selectedItem
    ? [selectedItem.latitude, selectedItem.longitude]
    : history.length > 0
    ? [history[0].latitude, history[0].longitude]
    : [28.3949, 84.124] // Nepal default

  return (
    <div className="ny-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-ny-text flex items-center gap-2">
          <FiClock size={18} className="text-ny-green" />
          Location History
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchHistory}
            className="ny-btn ny-btn-ghost ny-btn-sm"
            type="button"
            aria-label="Refresh history"
          >
            <FiRefreshCw size={14} />
          </button>
          <button
            onClick={clearHistory}
            disabled={clearing}
            className="ny-btn ny-btn-danger ny-btn-sm"
            type="button"
          >
            <FiTrash2 size={14} /> {clearing ? "Clearing..." : "Clear"}
          </button>
        </div>
      </div>

      {showMap && (
        <div className="mb-4 rounded-xl overflow-hidden border border-ny-border" style={{ height: 250 }}>
          <MapContainer
            center={mapCenter}
            zoom={10}
            style={{ height: "100%", width: "100%" }}
            ref={mapRef}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {history.map((item) => (
              <Marker
                key={item.id}
                position={[item.latitude, item.longitude]}
                eventHandlers={{ click: () => setSelectedId(item.id) }}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-semibold">{item.city || item.address || "Unknown location"}</p>
                    <p className="text-xs text-gray-500">{formatTimestamp(item.timestamp)}</p>
                    {item.accuracy && (
                      <p className="text-xs text-gray-500">Accuracy: ±{Math.round(item.accuracy)}m</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}
            {selectedItem && selectedItem.accuracy && (
              <Circle
                center={[selectedItem.latitude, selectedItem.longitude]}
                radius={selectedItem.accuracy}
                pathOptions={{ color: "#075B48", fillOpacity: 0.1 }}
              />
            )}
          </MapContainer>
        </div>
      )}

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {history.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setSelectedId(item.id)}
            className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-colors text-left ${
              selectedId === item.id
                ? "border-ny-green bg-ny-soft-green"
                : "border-ny-border hover:border-ny-green/50"
            }`}
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-ny-soft-green flex items-center justify-center">
              <FiNavigation size={14} className="text-ny-green" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-ny-text truncate">
                {item.city || item.address || "Unknown location"}
              </p>
              <p className="text-xs text-ny-text-muted">{formatTimestamp(item.timestamp)}</p>
            </div>
            {item.accuracy && (
              <div className={`flex items-center gap-1 text-xs font-medium ${getAccuracyColor(item.accuracy)}`}>
                {getAccuracyIcon(item.accuracy)}
                <span>±{Math.round(item.accuracy)}m</span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}

export default LocationHistory
