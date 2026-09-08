import { useState, useEffect } from "react"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { useSearchParams, Link } from "react-router-dom"
import { motion } from "framer-motion"
import MapView from "../components/map/MapView"
import MapillaryImages from "../components/map/MapillaryImages"
import useGeolocation from "../hooks/useGeolocation"
import {
  FiNavigation, FiMapPin, FiShield,
  FiArrowLeft, FiArrowRight, FiArrowUp, FiRotateCcw, FiChevronLeft,
  FiChevronRight, FiCompass, FiTarget, FiRadio, FiLayers, FiRepeat,
  FiCheckCircle, FiAlertTriangle, FiPhoneCall, FiSun, FiZap, FiTruck, FiCoffee
} from "react-icons/fi"
import navigationApi from "../api/navigationApi"
import emergencyApi from "../api/emergencyApi"
import useAuth from "../hooks/useAuth"
import { savedRoutesApi } from "../services/api"
import nearbyApi from "../api/nearbyApi"
import destinationApi from "../api/destinationApi"
import axiosClient from "../api/axiosClient"
import { formatDistance, formatDuration } from "../utils/formatDistance"
import { formatCoords, hasValidCoords } from "../utils/placeUtils"

const AMENITY_TABS = [
  { id: "hospitals", label: "🏥 Hospitals", icon: "🏥" },
  { id: "police", label: "🚓 Police", icon: "🚓" },
  { id: "atms", label: "🏦 Banks & ATMs", icon: "🏦" },
  { id: "pharmacies", label: "💊 Pharmacies", icon: "💊" },
  { id: "stores", label: "🛒 Stores & Marts", icon: "🛒" },
  { id: "restaurants", label: "🍽 Restaurants", icon: "🍽️" },
  { id: "hotels", label: "🏨 Hotels", icon: "🏨" },
]

const TRANSPORT_MODES = [
  { id: "Private Car / Taxi", label: "🚗 Private Car / Taxi", avgSpeed: 40 },
  { id: "Tourist Bus", label: "🚌 Tourist Bus", avgSpeed: 30 },
  { id: "Motorcycle", label: "🏍️ Motorcycle", avgSpeed: 45 },
  { id: "Flight", label: "✈️ Mountain Flight", avgSpeed: 250 },
  { id: "Walking / Trek", label: "🚶 Walking / Trek", avgSpeed: 5 },
]

const haversineKm = (lat1, lng1, lat2, lng2) => {
  if (!hasValidCoords(lat1, lng1) || !hasValidCoords(lat2, lng2)) return null
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

const DISTRICT_ALTITUDES = {
  kathmandu: "1,400 m",
  lalitpur: "1,400 m",
  bhaktapur: "1,400 m",
  kaski: "822 m",
  pokhara: "822 m",
  solukhumbu: "3,440 m",
  mustang: "3,840 m",
  manang: "3,519 m",
  chitwan: "415 m",
  bardiya: "152 m",
  lumbini: "150 m",
  ilam: "1,200 m",
  tanahun: "1,030 m",
  myagdi: "2,060 m",
  gorkha: "1,060 m",
  rasuwa: "2,030 m",
  sindhupalchok: "1,450 m",
  dolakha: "1,660 m",
  darchula: "1,800 m",
  dolpa: "2,280 m",
  mugu: "2,990 m",
  sankhuwasabha: "1,500 m",
  taplejung: "1,820 m",
}

const getDistrictAltitude = (dest) => {
  if (dest?.altitude) return dest.altitude
  const key = (dest?.district || dest?.city || dest?.name || "").toLowerCase()
  for (const [k, v] of Object.entries(DISTRICT_ALTITUDES)) {
    if (key.includes(k)) return `${v} (district typical)`
  }
  return "Information unavailable"
}

const compassBearing = (lat1, lng1, lat2, lng2) => {
  if (!hasValidCoords(lat1, lng1) || !hasValidCoords(lat2, lng2)) return ""
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
    category: row.category || row.type || "Service",
    address: row.address || row.district || "Address recorded",
    distance: km == null ? "Information unavailable" : km < 0.1 ? "0 km (Here)" : `≈ ${km.toFixed(1)} km (straight line)`,
    bearing: bearing ? `${bearing} ${compassArrow(bearing)}` : "",
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
  const { position, error: geoError, locating, retry: retryGeo } = useGeolocation()
  const [searchParams] = useSearchParams()
  const requestedDest = searchParams.get("dest") || searchParams.get("destination") || ""
  const requestedOrigin = searchParams.get("origin") || ""

  const [originQuery, setOriginQuery] = useState(requestedOrigin || "")
  const [destinationQuery, setDestinationQuery] = useState(requestedDest || "")
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState([])
  const [transportMode, setTransportMode] = useState("Private Car / Taxi")
  const [distance, setDistance] = useState(null)
  const [durationMin, setDurationMin] = useState(null)
  const [durationNote, setDurationNote] = useState("")
  const [durationSource, setDurationSource] = useState("")
  const [steps, setSteps] = useState([])
  const [routeAlerts, setRouteAlerts] = useState([])
  const [alertsLoaded, setAlertsLoaded] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [emergencyDir, setEmergencyDir] = useState(null)
  const [nearbyDests, setNearbyDests] = useState([])
  const [featuredDests, setFeaturedDests] = useState([])
  const [nearbyPlaces, setNearbyPlaces] = useState([])
  const [nearbyLoading, setNearbyLoading] = useState(false)

  // HUD & Tools Drawer State
  // Standard turn-by-turn map is the default experience; the Game HUD is opt-in (brief item).
  const [gameMode, setGameMode] = useState(false)
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [satelliteView, setSatelliteView] = useState(false)
  const [showToolsDrawer, setShowToolsDrawer] = useState(false)
  const [amenityTab, setAmenityTab] = useState("hospitals")

  // "My Current Location" is a symbolic origin: it resolves to the browser
  // GPS fix at request time and is never silently replaced by a fixed city.
  const usingMyLocation = originQuery.trim().toLowerCase() === "my current location"

  const handleUseMyLocation = () => {
    if (position) {
      setOriginQuery("My Current Location")
      return
    }
    retryGeo()
    setOriginQuery("My Current Location")
  }

  const handleGetRoute = async (targetDest = null, targetOrigin = null) => {
    const destName = typeof targetDest === "string" ? targetDest : destinationQuery.trim()
    const origName = typeof targetOrigin === "string" ? targetOrigin : originQuery.trim()
    if (!destName) return

    // Honest origin: GPS fix, a named place the backend can resolve, or an
    // explicit error — never a fabricated default city.
    const useGpsOrigin = !origName || usingMyLocation
    if (useGpsOrigin && !position) {
      setError(
        geoError
          ? `Location unavailable (${geoError}). Type a starting place — e.g. Kathmandu — or enable GPS and press "Use My Location".`
          : 'Press "Use My Location" to share your GPS position, or type a starting place — e.g. Kathmandu.'
      )
      return
    }

    setLoading(true)
    setError("")

    try {
      const payload = {
        destination_name: destName,
        transport_mode: transportMode,
      }
      if (useGpsOrigin) {
        payload.start_latitude = position.lat
        payload.start_longitude = position.lng
        payload.origin_name = "Current Location"
      } else {
        payload.origin_name = origName
      }

      const response = await navigationApi.getRoute(payload)
      const dest = response.data.destination || null
      const recordedSteps = Array.isArray(response.data.steps) ? response.data.steps : []

      setDestination(dest)
      setRoute(response.data.route || [])
      setSteps(recordedSteps)
      setDurationMin(response.data.duration_min ?? null)
      setDurationNote(response.data.duration_note || "")
      setDurationSource(response.data.duration_source || "")
      setDistance(response.data.distance_km ?? null)
      setCurrentStepIdx(0)

      // Navigation history (spec item 16): silently log each successful
      // calculation for signed-in travellers. Failures never disturb the map.
      if (isAuthenticated) {
        savedRoutesApi.create({
          origin_name: response.data.origin?.name || (usingMyLocation ? "Current Location" : origName),
          origin_latitude: response.data.origin?.latitude ?? (useGpsOrigin ? position.lat : null),
          origin_longitude: response.data.origin?.longitude ?? (useGpsOrigin ? position.lng : null),
          destination_name: dest?.name || destName,
          destination_latitude: dest?.latitude ?? null,
          destination_longitude: dest?.longitude ?? null,
          transport_mode: transportMode,
          distance_km: response.data.distance_km ?? null,
          duration_min: response.data.duration_min ?? null,
          duration_source: response.data.duration_source || "",
        }).catch(() => {})
      }

      // Real safety data only: active verified alerts near the destination
      // corridor. No fabricated "road open / rain possible" claims — when
      // the alert feed has nothing, the UI says exactly that.
      if (dest?.latitude != null && dest?.longitude != null) {
        axiosClient
          .get("/alerts/nearby/", {
            params: { latitude: dest.latitude, longitude: dest.longitude, radius_km: 25 },
          })
          .then(({ data }) => {
            const list = data.results || data || []
            setRouteAlerts(Array.isArray(list) ? list.slice(0, 6) : [])
            setAlertsLoaded(true)
          })
          .catch(() => {
            setRouteAlerts([])
            setAlertsLoaded(true)
          })
      } else {
        setRouteAlerts([])
        setAlertsLoaded(true)
      }
    } catch (err) {
      setRoute([])
      setSteps([])
      setDistance(null)
      setDurationMin(null)
      setDurationNote("")
      setDurationSource("")
      setDestination(null)
      setError(err.response?.data?.detail || "Routing information unavailable for this pair of places. Check the place names and try again.")
    } finally {
      setLoading(false)
    }
  }

  const [shareCopied, setShareCopied] = useState(false)
  const { isAuthenticated } = useAuth() || {}
  const [routesOpen, setRoutesOpen] = useState(false)
  const [routesTab, setRoutesTab] = useState("history")
  const [myRoutes, setMyRoutes] = useState([])
  const loadMyRoutes = (tab) => {
    savedRoutesApi
      .list(tab === "saved")
      .then((res) => setMyRoutes(Array.isArray(res.data) ? res.data : res.data?.results || []))
      .catch(() => setMyRoutes([]))
  }

  const toggleRoutesPanel = () => {
    const next = !routesOpen
    setRoutesOpen(next)
    if (next) loadMyRoutes(routesTab)
  }

  const handleSaveCurrentRoute = () => {
    if (!destination) return
    savedRoutesApi
      .create({
        origin_name: originQuery.trim() || "Current Location",
        origin_latitude: position?.lat ?? null,
        origin_longitude: position?.lng ?? null,
        destination_name: destination.name || destinationQuery.trim(),
        destination_latitude: destination.latitude ?? null,
        destination_longitude: destination.longitude ?? null,
        transport_mode: transportMode,
        distance_km: distance,
        duration_min: durationMin,
        duration_source: durationSource,
        is_saved: true,
        label: `${originQuery.trim() || "Current Location"} \u2192 ${destination.name || destinationQuery.trim()}`,
      })
      .then(() => { if (routesOpen) loadMyRoutes(routesTab) })
      .catch(() => {})
  }

  const handleShareRoute = async () => {
    const dest = destinationQuery.trim()
    if (!dest) return
    const params = new URLSearchParams({ dest })
    const orig = originQuery.trim()
    if (orig) params.set("origin", orig)
    const url = `${window.location.origin}/navigation?${params.toString()}`
    try {
      await navigator.clipboard.writeText(url)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 2000)
    } catch {
      window.prompt("Copy this route link:", url)
    }
  }

  const handleSwapLocations = () => {
    const orig = originQuery
    const dest = destinationQuery
    setOriginQuery(dest)
    setDestinationQuery(orig)
    if (dest) handleGetRoute(orig, dest)
  }

  useEffect(() => {
    if (requestedDest) {
      const z = setTimeout(() => handleGetRoute(requestedDest, requestedOrigin), 0)
      return () => clearTimeout(z)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedDest, requestedOrigin])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    destinationApi.getDestinations({ featured: true, page_size: 8, limit: 8 })
      .then(({ data }) => {
        const list = data.results || data || []
        setFeaturedDests(list.slice(0, 8))
      })
      .catch(() => setFeaturedDests([]))
    }, 0)
    return () => clearTimeout(t)
  }, [])

  // Nearby searches need a real centre: the GPS fix, or the routed
  // destination. Never a silent default city.
  const nearbyCenter = position
    ? { lat: position.lat, lng: position.lng, label: "your GPS position" }
    : destination?.latitude != null && destination?.longitude != null
      ? { lat: Number(destination.latitude), lng: Number(destination.longitude), label: `around ${destination.name || "the destination"}` }
      : null

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    if (!nearbyCenter) {
      setNearbyPlaces([])
      setEmergencyDir(null)
      setNearbyLoading(false)
      return
    }
    setNearbyLoading(true)
    emergencyApi.nearby(nearbyCenter.lat, nearbyCenter.lng, { radius_km: 50, limit: 8 })
      .then(({ data }) => setEmergencyDir(data))
      .catch(() => setEmergencyDir(null))

    nearbyApi.getNearbyPlaces({ lat: nearbyCenter.lat, lng: nearbyCenter.lng, category: amenityTab, radius_km: 25 })
      .then(({ data }) => {
        const list = data.items || data.results || data || []
        setNearbyPlaces(Array.isArray(list) ? list : [])
      })
      .catch(() => setNearbyPlaces([]))
      .finally(() => setNearbyLoading(false))
    }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [position, amenityTab, destination?.id])

  const currentStep = steps[currentStepIdx] || steps[0] || {
    turn: "straight",
    instruction: destinationQuery ? `Highway route toward ${destinationQuery}` : "Enter an origin and destination to start turn-by-turn navigation",
    distance_km: distance,
  }

  const TurnIcon = TURN_ICONS[currentStep.turn] || FiArrowUp

  return (
    <div className="container-app theme-himalaya py-6 space-y-6 animate-fadeIn" data-testid="navigation-page">
      <CMSPageIntro pageKey="navigation" />
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-amber-400 text-gray-950 text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-amber-400/20">
              <FiRadio className="animate-pulse text-red-600" /> Live Nepal Navigation Engine
            </span>
            <span className="text-xs text-gray-500 font-medium">Any Origin ➔ Any Destination in 7 Provinces</span>
          </div>
          <PageHeader title="Maps & Navigation" icon={FiNavigation} />
        </div>

        {/* HUD & Map Tools Switcher */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setGameMode(!gameMode)}
            className={`px-4 py-2 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all ${
              gameMode
                ? "bg-[#102A2E] text-emerald-300 shadow-lg shadow-emerald-950/30 ring-2 ring-emerald-500"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <FiTarget /> {gameMode ? "🎮 Game HUD: ON" : "🗺️ Standard Map"}
          </button>
          <button
            onClick={() => setShowToolsDrawer(!showToolsDrawer)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
              showToolsDrawer ? "bg-amber-400 text-slate-950 font-black" : "bg-gray-100 text-gray-700"
            }`}
          >
            <FiCompass /> 🛠️ Map Tools
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

      {/* Map Tools Drawer */}
      {showToolsDrawer && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="p-4 rounded-2xl bg-slate-900 text-white space-y-3 border border-slate-800">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <span className="font-extrabold text-xs text-amber-300">🛠️ Advanced Map Tools & Overlay Layers</span>
            <button onClick={() => setShowToolsDrawer(false)} className="text-xs text-slate-400 hover:text-white">Close Tools ✕</button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <button onClick={() => setSatelliteView(false)} className={`p-2.5 rounded-xl border text-left ${!satelliteView ? 'bg-[#102A2E] border-[#1D5146] text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'}`}>🗺️ Topographic Contour</button>
            <button onClick={() => setSatelliteView(true)} className={`p-2.5 rounded-xl border text-left ${satelliteView ? 'bg-emerald-800 border-emerald-500 text-white font-bold' : 'bg-slate-800 border-slate-700 text-slate-300'}`}>🛰️ Satellite Imagery</button>
            <button onClick={() => setGameMode(true)} className={`p-2.5 rounded-xl border text-left ${gameMode ? 'bg-amber-400 text-slate-950 font-black' : 'bg-slate-800 border-slate-700 text-slate-300'}`}>🎯 Compass Radar HUD</button>
            <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300">
              <span className="block font-bold text-amber-300">Altitude Matrix</span>
              <span className="text-[10px] text-slate-400">{getDistrictAltitude(destination)}</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* ROUTE SEARCH FORM: ORIGIN -> DESTINATION */}
      <div className="card-base p-5 border border-[#E5E0D5] rounded-3xl space-y-4 bg-white shadow-md">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleGetRoute()
          }}
          className="space-y-3"
        >
          <div className="grid sm:grid-cols-2 gap-3 items-center">
            <div className="relative flex gap-2">
              <div className="relative flex-1">
                <FiCompass className="absolute left-4 top-1/2 -translate-y-1/2 text-emerald-600" />
                <input
                  className="input-field pl-11 text-xs font-medium"
                  placeholder="From: My Current Location, Kathmandu, Pokhara, Rara..."
                  value={originQuery}
                  onChange={(e) => setOriginQuery(e.target.value)}
                />
              </div>
              <button
                type="button"
                onClick={handleUseMyLocation}
                className="px-3 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold whitespace-nowrap flex items-center gap-1.5"
                title={position ? "GPS fix acquired — click to use it as the origin" : locating ? "Requesting GPS permission…" : "Request browser GPS and use it as the origin"}
              >
                <FiTarget size={13} /> {locating && !position ? "Locating…" : "📍 Use My Location"}
              </button>
            </div>

            <div className="relative">
              <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-rose-600" />
              <input
                className="input-field pl-11 text-xs font-medium"
                placeholder="Destination Place (e.g. Koshi, Lumbini, Chitwan, Phewa Lake, Thamel)..."
                value={destinationQuery}
                onChange={(e) => setDestinationQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="text-[11px] text-slate-500" role="status">
            {position ? (
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                <span>📍 GPS fix acquired ({position.lat.toFixed(4)}, {position.lng.toFixed(4)})</span>
                {position.accuracy != null && <span>Accuracy ±{Math.round(position.accuracy)} m</span>}
                {position.altitude != null && <span>Altitude {Math.round(position.altitude)} m</span>}
                {position.speed != null && <span>Speed {Math.round(position.speed * 3.6)} km/h</span>}
              </div>
            ) : locating ? (
              <p>Requesting your GPS position…</p>
            ) : geoError ? (
              <p>GPS unavailable: {geoError}. Type a starting place instead — e.g. Kathmandu.</p>
            ) : (
              <p>No GPS position yet. Press “Use My Location” or type a starting place.</p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleSwapLocations}
                className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold flex items-center gap-1"
                title="Swap Origin and Destination"
              >
                <FiRepeat /> ⇄ Swap
              </button>

              <select
                className="input-field py-1.5 px-3 text-xs w-auto border-slate-200 font-bold"
                value={transportMode}
                onChange={(e) => setTransportMode(e.target.value)}
              >
                {TRANSPORT_MODES.map((mode) => (
                  <option key={mode.id} value={mode.id}>{mode.label}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              {isAuthenticated && destination && (
                <button
                  type="button"
                  onClick={handleSaveCurrentRoute}
                  title="Keep this route in your Saved Routes"
                  className="px-3.5 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold text-xs whitespace-nowrap border border-amber-300"
                >
                  ⭐ Save
                </button>
              )}
              <button
                type="button"
                onClick={handleShareRoute}
                disabled={!destinationQuery.trim()}
                className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs whitespace-nowrap disabled:opacity-40"
                title="Copy a link that opens this exact route"
              >
                {shareCopied ? "✓ Copied" : "🔗 Copy route link"}
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-black text-xs shadow-lg transition-all whitespace-nowrap"
              >
                {loading ? "Calculating..." : "Find Route & Calculate Distance"}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* MY ROUTES — saved routes + navigation history (spec items 15/16) */}
      {isAuthenticated && (
        <div className="p-4 rounded-3xl bg-white border border-[#E5E0D5] shadow-md space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <button
              type="button"
              onClick={toggleRoutesPanel}
              aria-expanded={routesOpen}
              className="text-xs font-black uppercase text-slate-700 flex items-center gap-1.5 hover:text-emerald-700"
            >
              🕘 My routes {routesOpen ? "▲" : "▼"}
            </button>
            {routesOpen && (
              <div className="flex gap-1.5" role="tablist" aria-label="Route lists">
                {["history", "saved"].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    role="tab"
                    aria-selected={routesTab === tab}
                    onClick={() => { setRoutesTab(tab); loadMyRoutes(tab) }}
                    className={`px-3 py-1 rounded-full text-[11px] font-bold transition ${routesTab === tab ? "bg-emerald-700 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
                  >
                    {tab === "history" ? "History" : "⭐ Saved"}
                  </button>
                ))}
              </div>
            )}
          </div>
          {routesOpen && (
            myRoutes.length === 0 ? (
              <p className="text-xs text-slate-500">
                {routesTab === "history"
                  ? "Routes you calculate while signed in appear here."
                  : "Press “⭐ Save” on a calculated route to keep it here."}
              </p>
            ) : (
              <ul className="max-h-56 space-y-1.5 overflow-y-auto pr-1">
                {myRoutes.map((r) => (
                  <li key={r.id} className="flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
                    <button
                      type="button"
                      className="min-w-0 flex-1 text-left"
                      title="Open this route"
                      onClick={() => {
                        const namedOrigin = r.origin_name && r.origin_name !== "Current Location" ? r.origin_name : null
                        if (namedOrigin) setOriginQuery(namedOrigin)
                        setDestinationQuery(r.destination_name)
                        const modeMatch = TRANSPORT_MODES.find((m) => m.id === r.transport_mode)
                        if (modeMatch) setTransportMode(modeMatch.id)
                        setRoutesOpen(false)
                        handleGetRoute(r.destination_name, namedOrigin)
                      }}
                    >
                      <span className="block truncate font-bold text-slate-800">
                        {r.label || `${r.origin_name || "Current Location"} → ${r.destination_name}`}
                      </span>
                      <span className="block text-[10px] text-slate-500">
                        {r.transport_mode}
                        {r.distance_km != null ? ` · ${Number(r.distance_km).toFixed(1)} km` : ""}
                        {r.duration_min != null ? ` · ${Math.floor(r.duration_min / 60)}h ${r.duration_min % 60}m` : ""}
                        {r.duration_source ? ` · ${r.duration_source}` : ""}
                        {" · "}{new Date(r.created_at).toLocaleDateString()}
                      </span>
                    </button>
                    <button
                      type="button"
                      aria-label={r.is_saved ? "Remove from saved" : "Save this route"}
                      onClick={() => savedRoutesApi.update(r.id, { is_saved: !r.is_saved }).then(() => loadMyRoutes(routesTab)).catch(() => {})}
                      className="text-sm"
                    >
                      {r.is_saved ? "⭐" : "☆"}
                    </button>
                    <button
                      type="button"
                      aria-label="Delete route"
                      onClick={() => savedRoutesApi.remove(r.id).then(() => loadMyRoutes(routesTab)).catch(() => {})}
                      className="text-sm text-slate-400 hover:text-red-500"
                    >
                      🗑
                    </button>
                  </li>
                ))}
              </ul>
            )
          )}
        </div>
      )}

      {/* ROUTE SAFETY — real verified alerts only, never invented statuses */}
      {alertsLoaded && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 rounded-3xl bg-slate-950 text-white border border-slate-800 space-y-3 shadow-xl">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
            <span className="text-xs font-black uppercase text-amber-300 flex items-center gap-1.5">
              <FiShield className="text-amber-400" /> Route Safety Alerts
            </span>
            <span className="text-[10px] text-slate-400 font-extrabold">
              {routeAlerts.length ? `${routeAlerts.length} active alert${routeAlerts.length > 1 ? "s" : ""} near destination` : "No active alerts recorded"}
            </span>
          </div>

          {routeAlerts.length === 0 ? (
            <p className="text-xs text-slate-300 py-1">
              No verified weather, landslide, flood, or transport alerts are currently recorded within 25 km of this
              destination. Alerts appear here only when an administrator has published them from a real source.
            </p>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
              {routeAlerts.map((alert) => (
                <div key={alert.id} className="p-3 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">
                    {alert.alert_type} · {alert.severity}
                  </span>
                  <p className="font-extrabold text-amber-200">{alert.title}</p>
                  <p className="text-[10px] text-slate-300 line-clamp-2">{alert.description}</p>
                  <p className="text-[10px] text-slate-500">
                    Source: {alert.source || "Information unavailable"}
                    {alert.is_verified ? " · ✓ Verified" : " · Unverified"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* NEARBY SERVICES & AMENITIES RADAR */}
      <div className="card-base p-5 border border-[#E5E0D5] rounded-3xl space-y-4 bg-gradient-to-r from-white to-purple-50/30">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E5E0D5] pb-3">
          <div>
            <h3 className="text-sm font-black text-purple-950 flex items-center gap-2">
              <FiCompass className="text-emerald-700" /> Search Around Current GPS / Destination
            </h3>
            <p className="text-xs text-gray-500">
              Select a service category to discover nearest facilities with Haversine distance and compass heading
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1.5">
            {AMENITY_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setAmenityTab(tab.id)}
                className={`px-2.5 py-1.5 rounded-xl text-[11px] font-bold text-center transition-all ${
                  amenityTab === tab.id
                    ? "bg-[#102A2E] text-white shadow"
                    : "bg-white text-gray-700 hover:bg-emerald-100 border border-[#E5E0D5]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {nearbyPlaces.slice(0, 8).map((place) => {
            const card = toAmenityCard(place, nearbyCenter)
            return (
              <div key={card.id} className="p-3 rounded-2xl bg-white border border-[#E5E0D5] shadow-sm space-y-2 flex flex-col justify-between hover:shadow-md transition">
                <div>
                  <span className="px-2 py-0.5 rounded bg-[#F7F8F5] text-[#1D5146] text-[10px] font-black uppercase block w-fit">
                    {card.category}
                  </span>
                  <h4 className="font-bold text-slate-900 text-xs mt-1 truncate">{card.name}</h4>
                  <p className="text-[10px] text-slate-500 truncate">{card.address}</p>
                </div>
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="font-black text-emerald-700">{card.distance}</span>
                  <span className="font-extrabold text-amber-700 text-[11px]">{card.bearing}</span>
                </div>
              </div>
            )
          })}
          {!nearbyPlaces.length && (
            <p className="sm:col-span-4 text-center py-4 text-xs text-slate-500">
              {nearbyLoading
                ? `Searching for ${amenityTab} ${nearbyCenter ? nearbyCenter.label : ""}…`
                : nearbyCenter
                  ? `No ${amenityTab} with recorded coordinates were found within 25 km of ${nearbyCenter.label}. Try a larger category or another location.`
                  : 'Share your location ("Use My Location") or calculate a route first — nearby services are searched around a real position, never an assumed city.'}
            </p>
          )}
        </div>
      </div>

      {/* MAP & TURN-BY-TURN HUD DISPLAY */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card-base overflow-hidden rounded-3xl border border-[#E5E0D5] h-[500px] relative shadow-2xl">
          <MapView
            destination={destination}
            routeWaypoints={route}
            satellite={satelliteView}
          />
        </div>

        {/* HUD NAVIGATOR PANEL */}
        <div className="card-base p-5 bg-slate-950 text-white rounded-3xl border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex justify-between items-center border-b border-slate-800 pb-2">
              <span className="text-[10px] font-black uppercase text-amber-400">Tactical HUD Navigation</span>
              <span className="text-xs font-bold text-emerald-400">{distance ? `${distance} km` : "Location Active"}</span>
            </div>

            <div className="p-4 rounded-2xl bg-[#102A2E]/60 border border-purple-700 space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-400 text-slate-950 flex items-center justify-center font-black shrink-0">
                  <TurnIcon size={22} />
                </div>
                <div>
                  <span className="text-[10px] font-extrabold uppercase text-amber-300">Next Maneuver</span>
                  <p className="text-xs font-bold text-white leading-tight">{currentStep.instruction}</p>
                </div>
              </div>
            </div>

            {distance && (
              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-bold">Total Distance</span>
                  <span className="text-lg font-black text-amber-300">{distance} km</span>
                </div>
                <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block font-bold">
                    {durationSource === "estimated" ? "Est. Duration (avg speed)" : "Duration"}
                  </span>
                  {durationSource === "unavailable" ? (
                    <span className="text-[11px] font-bold text-amber-300 leading-tight block">
                      {durationNote || "Information unavailable"}
                    </span>
                  ) : (
                    <span className="text-lg font-black text-emerald-400">{durationMin ? `${durationMin} mins` : "—"}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <Link
              to="/checkout"
              className="w-full py-3 rounded-2xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs text-center block shadow-lg transition-transform hover:scale-105"
            >
              Request Booking For This Route ➔
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
