import { useState, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"
import MapView from "../components/map/MapView"
import MapillaryImages from "../components/map/MapillaryImages"
import useGeolocation from "../hooks/useGeolocation"
import {
  FiNavigation, FiMapPin, FiShield,
  FiArrowLeft, FiArrowRight, FiArrowUp, FiRotateCcw, FiChevronLeft,
  FiChevronRight, FiCompass, FiTarget, FiRadio, FiLayers,
} from "react-icons/fi"
import navigationApi from "../api/navigationApi"
import emergencyApi from "../api/emergencyApi"
import nearbyApi from "../api/nearbyApi"
import destinationApi from "../api/destinationApi"
import { formatDistance, formatDuration } from "../utils/formatDistance"
import { formatCoords, hasValidCoords } from "../utils/placeUtils"

const AMENITY_TABS = [
  { id: "hospitals", label: "Hospitals / Medical" },
  { id: "police", label: "Police" },
  { id: "stores", label: "Recorded services" },
  { id: "atms", label: "Banks & ATMs" },
]

// Haversine distance (km) between two coordinates.
const haversineKm = (lat1, lng1, lat2, lng2) => {
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

// Compass bearing (16-point) from A to B.
const compassBearing = (lat1, lng1, lat2, lng2) => {
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const y = Math.sin(dLng) * Math.cos((lat2 * Math.PI) / 180)
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(dLng)
  const deg = (Math.atan2(y, x) * 180) / Math.PI
  const dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
  return dirs[Math.round(((deg + 360) % 360) / 22.5) % 16]
}

const compassArrow = (dir) => {
  const arrows = { N: "⬆", NE: "↗", E: "➔", SE: "↘", S: "⬇", SW: "↙", W: "⬅", NW: "↖" }
  for (const k of Object.keys(arrows)) if (dir.startsWith(k)) return arrows[k]
  return "➔"
}

const toAmenityCard = (row, origin) => {
  const lat = Number(row.latitude)
  const lng = Number(row.longitude)
  const km = hasValidCoords(origin?.lat, origin?.lng) && hasValidCoords(lat, lng)
    ? haversineKm(origin.lat, origin.lng, lat, lng)
    : null
  const bearing = km != null ? compassBearing(origin.lat, origin.lng, lat, lng) : ""
  return {
    id: row.id || `${row.type}-${row.name}`,
    name: row.name,
    address: row.address || row.district || "Address not recorded",
    distance: km == null ? "Distance unknown" : km < 0.1 ? "Here" : `${km.toFixed(1)} km`,
    bearing: bearing ? `${bearing} ${compassArrow(bearing)}` : "Not recorded",
    coords: hasValidCoords(lat, lng) ? { lat, lng } : null,
    phone: row.phone_number || row.phone || "",
  }
}

const TURN_ICONS = {
  start: FiArrowUp,
  straight: FiArrowUp,
  left: FiArrowLeft,
  right: FiArrowRight,
  sharp_left: FiChevronLeft,
  sharp_right: FiChevronRight,
  uturn: FiRotateCcw,
}

export default function Navigation() {
  const { position } = useGeolocation()
  const [searchParams] = useSearchParams()
  const requestedDest = searchParams.get("dest") || searchParams.get("destination") || ""

  const [destinationQuery, setDestinationQuery] = useState(requestedDest || "")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [routeType, setRouteType] = useState("fastest")
  const [distance, setDistance] = useState(null)
  const [durationMin, setDurationMin] = useState(null)
  const [steps, setSteps] = useState([])
  const [note, setNote] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [emergencyDir, setEmergencyDir] = useState(null)
  const [nearbyDests, setNearbyDests] = useState([])
  const [featuredDests, setFeaturedDests] = useState([])

  // Game HUD state
  const [gameMode, setGameMode] = useState(true)
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [satelliteView, setSatelliteView] = useState(false)
  const [amenityTab, setAmenityTab] = useState("hospitals")

  const handleGetRoute = async (targetDest = null) => {
    const destName = typeof targetDest === "string" ? targetDest : destinationQuery.trim()
    if (!destName) return

    setLoading(true)
    setError("")

    if (!position?.lat || !position?.lng) {
      setError("Enable GPS so the route can start from your recorded location.")
      setLoading(false)
      return
    }

    try {
      const payload = {
        start_latitude: position.lat,
        start_longitude: position.lng,
        destination_name: destName,
        route_type: routeType,
      }

      const response = await navigationApi.getRoute(payload)
      const dest = response.data.destination || null
      const recordedSteps = Array.isArray(response.data.steps) ? response.data.steps : []

      setDestination(dest)
      setRoute(response.data.route || [])
      setSteps(recordedSteps)
      setDurationMin(response.data.duration_min ?? null)
      setDistance(response.data.distance_km ?? null)
      setNote(response.data.note || (recordedSteps.length ? null : "Turn-by-turn steps are not recorded for this route. The map uses stored destination coordinates."))
      setCurrentStepIdx(0)
    } catch (err) {
      setRoute([])
      setSteps([])
      setDistance(null)
      setDurationMin(null)
      setDestination(null)
      setError(err.response?.data?.detail || "Route unavailable for this recorded place.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (requestedDest && position?.lat && position?.lng) handleGetRoute(requestedDest)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedDest, position?.lat, position?.lng])

  useEffect(() => {
    const recorded = (list) => (Array.isArray(list) ? list : []).filter(
      (row) => row?.name && hasValidCoords(row.latitude, row.longitude),
    )
    destinationApi.getDestinations({ featured: true, page_size: 8, limit: 8 })
      .then(({ data }) => {
        const featured = recorded(data.results || data)
        if (featured.length) {
          setFeaturedDests(featured.slice(0, 8))
          return
        }
        return destinationApi.getDestinations({ page_size: 8, limit: 8 })
          .then(({ data: fallback }) => setFeaturedDests(recorded(fallback.results || fallback).slice(0, 8)))
      })
      .catch(() => setFeaturedDests([]))
  }, [])

  useEffect(() => {
    if (!position?.lat || !position?.lng) return
    emergencyApi.nearby(position.lat, position.lng, { radius_km: 50, limit: 8 })
      .then(({ data }) => setEmergencyDir(data))
      .catch(() => setEmergencyDir(null))
    nearbyApi.getNearbyPlaces({ lat: position.lat, lng: position.lng, radius: 30000 })
      .then(({ data }) => {
        const list = data.items || data.results || data || []
        setNearbyDests(Array.isArray(list) ? list.filter((row) => row.type === "destination" || row.slug) : [])
      })
      .catch(() => setNearbyDests([]))
  }, [position])

  const amenityItems = (() => {
    if (amenityTab === "hospitals") return (emergencyDir?.hospitals || []).slice(0, 4).map((row) => toAmenityCard(row, position))
    if (amenityTab === "police") return (emergencyDir?.police || []).slice(0, 4).map((row) => toAmenityCard(row, position))
    if (amenityTab === "atms") {
      return (emergencyDir?.specialized_contacts || [])
        .filter((row) => ["atm", "bank"].includes(row.type))
        .slice(0, 4)
        .map((row) => toAmenityCard(row, position))
    }
    const services = (emergencyDir?.specialized_contacts || []).filter((row) => !["hospital", "police"].includes(row.type))
    const destCards = nearbyDests.slice(0, 4).map((row) => toAmenityCard({ ...row, type: "destination" }, position))
    return (services.length ? services.slice(0, 4).map((row) => toAmenityCard(row, position)) : destCards)
  })()

  const currentStep = steps[currentStepIdx] || steps[0] || {
    turn: "straight",
    instruction: error || (destinationQuery ? `Search a recorded destination to start a route toward ${destinationQuery}` : "Search a recorded destination to start a route"),
    distance_km: distance,
    distance_m: null,
  }

  const TurnIcon = TURN_ICONS[currentStep.turn] || FiArrowUp

  return (
    <div className="container-app theme-himalaya py-6 space-y-6 animate-fadeIn" data-testid="navigation-page">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-amber-400 text-gray-950 text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-amber-400/20">
              <FiRadio className="animate-pulse text-red-600" /> Tactical Game HUD Mode
            </span>
            <span className="text-xs text-gray-500 font-medium">GTA / Free Fire Radar Overlay</span>
          </div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight mt-1 flex items-center gap-2">
            <FiNavigation className="text-purple-700" /> Nepal Route Navigation & Tactical HUD
          </h1>
        </div>

        {/* HUD Switcher */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setGameMode(!gameMode)}
            className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
              gameMode
                ? "bg-purple-900 text-amber-300 shadow-lg shadow-purple-950/30 ring-2 ring-amber-400"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <FiTarget /> {gameMode ? "🎮 Game HUD: ON" : "🗺️ Standard Map"}
          </button>
          <button
            onClick={() => setSatelliteView(!satelliteView)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
              satelliteView ? "bg-emerald-700 text-white" : "bg-gray-100 text-gray-700"
            }`}
          >
            <FiLayers /> {satelliteView ? "🛰️ Satellite" : "🗺️ Terrain"}
          </button>
        </div>
      </div>

      {/* Recorded featured destinations */}
      <div className="space-y-1.5">
        <p className="text-[11px] font-extrabold uppercase tracking-wider text-purple-700">
          Recorded destinations
        </p>
        <div className="flex overflow-x-auto gap-2 pb-2 no-scrollbar">
          {featuredDests.map((dest) => (
            <button
              key={dest.slug || dest.id}
              onClick={() => {
                setDestinationQuery(dest.name)
                handleGetRoute(dest.name)
              }}
              className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-purple-50 border border-purple-100 text-purple-900 text-xs font-bold whitespace-nowrap shadow-sm transition-all hover:border-purple-300"
            >
              {dest.city ? `${dest.city} ➔ ${dest.name}` : dest.name}
            </button>
          ))}
          {!featuredDests.length && (
            <p className="text-xs text-slate-500">No recorded destinations with coordinates are available yet.</p>
          )}
        </div>
      </div>

      {/* Nearby recorded destinations from current GPS */}
      <div className="space-y-1.5">
        <p className="text-[11px] font-extrabold uppercase tracking-wider text-purple-700">
          Nearby recorded places from current GPS
        </p>
        <div className="flex overflow-x-auto gap-2 pb-1 no-scrollbar">
          {nearbyDests.filter((row) => row?.name).slice(0, 8).map((dest) => (
            <button
              key={dest.slug || dest.id || dest.name}
              onClick={() => {
                setDestinationQuery(dest.name)
                handleGetRoute(dest.name)
              }}
              className="px-3.5 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-950 text-xs font-bold whitespace-nowrap shadow-sm transition-all"
            >
              {dest.city ? `${dest.city} ➔ ${dest.name}` : dest.name}
            </button>
          ))}
          {!nearbyDests.length && (
            <p className="text-xs text-slate-500">
              {position?.lat ? "No recorded destinations are stored near your GPS location." : "Enable GPS to list recorded destinations near you."}
            </p>
          )}
        </div>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleGetRoute()
        }}
        className="flex flex-col sm:flex-row gap-3"
      >
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-purple-600" />
          <input
            className="input-field pl-11 text-sm font-medium"
            placeholder="Search any destination in Nepal (e.g. Pokhara, Annapurna Base Camp, Lumbini, Rara Lake)..."
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="btn-primary px-8 py-3 bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 text-white font-bold rounded-xl shadow-lg transition-all"
        >
          {loading ? "Calculating..." : "Find Route & Start HUD"}
        </button>
      </form>

      {/* Interactive Nearby Amenities Around Current Location (Hotels, Hospitals, Stores/Pharmacies, ATMs) */}
      <div className="card-base p-5 border border-purple-100 rounded-3xl space-y-4 bg-gradient-to-r from-white to-purple-50/30">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-100 pb-3">
          <div>
            <h3 className="text-sm font-black text-purple-950 flex items-center gap-2">
              <FiCompass className="text-purple-600" /> Search Around Current Location
            </h3>
            <p className="text-xs text-gray-500">
              Select an amenity category to find nearest services with distance and compass direction
            </p>
          </div>
          <div className="flex overflow-x-auto gap-1.5 no-scrollbar">
            {AMENITY_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setAmenityTab(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                  amenityTab === tab.id
                    ? "bg-purple-700 text-white shadow"
                    : "bg-white text-gray-700 hover:bg-purple-100 border border-purple-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {!position && (
          <p className="text-xs text-amber-800">Enable GPS to list recorded hospitals, police and services near you. Pharmacies are only shown when they exist in the directory.</p>
        )}
        {position && !amenityItems.length && (
          <p className="text-xs text-slate-600">No recorded facilities of this type are stored near your GPS location.</p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {amenityItems.map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <p className="font-extrabold text-xs text-gray-900 line-clamp-1">{item.name}</p>
                  <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-mono font-bold shrink-0">
                    {item.distance}
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 mt-1 line-clamp-1">{item.address}</p>
                <p className="text-[11px] font-bold text-purple-700 mt-1">Compass: {item.bearing}</p>
              </div>
              <button
                onClick={() => {
                  setDestinationQuery(item.name)
                  handleGetRoute(item.name)
                }}
                className="mt-3 w-full py-1.5 rounded-xl bg-purple-50 hover:bg-purple-600 hover:text-white text-purple-900 font-bold text-xs flex items-center justify-center gap-1.5 transition-all border border-purple-200"
              >
                <FiCompass size={12} /> Navigate Here
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* GTA / FREE FIRE GAME HUD DISPLAY */}
      {gameMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative bg-gradient-to-r from-[#0c0217] via-[#1c042e] to-[#26052b] border-2 border-purple-500/60 rounded-3xl p-5 sm:p-6 shadow-2xl text-white overflow-hidden"
        >
          <div className="absolute inset-0 bg-[radial-gradient(#a855f7_1px,transparent_1px)] [background-size:20px_20px] opacity-15 pointer-events-none"></div>

          {/* Top HUD Banner: Large Maneuver Announcement */}
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 border-b border-purple-700/50 pb-5">
            <div className="flex items-center gap-4 w-full md:w-auto">
              <div className="w-16 h-16 rounded-2xl bg-amber-400 text-gray-950 flex items-center justify-center font-black shadow-lg shadow-amber-400/30 shrink-0">
                <TurnIcon size={36} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-widest text-amber-300">
                    NEXT MANEUVER · IN {formatDistance(currentStep.distance_km)}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-white leading-tight">
                  {currentStep.instruction}
                </h2>
              </div>
            </div>

            {/* Tactical Mission Target */}
            <div className="bg-purple-950/80 border border-purple-500/40 px-4 py-2.5 rounded-2xl text-right shrink-0">
              <p className="text-[10px] text-purple-300 uppercase font-black tracking-widest">
                🎯 CURRENT OBJECTIVE
              </p>
              <p className="text-base font-extrabold text-amber-300">
                {destinationQuery}
              </p>
              <p className="text-[11px] text-purple-200">
                Remaining: <b className="text-white">{distance != null ? formatDistance(distance) : "Not recorded"}</b> · {durationMin != null ? formatDuration(durationMin) : "duration not recorded"}
              </p>
            </div>
          </div>

          {/* HUD Instrumentation Row (Speed, Compass, Altitude, Zone Status) */}
          <div className="relative z-10 grid grid-cols-2 sm:grid-cols-4 gap-4 my-5">
            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Recorded distance</p>
              <p className="text-2xl font-black text-emerald-400 mt-0.5">{distance != null ? formatDistance(distance) : "—"}</p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Destination GPS</p>
              <p className="text-sm font-black text-amber-300 mt-0.5">{formatCoords(destination?.latitude, destination?.longitude) || "Not recorded"}</p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Recorded altitude</p>
              <p className="text-2xl font-black text-cyan-300 mt-0.5">{destination?.altitude || "—"}</p>
            </div>

            <div className="bg-black/40 border border-purple-800/60 p-3 rounded-2xl text-center">
              <p className="text-[10px] text-purple-300 uppercase font-bold tracking-wider">Safety Status</p>
              <p className="text-lg font-black text-emerald-300 mt-1 flex items-center justify-center gap-1">
                <FiShield size={16} /> SAFE ZONE
              </p>
            </div>
          </div>

          {/* Turn step skipper */}
          {steps.length > 1 && (
            <div className="relative z-10 flex items-center justify-between pt-2 border-t border-purple-800/40 text-xs text-purple-200">
              <span>Step {currentStepIdx + 1} of {steps.length}</span>
              <div className="flex gap-2">
                <button
                  disabled={currentStepIdx === 0}
                  onClick={() => setCurrentStepIdx(p => Math.max(0, p - 1))}
                  className="px-3 py-1 bg-purple-900/60 hover:bg-purple-800 rounded-lg disabled:opacity-30"
                >
                  Previous Turn
                </button>
                <button
                  disabled={currentStepIdx === steps.length - 1}
                  onClick={() => setCurrentStepIdx(p => Math.min(steps.length - 1, p + 1))}
                  className="px-3 py-1 bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold rounded-lg disabled:opacity-30"
                >
                  Next Turn
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Main Map & Step-by-Step Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl overflow-hidden shadow-2xl border border-gray-200">
          <MapView
            userLocation={position}
            destination={destination}
            route={route}
            height="520px"
          />
        </div>

        <div className="space-y-4">
          <div className="card-base p-5 shadow-lg border border-purple-100 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiCompass className="text-purple-700" /> Turn-by-Turn Route
              </h3>
              <span className="text-xs px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 font-bold">
                {steps.length} Steps
              </span>
            </div>

            <ol className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
              {steps.map((step, idx) => {
                const Icon = TURN_ICONS[step.turn] || FiArrowUp
                const isCurrent = idx === currentStepIdx
                return (
                  <li
                    key={idx}
                    onClick={() => setCurrentStepIdx(idx)}
                    className={`p-3 rounded-xl cursor-pointer transition-all flex items-start gap-3 border ${
                      isCurrent
                        ? "bg-purple-50 border-purple-400 shadow-sm"
                        : "hover:bg-gray-50 border-gray-100"
                    }`}
                  >
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold shrink-0 ${
                        isCurrent
                          ? "bg-amber-400 text-gray-950 shadow"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-gray-800 leading-snug">
                        {step.instruction}
                      </p>
                      <p className="text-[11px] text-gray-400 mt-1">
                        {formatDistance(step.distance_km)} · {step.distance_m} m
                      </p>
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>

          {destination?.latitude && destination?.longitude && (
            <div className="card-base p-5 shadow-lg border border-purple-100 rounded-2xl">
              <h4 className="font-bold text-sm text-gray-800 mb-2">
                Street-Level Imagery & Views
              </h4>
              <MapillaryImages
                latitude={Number(destination.latitude)}
                longitude={Number(destination.longitude)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
