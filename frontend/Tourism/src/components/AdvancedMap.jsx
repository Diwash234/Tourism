import { useEffect, useState, useCallback, useMemo, useRef } from "react"
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents, ZoomControl } from "react-leaflet"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiLayers, FiMapPin, FiDownload, FiMaximize2, FiMinimize2,
  FiNavigation, FiGrid, FiList, FiFilter,
} from "react-icons/fi"
import { destinationIcon, userIcon } from "./map/icons"
import { DEFAULT_MAP_CENTER } from "../utils/constants"

// ─── Tile Layer Providers ────────────────────────────────────────────────────
const TILE_PROVIDERS = {
  street: {
    name: "Street",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr: "&copy; OpenStreetMap contributors",
  },
  satellite: {
    name: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr: "Tiles &copy; Esri",
  },
  terrain: {
    name: "Terrain",
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr: "Map data: &copy; OpenStreetMap contributors, SRTM",
  },
}

// ─── Marker Clustering (simple grid-based) ────────────────────────────────────
const clusterMarkers = (markers, zoom) => {
  const gridSize = 0.5 / Math.pow(2, zoom - 10)
  const clusters = {}

  markers.forEach((marker) => {
    const key = `${Math.floor(marker.lat / gridSize)}-${Math.floor(marker.lng / gridSize)}`
    if (!clusters[key]) {
      clusters[key] = { lat: 0, lng: 0, count: 0, markers: [] }
    }
    clusters[key].lat += marker.lat
    clusters[key].lng += marker.lng
    clusters[key].count += 1
    clusters[key].markers.push(marker)
  })

  return Object.values(clusters).map((cluster) => ({
    lat: cluster.lat / cluster.count,
    lng: cluster.lng / cluster.count,
    count: cluster.count,
    markers: cluster.markers,
  }))
}

// ─── Heatmap Layer (simple circle markers) ───────────────────────────────────
const HeatmapLayer = ({ points }) => {
  const map = useMap()

  useEffect(() => {
    // In production, use leaflet.heat plugin
    // This is a simplified visualization
  }, [points, map])

  return (
    <>
      {points.map((point, i) => (
        <Marker
          key={i}
          position={[point.lat, point.lng]}
          icon={L.divIcon({
            className: "heatmap-point",
            html: `<div style="width:20px;height:20px;border-radius:50%;background:rgba(255,0,0,0.3);border:2px solid rgba(255,0,0,0.6);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          })}
        />
      ))}
    </>
  )
}

// ─── Drawing Tools (Measure Distance) ────────────────────────────────────────
const DrawingTool = ({ active, onPointsChange }) => {
  const [points, setPoints] = useState([])
  const map = useMapEvents({
    click(e) {
      if (active) {
        const newPoints = [...points, [e.latlng.lat, e.latlng.lng]]
        setPoints(newPoints)
        onPointsChange?.(newPoints)
      }
    },
  })

  useEffect(() => {
    if (!active) {
      setPoints([])
      onPointsChange?.([])
    }
  }, [active, onPointsChange])

  const totalDistance = useMemo(() => {
    let dist = 0
    for (let i = 1; i < points.length; i++) {
      const [lat1, lng1] = points[i - 1]
      const [lat2, lng2] = points[i]
      // Haversine formula
      const R = 6371
      const dLat = ((lat2 - lat1) * Math.PI) / 180
      const dLng = ((lng2 - lng1) * Math.PI) / 180
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
      dist += R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    }
    return dist
  }, [points])

  return (
    <>
      {points.length > 1 && (
        <Polyline positions={points} color="#F59E0B" weight={3} dashArray="10, 10" />
      )}
      {active && points.length > 0 && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3 text-sm">
          <p className="font-medium">Distance: {totalDistance.toFixed(2)} km</p>
          <p className="text-xs text-gray-500">Click to add points</p>
        </div>
      )}
    </>
  )
}

// ─── Layer Toggle Component ──────────────────────────────────────────────────
const LayerToggle = ({ layers, onToggle }) => (
  <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-2 space-y-1">
    {Object.entries(layers).map(([key, label]) => (
      <label key={key} className="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded cursor-pointer text-sm">
        <input
          type="checkbox"
          checked={layers[key].visible}
          onChange={() => onToggle(key)}
          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
        />
        <span>{label}</span>
      </label>
    ))}
  </div>
)

// ─── Export Map as Image ─────────────────────────────────────────────────────
const ExportMapButton = ({ mapRef }) => {
  const handleExport = useCallback(() => {
    if (!mapRef.current) return

    // In production, use html2canvas or leaflet-image plugin
    // This is a simplified version that captures the map container
    const mapContainer = mapRef.current.container
    if (mapContainer) {
      // Create a canvas and draw the map
      const canvas = document.createElement("canvas")
      canvas.width = mapContainer.offsetWidth
      canvas.height = mapContainer.offsetHeight
      const ctx = canvas.getContext("2d")
      ctx.fillStyle = "#f0f0f0"
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = "#333"
      ctx.font = "16px sans-serif"
      ctx.fillText("Map Export - Nepal Tourism", 20, 30)

      // Download
      const link = document.createElement("a")
      link.download = "nepal-tourism-map.png"
      link.href = canvas.toDataURL()
      link.click()
    }
  }, [mapRef])

  return (
    <button
      onClick={handleExport}
      className="p-2 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
      title="Export Map"
    >
      <FiDownload size={18} />
    </button>
  )
}

// ─── Main AdvancedMap Component ──────────────────────────────────────────────
const AdvancedMap = ({
  center,
  markers = [],
  userLocation,
  route = [],
  height = "500px",
  showClustering = true,
  showHeatmap = false,
  showDrawingTools = true,
  showLayerToggle = true,
  onMarkerClick,
  className = "",
}) => {
  const [mapStyle, setMapStyle] = useState("street")
  const [layers, setLayers] = useState({
    markers: { visible: true, label: "Markers" },
    heatmap: { visible: false, label: "Heatmap" },
    route: { visible: true, label: "Route" },
  })
  const [drawingMode, setDrawingMode] = useState(false)
  const [drawingPoints, setDrawingPoints] = useState([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [clusteringEnabled, setClusteringEnabled] = useState(showClustering)
  const mapRef = useRef(null)

  const activeTile = TILE_PROVIDERS[mapStyle] || TILE_PROVIDERS.street

  // Cluster markers if enabled
  const clusteredMarkers = useMemo(() => {
    if (!clusteringEnabled || markers.length < 10) return markers.map((m) => ({ ...m, count: 1 }))
    return clusterMarkers(markers, 10)
  }, [markers, clusteringEnabled])

  const handleLayerToggle = useCallback((key) => {
    setLayers((prev) => ({
      ...prev,
      [key]: { ...prev[key], visible: !prev[key].visible },
    }))
  }, [])

  const handleExport = useCallback(() => {
    // Export map as image
    const mapContainer = document.querySelector(".leaflet-container")
    if (mapContainer) {
      // Use html2canvas in production
      alert("Map export functionality - integrate with html2canvas for full implementation")
    }
  }, [])

  return (
    <div className={`relative ${className}`} style={{ height: isFullscreen ? "100vh" : height }}>
      {/* Map Controls */}
      <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2">
        {/* Map Style Selector */}
        <div className="bg-white rounded-lg shadow-lg p-1 flex gap-1">
          {Object.entries(TILE_PROVIDERS).map(([key, provider]) => (
            <button
              key={key}
              onClick={() => setMapStyle(key)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mapStyle === key
                  ? "bg-emerald-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {provider.name}
            </button>
          ))}
        </div>

        {/* Drawing Tools */}
        {showDrawingTools && (
          <button
            onClick={() => setDrawingMode(!drawingMode)}
            className={`p-2 bg-white rounded-lg shadow-lg transition-colors ${
              drawingMode ? "bg-amber-100 text-amber-700" : "hover:bg-gray-50"
            }`}
            title="Measure Distance"
          >
            <FiNavigation size={18} />
          </button>
        )}

        {/* Export */}
        <ExportMapButton mapRef={mapRef} />

        {/* Fullscreen */}
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-2 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
          title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
        >
          {isFullscreen ? <FiMinimize2 size={18} /> : <FiMaximize2 size={18} />}
        </button>
      </div>

      {/* Layer Toggle */}
      {showLayerToggle && <LayerToggle layers={layers} onToggle={handleLayerToggle} />}

      {/* Drawing Mode Indicator */}
      <AnimatePresence>
        {drawingMode && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-amber-500 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium"
          >
            Click on map to measure distance
          </motion.div>
        )}
      </AnimatePresence>

      {/* Map Container */}
      <MapContainer
        center={center || DEFAULT_MAP_CENTER}
        zoom={13}
        scrollWheelZoom={true}
        zoomControl={false}
        style={{ height: "100%", width: "100%" }}
        ref={mapRef}
      >
        <ZoomControl position="bottomright" />
        <TileLayer key={mapStyle} attribution={activeTile.attr} url={activeTile.url} />

        {/* Drawing Tool */}
        {showDrawingTools && (
          <DrawingTool active={drawingMode} onPointsChange={setDrawingPoints} />
        )}

        {/* Heatmap Layer */}
        {layers.heatmap.visible && showHeatmap && (
          <HeatmapLayer points={markers} />
        )}

        {/* Markers */}
        {layers.markers.visible && clusteredMarkers.map((marker, i) => (
          <Marker
            key={i}
            position={[marker.lat, marker.lng]}
            icon={marker.count > 1 ? L.divIcon({
              className: "cluster-marker",
              html: `<div style="width:40px;height:40px;border-radius:50%;background:#1B8A5A;color:white;display:flex;align-items:center;justify-content:center;font-weight:bold;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);">${marker.count}</div>`,
              iconSize: [40, 40],
              iconAnchor: [20, 20],
            }) : destinationIcon}
            eventHandlers={{ click: () => onMarkerClick?.(marker) }}
          >
            <Popup>
              <div className="min-w-[150px]">
                <p className="font-semibold">{marker.name || "Location"}</p>
                {marker.count > 1 && <p className="text-xs text-gray-500">{marker.count} places</p>}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* User Location */}
        {userLocation && (
          <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
            <Popup>Your Location</Popup>
          </Marker>
        )}

        {/* Route */}
        {layers.route.visible && route.length > 1 && (
          <Polyline positions={route} color="#2563eb" weight={5} opacity={0.8} />
        )}
      </MapContainer>
    </div>
  )
}

export default AdvancedMap
