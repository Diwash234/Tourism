import { useState, useEffect, useRef, useCallback } from "react"
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker, Circle } from "react-leaflet"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiNavigation, FiMapPin, FiLayers, FiCompass, FiTarget,
  FiVolume2, FiVolumeX, FiChevronLeft, FiChevronRight,
  FiMap, FiImage, FiRoute, FiClock, FiDollarSign,
  FiActivity, FiAlertTriangle, FiHeart, FiCoffee,
  FiShoppingBag, FiCreditCard, FiPill, FiHome
} from "react-icons/fi"
import { TurnIcon } from "../../utils/uiIcons"
import navigationApi from "../../api/navigationApi"
import nearbyApi from "../../api/nearbyApi"
import destinationApi from "../../api/destinationApi"
import useGeolocation from "../../hooks/useGeolocation"
import { formatDistance, formatDuration } from "../../utils/formatDistance"

// Tile providers
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
}

// Custom marker icons
const createIcon = (emoji, color = "#2563eb", size = 32) => {
  return L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:${size * 0.5}px;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);">${emoji}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
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
      <Polyline positions={route} color="#000" weight={10} opacity={0.2} lineCap="round" lineJoin="round" />
      <Polyline positions={route} color={color} weight={6} opacity={0.9} lineCap="round" lineJoin="round" />
      <Polyline positions={route} color="#fff" weight={2} opacity={0.6} dashArray="10, 10" lineCap="round" />
    </>
  )
}

// Calculate ETA based on distance and transport mode
const calculateETA = (distanceKm, mode) => {
  const speeds = {
    "Private Car / Taxi": 35,
    "Tourist Bus": 28,
    "Motorcycle": 40,
    "Walking / Trek": 4.5,
    "Flight": 500,
  }
  const speed = speeds[mode] || 35
  const hours = distanceKm / speed
  const totalMinutes = Math.round(hours * 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return { hours: h, minutes: m, totalMinutes, display: h > 0 ? `${h}h ${m}m` : `${m} min` }
}

// Nearby place categories with icons
const PLACE_CATEGORIES = [
  { id: "hospitals", label: "Hospitals", icon: "🏥", color: "#ef4444", FiIcon: FiHeart },
  { id: "hotels", label: "Hotels", icon: "🏨", color: "#8b5cf6", FiIcon: FiHome },
  { id: "restaurants", label: "Restaurants", icon: "🍽️", color: "#f59e0b", FiIcon: FiCoffee },
  { id: "police", label: "Police", icon: "🚔", color: "#3b82f6", FiIcon: FiAlertTriangle },
  { id: "atms", label: "ATMs", icon: "🏧", color: "#10b981", FiIcon: FiCreditCard },
  { id: "pharmacies", label: "Pharmacies", icon: "💊", color: "#06b6d4", FiIcon: FiPill },
  { id: "attraction", label: "Attractions", icon: "🎯", color: "#ec4899", FiIcon: FiMapPin },
  { id: "temple", label: "Temples", icon: "🛕", color: "#f97316", FiIcon: FiMapPin },
  { id: "nature", label: "Nature", icon: "🌿", color: "#22c55e", FiIcon: FiMapPin },
  { id: "viewpoint", label: "Viewpoints", icon: "👁️", color: "#6366f1", FiIcon: FiMapPin },
]

const AdvancedNavigation = () => {
  const { position, error: geoError, locating, retry: retryGeo, watchPosition } = useGeolocation({ auto: true })
  const [originQuery, setOriginQuery] = useState("")
  const [destinationQuery, setDestinationQuery] = useState("")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [steps, setSteps] = useState([])
  const [distance, setDistance] = useState(null)
  const [durationMin, setDurationMin] = useState(null)
  const [eta, setEta] = useState(null)
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [voiceOn, setVoiceOn] = useState(false)
  const [mapStyle, setMapStyle] = useState("standard")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [nearbyPlaces, setNearbyPlaces] = useState([])
  const [nearbyLoading, setNearbyLoading] = useState(false)
  const [nearbyError, setNearbyError] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("hospitals")
  const [showNearby, setShowNearby] = useState(false)
  const [routeColor, setRouteColor] = useState("#2563eb")
  const [transportMode, setTransportMode] = useState("Private Car / Taxi")
  const [allDestinations, setAllDestinations] = useState([])
  const [destinationsWithDistance, setDestinationsWithDistance] = useState([])
  const [destinationsError, setDestinationsError] = useState("")
  const [showAllDestinations, setShowAllDestinations] = useState(false)
  const [gpsTracking, setGpsTracking] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  const watchIdRef = useRef(null)
  const nearbyRequestIdRef = useRef(0)

  // Start GPS tracking
  const startTracking = useCallback(() => {
    if (watchIdRef.current !== null) return
    const id = watchPosition((pos) => {
      setLastUpdate(new Date())
    }, () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current)
        watchIdRef.current = null
      }
      setGpsTracking(false)
    })
    if (id === null) return
    watchIdRef.current = id
    setGpsTracking(true)
  }, [watchPosition])

  // Stop GPS tracking
  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    setGpsTracking(false)
  }, [])

  useEffect(() => () => {
    if (watchIdRef.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current)
    }
  }, [])

  // Calculate route
  const handleGetRoute = async (destName = null, origName = null) => {
    const dest = destName || destinationQuery.trim()
    const orig = origName || originQuery.trim()
    if (!dest) return

    setLoading(true)
    setError("")

    try {
      const payload = {
        destination_name: dest,
        transport_mode: transportMode,
      }

      const usesCurrentLocation = !orig || /^(current location|my current location|my location|near me)$/i.test(orig)
      if (usesCurrentLocation && position) {
        payload.start_latitude = position.lat
        payload.start_longitude = position.lng
        if (position.accuracy != null) payload.gps_accuracy_m = position.accuracy
        payload.origin_name = "Current Location"
      } else if (usesCurrentLocation) {
        setError("Allow location access or enter a starting place before requesting directions.")
        return
      } else {
        payload.origin_name = orig
      }

      const response = await navigationApi.getRoute(payload)
      const data = response.data

      setDestination(data.destination)
      setRoute(data.geometry?.coordinates || data.route || [])
      setSteps(data.steps || [])
      setDistance(data.distance_km)
      setDurationMin(data.duration_min)

      // Calculate ETA
      if (data.distance_km) {
        setEta(calculateETA(data.distance_km, transportMode))
      }

      setCurrentStepIdx(0)

    } catch (err) {
      setError(err.response?.data?.detail || "Route calculation failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  // Fetch nearby places
  const fetchNearbyPlaces = useCallback(async (lat, lng, category = selectedCategory) => {
    const requestId = ++nearbyRequestIdRef.current
    setNearbyLoading(true)
    setNearbyError("")
    try {
      const { data } = await nearbyApi.getNearbyPlaces({
        lat,
        lng,
        category,
        radius_km: 50,
        limit: 50,
      })
      if (requestId === nearbyRequestIdRef.current) {
        setNearbyPlaces(data.items || data.results || data || [])
      }
    } catch (err) {
      if (requestId === nearbyRequestIdRef.current) {
        setNearbyPlaces([])
        setNearbyError(err.response?.data?.detail || "Nearby places could not be loaded. Please try again.")
      }
    } finally {
      if (requestId === nearbyRequestIdRef.current) setNearbyLoading(false)
    }
  }, [selectedCategory])

  const nearbyLat = position?.lat ?? (destination?.latitude != null ? Number(destination.latitude) : null)
  const nearbyLng = position?.lng ?? (destination?.longitude != null ? Number(destination.longitude) : null)

  useEffect(() => {
    if (!showNearby) return undefined
    const timer = setTimeout(() => {
      if (!Number.isFinite(nearbyLat) || !Number.isFinite(nearbyLng)) {
        setNearbyPlaces([])
        setNearbyLoading(false)
        setNearbyError("Allow location access to find nearby places.")
        return
      }
      fetchNearbyPlaces(nearbyLat, nearbyLng, selectedCategory)
    }, 0)
    return () => {
      clearTimeout(timer)
      nearbyRequestIdRef.current += 1
    }
  }, [showNearby, nearbyLat, nearbyLng, selectedCategory, fetchNearbyPlaces])

  // Fetch all destinations with distances
  const fetchAllDestinations = async () => {
    if (!position) return
    setLoading(true)
    setDestinationsError("")
    try {
      const { data } = await destinationApi.getMapPoints()
      const dests = Array.isArray(data) ? data : data?.points || data?.results
      if (!Array.isArray(dests)) {
        throw new Error("Destination map response did not include a points list.")
      }

      // The map-points endpoint covers the whole catalogue; do not limit
      // distance ranking to whichever 100 records happen to be first.
      const withDistances = dests.map((dest) => {
        if (dest.latitude == null || dest.longitude == null) return null
        const latitude = Number(dest.latitude)
        const longitude = Number(dest.longitude)
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
        const dist = haversineKm(position.lat, position.lng, latitude, longitude)
        if (dist === null) return null
        const eta = calculateETA(dist, transportMode)
        return { ...dest, distanceKm: dist, eta }
      }).filter(Boolean)

      // Keep the panel bounded while ranking against the complete catalogue.
      withDistances.sort((a, b) => a.distanceKm - b.distanceKm)
      setDestinationsWithDistance(withDistances.slice(0, 100))
    } catch (err) {
      console.error("Failed to fetch destinations:", err)
      setDestinationsWithDistance([])
      setDestinationsError(
        err.response?.data?.detail || "Destinations could not be loaded. Please try again."
      )
    } finally {
      setLoading(false)
    }
  }

  // Haversine distance calculation
  const haversineKm = (lat1, lng1, lat2, lng2) => {
    const R = 6371
    const dLat = ((lat2 - lat1) * Math.PI) / 180
    const dLng = ((lng2 - lng1) * Math.PI) / 180
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  }

  // Handle nearby place route
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

  // Update ETA when position changes
  useEffect(() => {
    if (!position || !destination?.latitude || !destination?.longitude) return undefined
    const dist = haversineKm(position.lat, position.lng, Number(destination.latitude), Number(destination.longitude))
    if (dist === null) return undefined
    const timer = setTimeout(() => setEta(calculateETA(dist, transportMode)), 0)
    return () => clearTimeout(timer)
  }, [position, destination, transportMode])

  const mapCenter = position
    ? { lat: position.lat, lng: position.lng }
    : destination
    ? { lat: Number(destination.latitude), lng: Number(destination.longitude) }
    : { lat: 27.7172, lng: 85.3240 }

  const currentStep = steps[currentStepIdx]

  return (
    <div className="space-y-4">
      {/* GPS Tracking Toggle */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FiActivity className="text-emerald-600" /> Real-Time GPS Tracking
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {gpsTracking ? "Tracking active — ETA updates as you move" : "Enable for live ETA updates"}
            </p>
          </div>
          <button
            onClick={gpsTracking ? stopTracking : startTracking}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-colors ${
              gpsTracking ? "bg-red-500 text-white" : "bg-emerald-600 text-white"
            }`}
          >
            <FiTarget size={14} />
            {gpsTracking ? "Stop Tracking" : "Start Tracking"}
          </button>
        </div>
        {position && (
          <div className="mt-3 p-3 rounded-xl bg-slate-50 text-xs">
            <div className="flex items-center gap-4">
              <span className="font-bold text-slate-700">
                📍 {position.lat.toFixed(4)}, {position.lng.toFixed(4)}
              </span>
              {position.accuracy && (
                <span className="text-slate-500">±{Math.round(position.accuracy)}m</span>
              )}
              {lastUpdate && (
                <span className="text-slate-400">
                  Updated: {lastUpdate.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

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

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={transportMode}
            onChange={(e) => setTransportMode(e.target.value)}
            className="px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="Private Car / Taxi">🚕 Car/Taxi</option>
            <option value="Tourist Bus">🚌 Tourist Bus</option>
            <option value="Motorcycle">🏍️ Motorcycle</option>
            <option value="Walking / Trek">🚶 Walking</option>
            <option value="Flight">✈️ Flight</option>
          </select>

          <button
            onClick={retryGeo}
            className="px-3 py-2 rounded-xl bg-emerald-50 text-emerald-700 text-xs font-bold flex items-center gap-1.5 hover:bg-emerald-100 transition-colors"
          >
            <FiTarget size={14} />
            {locating ? "Locating..." : "Use My Location"}
          </button>

          <button
            onClick={() => setShowNearby(!showNearby)}
            className={`px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors ${
              showNearby ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <FiMapPin size={14} />
            Nearby Places
          </button>

          <button
            onClick={() => {
              setShowAllDestinations(true)
              fetchAllDestinations()
            }}
            className="px-3 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-bold flex items-center gap-1.5 hover:bg-slate-200 transition-colors"
          >
            <FiMap size={14} />
            All Destinations
          </button>

          <button
            onClick={() => handleGetRoute()}
            disabled={loading || !destinationQuery.trim()}
            className="px-5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white text-sm font-bold flex items-center gap-2 transition-colors ml-auto"
          >
            <FiNavigation size={16} />
            {loading ? "Calculating..." : "Get Directions"}
          </button>
        </div>

        {geoError && <p className="text-xs text-amber-700" role="status">{geoError}</p>}

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
        <div className="lg:col-span-2 relative h-[500px] rounded-2xl overflow-hidden border border-slate-200 shadow-lg">
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

            {/* User location with accuracy circle */}
            {position && (
              <>
                <Circle
                  center={[position.lat, position.lng]}
                  radius={position.accuracy || 50}
                  pathOptions={{ color: "#10b981", fillColor: "#10b981", fillOpacity: 0.1 }}
                />
                <Marker
                  position={[position.lat, position.lng]}
                  icon={createIcon("📍", "#10b981")}
                >
                  <Popup>Your Location</Popup>
                </Marker>
              </>
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
          {distance && eta && (
            <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 backdrop-blur rounded-xl p-3 shadow-lg border border-slate-200">
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1.5">
                  <FiRoute size={14} className="text-emerald-600" />
                  <span className="font-bold text-slate-900">{distance.toFixed(1)} km</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <FiClock size={14} className="text-amber-600" />
                  <span className="font-bold text-slate-900">{eta.display}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* Turn-by-turn */}
          <div className="bg-slate-950 text-white rounded-2xl border border-slate-800 overflow-hidden">
            <div className="h-1 bg-slate-800">
              <motion.div
                className="h-full bg-gradient-to-r from-emerald-500 to-amber-400"
                initial={{ width: 0 }}
                animate={{ width: `${steps.length > 0 ? ((currentStepIdx + 1) / steps.length) * 100 : 0}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>

            <div className="p-4 space-y-4">
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

              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={() => setCurrentStepIdx(Math.max(0, currentStepIdx - 1))}
                  disabled={currentStepIdx === 0}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white text-xs font-bold flex items-center gap-1 transition-colors"
                >
                  <FiChevronLeft /> Prev
                </button>

                <button
                  onClick={() => setVoiceOn(!voiceOn)}
                  className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors ${
                    voiceOn ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {voiceOn ? <FiVolume2 /> : <FiVolumeX />}
                  {voiceOn ? "Voice On" : "Voice Off"}
                </button>

                <button
                  onClick={() => setCurrentStepIdx(Math.min(steps.length - 1, currentStepIdx + 1))}
                  disabled={currentStepIdx >= steps.length - 1}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white text-xs font-bold flex items-center gap-1 transition-colors"
                >
                  Next <FiChevronRight />
                </button>
              </div>
            </div>
          </div>

          {/* Nearby Places */}
          {showNearby && (
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <FiMapPin className="text-emerald-600" /> Nearby Places
                </h3>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {PLACE_CATEGORIES.map((cat) => (
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
                {nearbyLoading ? (
                  <div className="p-4 text-center text-xs text-slate-500">Searching nearby places...</div>
                ) : nearbyError ? (
                  <div className="p-4 text-center text-xs text-rose-700" role="status">{nearbyError}</div>
                ) : nearbyPlaces.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">No places found nearby</div>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {nearbyPlaces.slice(0, 10).map((place, idx) => (
                      <div key={idx} className="p-3 hover:bg-slate-50 transition-colors">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-900 truncate">{place.name}</p>
                            <p className="text-[10px] text-slate-500 truncate">{place.address || place.district || ""}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] font-bold text-emerald-600">
                                {Number.isFinite(Number(place.distance_km ?? place.distance))
                                  ? `${Number(place.distance_km ?? place.distance).toFixed(1)} km`
                                  : ""}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleNearbyRoute(place)}
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
          )}

          {/* All Destinations with Distance */}
          <AnimatePresence>
            {showAllDestinations && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="bg-white rounded-2xl border border-slate-200 overflow-hidden"
              >
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <FiMap className="text-emerald-600" /> All Destinations
                  </h3>
                  <button
                    onClick={() => setShowAllDestinations(false)}
                    className="text-xs text-slate-500 hover:text-slate-700"
                  >
                    Close
                  </button>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {loading ? (
                    <div className="p-4 text-center text-xs text-slate-500">Calculating distances...</div>
                  ) : destinationsError ? (
                    <div className="p-4 text-center text-xs text-red-700" role="alert">
                      {destinationsError}
                    </div>
                  ) : destinationsWithDistance.length === 0 ? (
                    <div className="p-4 text-center text-xs text-slate-500">
                      {position ? "No destinations found" : "Enable GPS to see distances"}
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {destinationsWithDistance.map((dest, idx) => (
                        <div key={dest.id} className="p-3 hover:bg-slate-50 transition-colors">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-bold text-slate-900 truncate">{dest.name}</p>
                              <p className="text-[10px] text-slate-500">{dest.district} • {dest.province}</p>
                              <div className="flex items-center gap-3 mt-1.5">
                                <span className="text-[10px] font-bold text-emerald-600 flex items-center gap-1">
                                  <FiRoute size={10} />
                                  {dest.distanceKm.toFixed(1)} km
                                </span>
                                <span className="text-[10px] font-bold text-amber-600 flex items-center gap-1">
                                  <FiClock size={10} />
                                  {dest.eta.display}
                                </span>
                              </div>
                            </div>
                            <button
                              onClick={() => {
                                setDestinationQuery(dest.name)
                                handleGetRoute(dest.name, "Current Location")
                              }}
                              className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold whitespace-nowrap flex items-center gap-1 transition-colors"
                            >
                              <FiNavigation size={10} /> Go
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Route Summary */}
          {destination && distance && eta && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Route Summary</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-xl bg-slate-50 text-center">
                  <p className="text-[10px] text-slate-500 font-bold">Distance</p>
                  <p className="text-lg font-black text-slate-900">{distance.toFixed(1)} km</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 text-center">
                  <p className="text-[10px] text-slate-500 font-bold">ETA</p>
                  <p className="text-lg font-black text-slate-900">{eta.display}</p>
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

export default AdvancedNavigation
