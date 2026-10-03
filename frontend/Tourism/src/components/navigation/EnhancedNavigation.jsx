import { useState, useEffect, useRef, useCallback } from "react"
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker } from "react-leaflet"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiNavigation, FiMapPin, FiLayers, FiCompass, FiTarget,
  FiVolume2, FiVolumeX, FiChevronLeft, FiChevronRight,
  FiMap, FiImage, FiRoute, FiClock, FiDollarSign
} from "react-icons/fi"
import { TurnIcon } from "../../utils/uiIcons"
import navigationApi from "../../api/navigationApi"
import nearbyApi from "../../api/nearbyApi"
import useGeolocation from "../../hooks/useGeolocation"
import { formatDistance, formatDuration } from "../../utils/formatDistance"

// Tile providers including satellite
const TILE_PROVIDERS = {
  standard: {
    name: "Standard",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr: "&copy; OpenStreetMap contributors",
  },
  satellite: {
    name: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr: "Tiles &copy; Esri &mdash; Source: Esri, USGS",
  },
  terrain: {
    name: "Terrain",
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr: "&copy; OpenTopoMap contributors",
  },
  hybrid: {
    name: "Hybrid",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr: "Tiles &copy; Esri",
  },
}

// Custom icons using divIcon for better styling
const createIcon = (emoji, color = "#2563eb") => {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${color};width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);">${emoji}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  })
}

const Recenter = ({ center, zoom }) => {
  const map = useMap()
  useEffect(() => {
    if (center) {
      map.flyTo([center.lat, center.lng], zoom || 15, { duration: 1.5 })
    }
  }, [center, zoom, map])
  return null
}

const RouteLayer = ({ route, color = "#2563eb" }) => {
  if (!route || route.length < 2) return null
  return (
    <>
      {/* Route shadow */}
      <Polyline
        positions={route}
        color="#000"
        weight={10}
        opacity={0.2}
        lineCap="round"
        lineJoin="round"
      />
      {/* Main route */}
      <Polyline
        positions={route}
        color={color}
        weight={6}
        opacity={0.9}
        lineCap="round"
        lineJoin="round"
      />
      {/* Route direction arrows */}
      <Polyline
        positions={route}
        color="#fff"
        weight={2}
        opacity={0.6}
        dashArray="10, 10"
        lineCap="round"
      />
    </>
  )
}

const TurnByTurnPanel = ({ steps, currentStepIdx, onStepChange, voiceOn, onToggleVoice }) => {
  const currentStep = steps[currentStepIdx]
  const progress = steps.length > 0 ? ((currentStepIdx + 1) / steps.length) * 100 : 0

  return (
    <div className="bg-slate-950 text-white rounded-2xl border border-slate-800 overflow-hidden">
      {/* Progress bar */}
      <div className="h-1 bg-slate-800">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-500 to-amber-400"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <div className="p-4 space-y-4">
        {/* Current step display */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shrink-0 shadow-lg">
            {currentStep ? <TurnIcon step={currentStep} size={32} /> : <FiNavigation size={28} />}
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
              Step {currentStepIdx + 1} of {steps.length}
            </span>
            <p className="text-sm font-bold text-white leading-tight mt-0.5">
              {currentStep?.instruction || "Enter origin and destination to start navigation"}
            </p>
            {currentStep?.distance_km != null && (
              <p className="text-xs text-slate-400 mt-0.5">
                {currentStep.distance_km < 1
                  ? `${Math.round(currentStep.distance_km * 1000)} m`
                  : `${currentStep.distance_km.toFixed(1)} km`}
              </p>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between gap-2">
          <button
            onClick={() => onStepChange(Math.max(0, currentStepIdx - 1))}
            disabled={currentStepIdx === 0}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white text-xs font-bold flex items-center gap-1 transition-colors"
          >
            <FiChevronLeft /> Prev
          </button>

          <button
            onClick={onToggleVoice}
            className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors ${
              voiceOn ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300"
            }`}
          >
            {voiceOn ? <FiVolume2 /> : <FiVolumeX />}
            {voiceOn ? "Voice On" : "Voice Off"}
          </button>

          <button
            onClick={() => onStepChange(Math.min(steps.length - 1, currentStepIdx + 1))}
            disabled={currentStepIdx >= steps.length - 1}
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white text-xs font-bold flex items-center gap-1 transition-colors"
          >
            Next <FiChevronRight />
          </button>
        </div>

        {/* Steps list */}
        {steps.length > 0 && (
          <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
            {steps.map((step, idx) => (
              <button
                key={idx}
                onClick={() => onStepChange(idx)}
                className={`w-full text-left p-2.5 rounded-lg flex items-center gap-2.5 transition-colors ${
                  idx === currentStepIdx
                    ? "bg-amber-400/20 border border-amber-400/50"
                    : idx < currentStepIdx
                    ? "bg-slate-800/50 opacity-50"
                    : "bg-slate-800 hover:bg-slate-700"
                }`}
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                  idx === currentStepIdx ? "bg-amber-400 text-slate-950" : "bg-slate-700 text-slate-300"
                }`}>
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-white truncate">{step.instruction}</p>
                  {step.distance_km != null && (
                    <p className="text-[10px] text-slate-400">
                      {step.distance_km < 1 ? `${Math.round(step.distance_km * 1000)} m` : `${step.distance_km.toFixed(1)} km`}
                    </p>
                  )}
                </div>
                <TurnIcon step={step} size={16} />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const NearbyPlacesPanel = ({ places, onGetRoute, loading }) => {
  const [selectedCategory, setSelectedCategory] = useState("hospitals")

  const categories = [
    { id: "hospitals", label: "Hospitals", icon: "🏥", color: "#ef4444" },
    { id: "hotels", label: "Hotels", icon: "🏨", color: "#8b5cf6" },
    { id: "restaurants", label: "Restaurants", icon: "🍽️", color: "#f59e0b" },
    { id: "police", label: "Police", icon: "🚔", color: "#3b82f6" },
    { id: "atms", label: "ATMs", icon: "🏧", color: "#10b981" },
    { id: "pharmacies", label: "Pharmacies", icon: "💊", color: "#06b6d4" },
  ]

  return (
    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
      <div className="p-4 border-b border-slate-100">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FiMapPin className="text-emerald-600" /> Nearby Places
        </h3>
        <div className="flex flex-wrap gap-1.5 mt-3">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex items-center gap-1 transition-colors ${
                selectedCategory === cat.id
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <span>{cat.icon}</span>
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      <div className="max-h-64 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-xs text-slate-500">Searching nearby places...</div>
        ) : places.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500">No places found nearby</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {places.slice(0, 10).map((place, idx) => (
              <div key={idx} className="p-3 hover:bg-slate-50 transition-colors">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-900 truncate">{place.name}</p>
                    <p className="text-[10px] text-slate-500 truncate">{place.address || place.district || ""}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-bold text-emerald-600">
                        {place.distance_km ? `${place.distance_km.toFixed(1)} km` : ""}
                      </span>
                      {place.bearing && (
                        <span className="text-[10px] text-slate-400">{place.bearing}</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => onGetRoute(place)}
                    className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold whitespace-nowrap flex items-center gap-1 transition-colors"
                  >
                    <FiNavigation size={10} /> Route
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const EnhancedNavigation = () => {
  const { position, error: geoError, locating, retry: retryGeo } = useGeolocation({ auto: false })
  const [originQuery, setOriginQuery] = useState("")
  const [destinationQuery, setDestinationQuery] = useState("")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [steps, setSteps] = useState([])
  const [distance, setDistance] = useState(null)
  const [durationMin, setDurationMin] = useState(null)
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [voiceOn, setVoiceOn] = useState(false)
  const [mapStyle, setMapStyle] = useState("standard")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [nearbyPlaces, setNearbyPlaces] = useState([])
  const [nearbyLoading, setNearbyLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState("hospitals")
  const [showNearby, setShowNearby] = useState(false)
  const [routeColor, setRouteColor] = useState("#2563eb")

  const mapCenter = position
    ? { lat: position.lat, lng: position.lng }
    : destination
    ? { lat: Number(destination.latitude), lng: Number(destination.longitude) }
    : { lat: 27.7172, lng: 85.3240 } // Kathmandu default

  const handleGetRoute = async (destName = null, origName = null) => {
    const dest = destName || destinationQuery.trim()
    const orig = origName || originQuery.trim()
    if (!dest) return

    setLoading(true)
    setError("")

    try {
      const payload = {
        destination_name: dest,
        transport_mode: "Private Car / Taxi",
      }

      if (orig) {
        payload.origin_name = orig
      } else if (position) {
        payload.start_latitude = position.lat
        payload.start_longitude = position.lng
        payload.origin_name = "Current Location"
      }

      const response = await navigationApi.getRoute(payload)
      const data = response.data

      setDestination(data.destination)
      setRoute(data.geometry?.coordinates || data.route || [])
      setSteps(data.steps || [])
      setDistance(data.distance_km)
      setDurationMin(data.duration_min)
      setCurrentStepIdx(0)

      // Fetch nearby places around destination
      if (data.destination?.latitude && data.destination?.longitude) {
        fetchNearbyPlaces(data.destination.latitude, data.destination.longitude)
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Route calculation failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const fetchNearbyPlaces = async (lat, lng) => {
    setNearbyLoading(true)
    try {
      const { data } = await nearbyApi.getNearbyPlaces({
        lat,
        lng,
        category: selectedCategory,
        radius_km: 25,
      })
      setNearbyPlaces(data.items || data.results || data || [])
    } catch {
      setNearbyPlaces([])
    } finally {
      setNearbyLoading(false)
    }
  }

  const handleNearbyRoute = (place) => {
    setDestinationQuery(place.name)
    handleGetRoute(place.name, originQuery || "Current Location")
  }

  // Voice guidance
  useEffect(() => {
    if (!("speechSynthesis" in window)) return undefined
    if (!voiceOn || steps.length === 0) {
      window.speechSynthesis.cancel()
      return undefined
    }
    const step = steps[currentStepIdx]
    if (!step) return undefined

    const utterance = new SpeechSynthesisUtterance(
      `Step ${currentStepIdx + 1} of ${steps.length}. ${step.instruction}` +
        (step.distance_km != null ? `, ${step.distance_km < 1 ? `${Math.round(step.distance_km * 1000)} meters` : `${step.distance_km.toFixed(1)} kilometres`}` : "")
    )
    utterance.rate = 0.95
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)

    return () => window.speechSynthesis.cancel()
  }, [voiceOn, currentStepIdx, steps])

  const currentStep = steps[currentStepIdx]

  return (
    <div className="space-y-4">
      {/* Search Form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <div className="relative">
            <FiCompass className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-600" size={16} />
            <input
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="From: Current Location, Kathmandu..."
              value={originQuery}
              onChange={(e) => setOriginQuery(e.target.value)}
            />
          </div>
          <div className="relative">
            <FiMapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-rose-600" size={16} />
            <input
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="To: Destination (e.g. Pokhara, Fishtail...)"
              value={destinationQuery}
              onChange={(e) => setDestinationQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={retryGeo}
              className="px-3 py-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-bold flex items-center gap-1.5 hover:bg-emerald-100 transition-colors"
            >
              <FiTarget size={14} />
              {locating ? "Locating..." : "Use My Location"}
            </button>
            <button
              onClick={() => setShowNearby(!showNearby)}
              className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors ${
                showNearby ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              <FiMapPin size={14} />
              Nearby Places
            </button>
          </div>

          <button
            onClick={() => handleGetRoute()}
            disabled={loading || !destinationQuery.trim()}
            className="px-5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-sm font-bold flex items-center gap-2 transition-colors"
          >
            <FiNavigation size={16} />
            {loading ? "Calculating..." : "Get Directions"}
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-medium">
            {error}
          </div>
        )}
      </div>

      {/* Map Style Selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {Object.entries(TILE_PROVIDERS).map(([key, provider]) => (
          <button
            key={key}
            onClick={() => setMapStyle(key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap flex items-center gap-1.5 transition-colors ${
              mapStyle === key
                ? "bg-slate-900 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            {key === "satellite" && <FiLayers size={12} />}
            {key === "standard" && <FiMap size={12} />}
            {key === "terrain" && <FiCompass size={12} />}
            {provider.name}
          </button>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-4">
        {/* Map */}
        <div className="lg:col-span-2 relative h-[400px] rounded-2xl overflow-hidden border border-slate-200 shadow-lg">
          <MapContainer
            center={[mapCenter.lat, mapCenter.lng]}
            zoom={13}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
          >
            <Recenter center={mapCenter} zoom={route.length > 0 ? 12 : 13} />
            <TileLayer
              attribution={TILE_PROVIDERS[mapStyle].attr}
              url={TILE_PROVIDERS[mapStyle].url}
            />

            {/* User location */}
            {position && (
              <Marker
                position={[position.lat, position.lng]}
                icon={createIcon("📍", "#10b981")}
              >
                <Popup>Your Location</Popup>
              </Marker>
            )}

            {/* Destination */}
            {destination?.latitude && (
              <Marker
                position={[Number(destination.latitude), Number(destination.longitude)]}
                icon={createIcon("🎯", "#ef4444")}
              >
                <Popup>
                  <div className="p-1">
                    <p className="font-bold text-sm">{destination.name}</p>
                    {destination.short_description && (
                      <p className="text-xs text-slate-500 mt-1">{destination.short_description}</p>
                    )}
                  </div>
                </Popup>
              </Marker>
            )}

            {/* Route */}
            <RouteLayer route={route} color={routeColor} />

            {/* Nearby places markers */}
            {showNearby && nearbyPlaces.map((place, idx) => (
              <Marker
                key={idx}
                position={[Number(place.latitude), Number(place.longitude)]}
                icon={createIcon("📍", "#8b5cf6")}
              >
                <Popup>
                  <div className="p-1">
                    <p className="font-bold text-xs">{place.name}</p>
                    <p className="text-[10px] text-slate-500">{place.distance_km?.toFixed(1)} km away</p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Map overlay info */}
          {distance && (
            <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 backdrop-blur rounded-xl p-3 shadow-lg border border-slate-200">
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <FiRoute size={14} className="text-emerald-600" />
                  <span className="font-bold text-slate-900">{distance} km</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <FiClock size={14} className="text-amber-600" />
                  <span className="font-bold text-slate-900">{durationMin} min</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Turn-by-turn */}
          <TurnByTurnPanel
            steps={steps}
            currentStepIdx={currentStepIdx}
            onStepChange={setCurrentStepIdx}
            voiceOn={voiceOn}
            onToggleVoice={() => setVoiceOn(!voiceOn)}
          />

          {/* Nearby Places */}
          {showNearby && (
            <NearbyPlacesPanel
              places={nearbyPlaces}
              onGetRoute={handleNearbyRoute}
              loading={nearbyLoading}
            />
          )}

          {/* Quick Stats */}
          {destination && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Route Summary</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-xl bg-slate-50 text-center">
                  <p className="text-[10px] text-slate-500 font-bold">Distance</p>
                  <p className="text-lg font-black text-slate-900">{distance || "—"} km</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 text-center">
                  <p className="text-[10px] text-slate-500 font-bold">Duration</p>
                  <p className="text-lg font-black text-slate-900">{durationMin || "—"} min</p>
                </div>
              </div>
              {destination.name && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                  <p className="text-xs font-bold text-emerald-900">{destination.name}</p>
                  {destination.short_description && (
                    <p className="text-[10px] text-emerald-700 mt-0.5 line-clamp-2">{destination.short_description}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default EnhancedNavigation
