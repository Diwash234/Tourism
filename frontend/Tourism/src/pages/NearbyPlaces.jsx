// Nearby = nearby *records from the live database*, derived per type:
//  - Destinations: GET /destinations/nearby/  (haversine on Destination)
//  - Hotels:       GET /hotels/nearby/        (haversine on Hotel)
//  - Hospitals:    GET /emergency/nearby/     (distance-ranked Hospital rows)
// All three are nearest-first with server-computed distance_km. There is no
// separate nearby dataset and nothing is hardcoded in this component.
//
// Location states are kept strictly distinct — "finding your location",
// "location blocked", "service error", "loading" and a genuine "nothing
// within this radius" each get their own message and recovery action, so a
// GPS denial can never masquerade as "No nearby places found".

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useSearchParams, Link } from "react-router-dom"
import { OpenNowBadge } from "../components/explore/FactBits"
import {
  FiMapPin,
  FiSearch,
  FiCrosshair,
  FiRefreshCw,
  FiNavigation,
  FiX,
  FiActivity,
  FiPhone,
  FiCompass,
  FiGrid,
  FiLayers,
  FiClock,
  FiAlertTriangle,
  FiShield,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import DestinationCard from "../components/cards/DestinationCard"
import HotelCard from "../components/cards/HotelCard"
import VerificationBadge from "../components/common/VerificationBadge"
import useGeolocation from "../hooks/useGeolocation"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import destinationApi from "../api/destinationApi"
import hotelApi from "../api/hotelApi"
import emergencyApi from "../api/emergencyApi"
import userApi from "../api/userApi"
import { getPlaceTypeIcon } from "../utils/placeTypeIcons"

const compassBearing = (lat1, lng1, lat2, lng2) => {
  if (lat1 == null || lng1 == null || lat2 == null || lng2 == null) return ""
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

/** Small "what kind of place is this" chip — icon + label, colour-coded. */
const PlaceTypeChip = ({ destination }) => {
  const type = getPlaceTypeIcon(destination)
  const TypeIcon = type.Icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold mb-1.5 ${type.chip}`}>
      <TypeIcon className="w-3 h-3" aria-hidden="true" />
      {type.label}
    </span>
  )
}

const RADIUS_OPTIONS_KM = [5, 10, 25, 50, 100, 250]
const DEFAULT_RADIUS_KM = 25
const PAGE_SIZE = 24

// /nearby-places?category=<OSM service category> (linked from site search)
// opens the matching tab; POI categories map onto the backend's groups.
const POI_DEFAULT_CATEGORIES = ["hotels", "hospitals", "police", "temples", "viewpoints", "restaurants", "banks"]
const CATEGORY_LINKS = {
  hospital: { type: "hospitals" }, clinic: { type: "hospitals" }, ambulance: { type: "hospitals" }, blood_bank: { type: "hospitals" },
  bank: { type: "pois", poi: "banks" }, atm: { type: "pois", poi: "atms" }, pharmacy: { type: "pois", poi: "pharmacies" },
  police: { type: "pois", poi: "police" }, hotel: { type: "hotels" },
}

const RESULT_TYPES = [
  { key: "destinations", label: "Destinations", noun: "destinations" },
  { key: "pois", label: "Real-world places", noun: "places" },
  { key: "hotels", label: "Hotels", noun: "hotels" },
  { key: "hospitals", label: "Hospitals", noun: "hospitals" },
]

const NearbyPlaces = () => {
  const { position, error: geoError, code: geoCode, locating, retry: retryGeo } = useGeolocation({ auto: false })
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()

  // A manually chosen origin (a real destination row) overrides the GPS fix.
  const [manualOrigin, setManualOrigin] = useState(null)
  const origin = useMemo(
    () =>
      manualOrigin ||
      (position ? { lat: position.lat, lng: position.lng, label: "Your location" } : null),
    [manualOrigin, position]
  )

  const [searchParams] = useSearchParams()
  const categoryLink = CATEGORY_LINKS[(searchParams.get("category") || "").toLowerCase()] || null
  const poiFocus = categoryLink?.poi || ""
  const [activeType, setActiveType] = useState(categoryLink?.type || "destinations")
  const activeMeta = RESULT_TYPES.find((t) => t.key === activeType)

  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM)
  const [reloadNonce, setReloadNonce] = useState(0)
  const [places, setPlaces] = useState([])
  const [total, setTotal] = useState(0)
  // idle | loading | done | error — "idle" only exists before the first
  // request resolves, and renders as loading whenever an origin is known.
  const [fetchState, setFetchState] = useState("idle")
  const requestId = useRef(0)

  const [pickerOpen, setPickerOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [searchError, setSearchError] = useState("")
  const [fetchError, setFetchError] = useState("")
  const [matches, setMatches] = useState([])
  const [searching, setSearching] = useState(false)

  const [favoriteMap, setFavoriteMap] = useState({})
  // Real-world POIs (OpenStreetMap) — structured payload for the pois tab
  const [poiData, setPoiData] = useState(null)
  const [poiCat, setPoiCat] = useState("")
  const [openNow, setOpenNow] = useState(false)
  const [viewMode, setViewMode] = useState("split") // "split" | "grid" | "radar"
  const [filterText, setFilterText] = useState("")
  const [sortBy, setSortBy] = useState("distance") // "distance" | "name"

  const displayedPlaces = useMemo(() => {
    let list = [...places]
    if (filterText.trim()) {
      const q = filterText.toLowerCase().trim()
      list = list.filter((p) =>
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.district && p.district.toLowerCase().includes(q)) ||
        (p.address && p.address.toLowerCase().includes(q)) ||
        (p.category && p.category.toLowerCase().includes(q)) ||
        (p.type && p.type.toLowerCase().includes(q))
      )
    }
    if (sortBy === "name") {
      list.sort((a, b) => (a.name || "").localeCompare(b.name || ""))
    } else {
      list.sort((a, b) => {
        const approxA = a.is_approximate || a.is_approximate_coordinate ? 1 : 0
        const approxB = b.is_approximate || b.is_approximate_coordinate ? 1 : 0
        if (approxA !== approxB) return approxA - approxB
        return (Number(a.distance_km) || 0) - (Number(b.distance_km) || 0)
      })
    }
    return list
  }, [places, filterText, sortBy])

  // --- data fetch: frontend sends coordinates, backend runs the distance query
  useEffect(() => {
    if (!origin) return undefined
    const id = ++requestId.current
    // Microtask kick keeps synchronous setState out of the effect flush
    // (react-hooks/set-state-in-effect).
    Promise.resolve().then(() => {
      if (id !== requestId.current) return
      setFetchState("loading")

      const settle = (list, count) => {
        if (id !== requestId.current) return
        setPlaces(list)
        setTotal(count)
        setFetchState("done")
      }
      const fail = (error) => {
        if (id !== requestId.current) return
        setPlaces([])
        setTotal(0)
        // Keep the real reason (connection refused, timeout, HTTP error) so
        // the page says what actually went wrong instead of a generic line.
        setFetchError(
          error?.apiUnreachable
            ? error.message
            : error?.response?.status
              ? `The server returned HTTP ${error.response.status}${error.response.data?.detail ? `: ${error.response.data.detail}` : ""}.`
              : error?.message || ""
        )
        setFetchState("error")
      }

      if (activeType === "hotels") {
        hotelApi
          .nearby({ latitude: origin.lat, longitude: origin.lng, radius_km: radiusKm, page_size: PAGE_SIZE })
          .then(({ data }) => {
            const list = Array.isArray(data?.results) ? data.results : []
            settle(list, typeof data?.count === "number" ? data.count : list.length)
          })
          .catch(fail)
        return
      }
      if (activeType === "pois") {
        destinationApi
          .getPOIsByCoords({ latitude: origin.lat, longitude: origin.lng, radius_km: Math.min(radiusKm, 25), ...(openNow ? { open_now: 1 } : {}),
            ...(poiFocus ? { categories: [...new Set([...POI_DEFAULT_CATEGORIES, poiFocus])].join(",") } : {}) })
          .then(({ data }) => {
            const all = Object.values(data?.categories || {}).flatMap((group) => group.results || [])
            setPoiData(data)
            setPoiCat((prev) => (prev && data?.categories?.[prev] ? prev : (poiFocus && data?.categories?.[poiFocus] ? poiFocus : Object.keys(data?.categories || {})[0] || "")))
            settle([...all, ...(data?.verified_database_places || [])], all.length + (data?.verified_database_places || []).length)
          })
          .catch(fail)
        return
      }
      if (activeType === "hospitals") {
        emergencyApi
          .nearby(origin.lat, origin.lng, { radius_km: radiusKm, limit: PAGE_SIZE })
          .then(({ data }) => {
            const list = Array.isArray(data?.hospitals) ? data.hospitals : []
            settle(list, typeof data?.counts?.hospitals_within_radius === "number" ? data.counts.hospitals_within_radius : list.length)
          })
          .catch(fail)
        return
      }
      destinationApi
        .getNearby({ latitude: origin.lat, longitude: origin.lng, radius_km: radiusKm, page_size: PAGE_SIZE })
        .then(({ data }) => {
          const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
          // The chosen starting point is not "nearby" to itself.
          const filtered = list.filter((p) => p.id !== origin.destinationId)
          settle(filtered, typeof data?.count === "number" ? data.count : list.length)
        })
        .catch(fail)
    })
  }, [origin, radiusKm, activeType, reloadNonce, openNow, poiFocus])

  // --- favorites (same contract as DestinationList; destinations tab only)
  useEffect(() => {
    if (!isAuthenticated) return
    userApi
      .getFavorites()
      .then(({ data }) => {
        const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
        const map = {}
        list.forEach((fav) => {
          map[fav.destination] = fav.id
        })
        setFavoriteMap(map)
      })
      .catch(() => {})
  }, [isAuthenticated])

  const handleToggleFavorite = useCallback(
    async (destId) => {
      if (!isAuthenticated) return showToast("Please login to save favorites", "info")
      const recordId = favoriteMap[destId]
      try {
        if (recordId) {
          await userApi.removeFavorite(recordId)
          setFavoriteMap((prev) => {
            const next = { ...prev }
            delete next[destId]
            return next
          })
          showToast("Removed from favorites", "info")
        } else {
          const { data } = await userApi.addFavorite(destId)
          setFavoriteMap((prev) => ({ ...prev, [destId]: data.id }))
          showToast("Saved to favorites ❤️", "success")
        }
      } catch {
        showToast("Could not update favorites", "error")
      }
    },
    [isAuthenticated, favoriteMap, showToast]
  )

  // --- manual origin picker: searches the real destinations API (debounced)
  useEffect(() => {
    if (!pickerOpen) return undefined
    const q = query.trim()
    const t = setTimeout(() => {
      if (q.length < 2) {
        setMatches([])
        setSearchError("")
        setSearching(false)
        return
      }
      setSearching(true)
      destinationApi
        .getAll({ search: q, page_size: 6 })
        .then(({ data }) => {
          const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
          setMatches(list.filter((d) => d.latitude != null && d.longitude != null))
          setSearchError("")
        })
        .catch((error) => {
          // A failed request is NOT "no match": say the server could not be
          // reached so the user doesn't think the place doesn't exist.
          setMatches([])
          setSearchError(error?.apiUnreachable ? error.message : error?.response?.data?.detail || "Couldn't reach the destination search. Check your connection (or that the backend is running) and try again.")
        })
        .finally(() => setSearching(false))
    }, 350)
    return () => clearTimeout(t)
  }, [query, pickerOpen])

  useEffect(() => {
    if (!pickerOpen) return undefined
    const closeOnEscape = (event) => {
      if (event.key === "Escape") {
        setPickerOpen(false)
        setQuery("")
      }
    }
    window.addEventListener("keydown", closeOnEscape)
    return () => window.removeEventListener("keydown", closeOnEscape)
  }, [pickerOpen])

  const chooseOrigin = (dest) => {
    setManualOrigin({
      lat: Number(dest.latitude),
      lng: Number(dest.longitude),
      label: dest.name,
      destinationId: dest.id,
    })
    setPickerOpen(false)
    setQuery("")
    setMatches([])
  }

  const handleUseMyLocation = () => {
    setManualOrigin(null)
    retryGeo()
  }

  // --- which panel to show: never collapse distinct failures into "empty"
  let panel
  if (!origin) {
    panel = geoError ? (geoCode === 1 ? "denied" : "location_error") : locating ? "locating" : "location_prompt"
  } else if (fetchState === "loading" || fetchState === "idle") {
    panel = "loading"
  } else if (fetchState === "error") {
    panel = "error"
  } else if (places.length === 0) {
    panel = "empty"
  } else {
    panel = "results"
  }

  const nextRadius = RADIUS_OPTIONS_KM.find((r) => r > radiusKm)
  const noun = activeMeta.noun
  const label = activeMeta.label

  const locationActions = (
    <div className="flex flex-wrap items-center justify-center gap-3">
      <button
        type="button"
        onClick={handleUseMyLocation}
        className="ny-btn ny-btn-primary min-h-11"
      >
        {geoError ? <FiRefreshCw className="h-4 w-4" aria-hidden="true" /> : <FiCrosshair className="h-4 w-4" aria-hidden="true" />}
        {geoError ? "Try Again" : "Use My Location"}
      </button>
      <button
        type="button"
        onClick={() => setPickerOpen(true)}
        className="ny-btn ny-btn-secondary min-h-11"
      >
        <FiSearch className="h-4 w-4" aria-hidden="true" /> Choose Location
      </button>
    </div>
  )

  const resultsSummary =
    total > places.length
      ? `Showing the ${places.length} nearest of ${total} ${noun} within ${radiusKm} km — nearest first`
      : `Found ${places.length} ${noun} within ${radiusKm} km — nearest first`

  const directionsHref = (item) =>
    `https://www.google.com/maps/dir/?api=1&destination=${item.latitude},${item.longitude}`

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="nearby-places" />
      <PageHeader title="Nearby Places" icon={FiMapPin} />

      {/* Result type tabs — all backed by real, distance-ranked DB queries */}
      <div className="flex flex-wrap gap-2 mb-4" role="tablist" aria-label="Nearby result types">
        {RESULT_TYPES.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={activeType === t.key}
            aria-controls="nearby-results-panel"
            onClick={() => setActiveType(t.key)}
            className={
              activeType === t.key
                ? "min-h-11 rounded-xl bg-[var(--ny-green)] px-4 py-2 text-sm font-semibold text-white shadow-[var(--ny-shadow)]"
                : "min-h-11 rounded-xl border border-[var(--ny-border)] px-4 py-2 text-sm font-semibold text-[var(--ny-green)] transition-colors hover:bg-[var(--ny-soft-green)]"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Search controls: origin + radius drive both the map and the list */}
      <div className="card-base p-4 mb-6 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
          <div className="flex items-center gap-2 min-w-0">
            <FiMapPin className="text-himalaya-500 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-wider text-gray-400">Searching from</p>
              <p className="text-sm font-semibold text-emerald-900 truncate max-w-[220px] sm:max-w-none">
                {origin ? origin.label : locating ? "Finding your location…" : "Location not set"}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleUseMyLocation}
              aria-label="Use my current location"
              className="inline-flex min-h-10 items-center gap-1.5 rounded-xl border border-[var(--ny-border)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--ny-green)] transition-colors hover:bg-[var(--ny-soft-green)] shadow-2xs"
            >
              <FiCrosshair className="w-3.5 h-3.5" /> Use My Location
            </button>
            <button
              type="button"
              onClick={() => setPickerOpen(true)}
              className="inline-flex min-h-10 items-center gap-1.5 rounded-xl border border-[var(--ny-border)] bg-white px-3 py-1.5 text-xs font-semibold text-[var(--ny-green)] transition-colors hover:bg-[var(--ny-soft-green)] shadow-2xs"
            >
              <FiSearch className="w-3.5 h-3.5" /> Choose Location
            </button>
          </div>
        </div>

        {/* Quick Radius Selector Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-bold text-slate-500 mr-1">Search Radius:</span>
            {RADIUS_OPTIONS_KM.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRadiusKm(r)}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                  radiusKm === r
                    ? "bg-emerald-700 text-white shadow-2xs"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {r} km
              </button>
            ))}
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
            {[
              { id: "split", label: "🗺️ Split Map", icon: FiLayers },
              { id: "grid", label: "📱 Grid", icon: FiGrid },
              { id: "radar", label: "🧭 Radar", icon: FiCompass },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setViewMode(m.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  viewMode === m.id
                    ? "bg-white text-emerald-900 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Emergency Hotlines Strip when viewing Hospitals or Police */}
      {(activeType === "hospitals" || (activeType === "pois" && poiCat === "police")) && (
        <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-950 flex flex-wrap items-center justify-between gap-3 text-xs shadow-2xs">
          <div className="flex items-center gap-2">
            <FiShield className="text-rose-600 w-4 h-4 shrink-0" />
            <span className="font-black uppercase tracking-wider text-[11px]">24/7 Nepal Emergency Dispatch</span>
          </div>
          <div className="flex flex-wrap items-center gap-3 font-bold text-xs">
            <a href="tel:1144" className="hover:underline flex items-center gap-1">👮 Tourist Police: <strong className="text-rose-700">1144</strong></a>
            <span className="text-rose-300">·</span>
            <a href="tel:100" className="hover:underline flex items-center gap-1">🚔 Police: <strong className="text-rose-700">100</strong></a>
            <span className="text-rose-300">·</span>
            <a href="tel:102" className="hover:underline flex items-center gap-1">🚑 Medical Ambulance: <strong className="text-rose-700">102</strong></a>
            <span className="text-rose-300">·</span>
            <a href="tel:1114" className="hover:underline flex items-center gap-1">🚁 APF Rescue: <strong className="text-rose-700">1114</strong></a>
          </div>
        </div>
      )}

      {/* Map View Container (Shown in split and radar modes) */}
      {viewMode !== "grid" && (
        <div className="rounded-xl2 overflow-hidden shadow-premium mb-6">
          <MapView
            userLocation={origin ? { lat: origin.lat, lng: origin.lng } : null}
            nearbyAttractions={displayedPlaces}
            height={viewMode === "radar" ? "320px" : "420px"}
          />
        </div>
      )}

      {/* Status panels — each failure mode gets its own message + recovery */}
      <div id="nearby-results-panel" role="tabpanel" aria-live="polite" aria-busy={panel === "loading" || panel === "locating"}>
        {panel === "location_prompt" && (
          <EmptyState
            icon={FiMapPin}
            title="Choose a starting point"
            subtitle="Share your location or choose a destination to rank nearby hospitals, hotels and places by real distance."
            action={locationActions}
          />
        )}

        {panel === "locating" && <Loader text={`Finding nearby ${noun}…`} />}

        {panel === "loading" && <Loader text={`Finding nearby ${noun}…`} />}

        {panel === "denied" && (
          <EmptyState
            icon={FiMapPin}
            title="Location access is turned off."
            subtitle="Your browser is blocking location access. Allow it in your browser settings and try again — or pick a starting point from our destinations."
            action={locationActions}
          />
        )}

        {panel === "location_error" && (
          <EmptyState
            icon={FiMapPin}
            title="We couldn't access your location."
            subtitle="Your location is unavailable right now. You can try again, or choose a starting point manually."
            action={locationActions}
          />
        )}

        {panel === "error" && (
          <EmptyState
            icon={FiRefreshCw}
            title={`${label} couldn't be loaded.`}
            subtitle={fetchError || "The request failed. Please retry."}
            action={
              <button
                type="button"
                onClick={() => setReloadNonce((n) => n + 1)}
                className="btn-primary !px-4 !py-2 text-sm"
              >
                <FiRefreshCw className="w-4 h-4" /> Retry
              </button>
            }
          />
        )}

        {panel === "empty" && (
          <EmptyState
            icon={FiSearch}
            title={`No ${noun} found within ${radiusKm} km.`}
            subtitle={`No recorded places are within ${radiusKm} km of ${origin?.label}. Try a larger radius or a different starting point.`}
            action={
              <div className="flex flex-wrap items-center justify-center gap-3">
                {nextRadius && (
                  <button
                    type="button"
                    onClick={() => setRadiusKm(nextRadius)}
                    className="btn-primary !px-4 !py-2 text-sm"
                  >
                    Expand to {nextRadius} km
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setPickerOpen(true)}
                  className="btn-outline !px-4 !py-2 text-sm"
                >
                  <FiSearch className="w-4 h-4" /> Change Location
                </button>
              </div>
            }
          />
        )}

        {panel === "results" && (
          <>
            {/* Live Filter & Sorting Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4 p-3 rounded-2xl bg-slate-50 border border-slate-200">
              <div className="relative min-w-[200px] flex-1 max-w-md">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-3.5 h-3.5" />
                <input
                  type="text"
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  placeholder={`Filter ${noun} by name or district…`}
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-600"
                />
                {filterText && (
                  <button
                    type="button"
                    onClick={() => setFilterText("")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <FiX size={13} />
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 font-bold">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-2.5 py-1 rounded-xl border border-slate-300 bg-white font-semibold text-slate-700"
                >
                  <option value="distance">Nearest First (km)</option>
                  <option value="name">Alphabetical (A–Z)</option>
                </select>
                <span className="text-[11px] text-slate-400 font-bold ml-1">
                  ({displayedPlaces.length} of {places.length})
                </span>
              </div>
            </div>

            <p className="text-xs text-gray-500 mb-4">{resultsSummary}</p>

            {/* RADAR & COMPASS VIEW MODE */}
            {viewMode === "radar" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {displayedPlaces.map((item) => {
                  const km = Number(item.distance_km)
                  const bearing = origin?.lat && item.latitude ? compassBearing(origin.lat, origin.lng, item.latitude, item.longitude) : ""
                  const arrow = compassArrow(bearing)
                  const estMins = km ? Math.max(2, Math.round((km / 35) * 60)) : null
                  return (
                    <div key={item.id || item.slug || `${item.type}-${item.name}`} className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-3">
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-black uppercase">
                            {item.category || item.type || noun}
                          </span>
                          {bearing && (
                            <span className="px-2 py-0.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs font-black flex items-center gap-1">
                              <span>{arrow}</span>
                              <span>{bearing}</span>
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-sm text-slate-900 mt-2 truncate">{item.name}</h4>
                        <p className="text-xs text-slate-500 truncate">{item.address || item.district || "Location recorded"}</p>
                      </div>

                      <div className="pt-2 border-t border-slate-100 space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-black text-emerald-800">
                            {km != null ? `≈ ${km.toFixed(1)} km` : "Proximity verified"}
                          </span>
                          {estMins && (
                            <span className="text-slate-500 text-[11px] flex items-center gap-1">
                              <FiClock size={11} /> ~{estMins}m drive
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <Link
                            to={`/navigation?dest=${encodeURIComponent(item.name)}${origin?.label ? `&origin=${encodeURIComponent(origin.label)}` : ""}`}
                            className="flex-1 py-1.5 px-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs text-center flex items-center justify-center gap-1"
                          >
                            <FiNavigation size={12} /> Road Route
                          </Link>
                          {item.latitude != null && (
                            <a
                              href={directionsHref(item)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="py-1.5 px-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-bold"
                              title="Google Directions"
                            >
                              Maps ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* Standard Views (Split / Grid) */}
            {viewMode !== "radar" && activeType === "pois" && poiData && (
              <div className="space-y-5">
                {poiData.provider_error && (
                  <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                    {poiData.provider_error} Verified database places below are still shown.
                  </p>
                )}
                {(poiData.verified_database_places || []).length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-emerald-900 mb-2">Recorded destinations near you</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                      {poiData.verified_database_places.map((row) => (
                        <a key={row.slug} href={row.source_url} className="card-base p-4 hover:shadow-md transition">
                          <p className="font-semibold text-sm text-emerald-900">{row.name}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{row.distance_km} km · {row.source}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
                <div className="flex flex-wrap items-center gap-3">
                  <label className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-900">
                    <input type="checkbox" checked={openNow} onChange={(e) => setOpenNow(e.target.checked)} className="h-4 w-4 accent-emerald-700" />
                    Open now only
                  </label>
                  {poiData.hours_note && <span className="text-xs text-gray-500">{poiData.hours_note}</span>}
                </div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(poiData.categories || {}).map(([key, group]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setPoiCat(key)}
                      className={`rounded-full px-3.5 py-1.5 text-xs font-bold transition-all ${poiCat === key ? "bg-emerald-700 text-white shadow" : "bg-white border border-emerald-200 text-emerald-800 hover:bg-emerald-50"}`}
                    >
                      {group.icon} {group.label} ({(group.results || []).length})
                    </button>
                  ))}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                  {(poiData.categories?.[poiCat]?.results || []).map((row) => (
                    <div key={`${row.osm_type}-${row.osm_id}`} className="card-base p-4">
                      <p className="font-semibold text-sm text-emerald-900">{row.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {[row.distance_km != null ? `${row.distance_km} km` : null, row.religion, row.address].filter(Boolean).join(" · ")}
                      </p>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs">
                        {row.phone && <a className="inline-flex items-center gap-1 text-emerald-700 hover:underline" href={`tel:${row.phone}`}><FiPhone className="w-3 h-3" /> {row.phone}</a>}
                        {row.website && <a className="text-emerald-700 hover:underline" href={row.website} target="_blank" rel="noopener noreferrer">Website</a>}
                        {row.hours ? <OpenNowBadge hours={row.hours} /> : row.opening_hours && <span className="text-gray-500">{row.opening_hours}</span>}
                        <a className="text-emerald-700 hover:underline" href={row.source_url} target="_blank" rel="noopener noreferrer">OpenStreetMap ↗</a>
                        <Link to={`/navigation?dest=${encodeURIComponent(row.name)}${origin?.label ? `&origin=${encodeURIComponent(origin.label)}` : ""}`} className="text-emerald-700 hover:underline font-bold inline-flex items-center gap-1"><FiNavigation className="w-3 h-3" /> Road route</Link>
                      </div>
                      <p className="text-[10px] text-gray-400 mt-2">{row.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {viewMode !== "radar" && activeType === "destinations" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {displayedPlaces.map((p) => (
                  <div key={p.id} className="flex flex-col">
                    <PlaceTypeChip destination={p} />
                    <DestinationCard
                      destination={p}
                      onToggleFavorite={handleToggleFavorite}
                      isFavorite={!!favoriteMap[p.id]}
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                      <Link
                        to={`/navigation?dest=${encodeURIComponent(p.name)}${origin?.label ? `&origin=${encodeURIComponent(origin.label)}` : ""}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-emerald-800 hover:text-emerald-950 hover:underline"
                      >
                        <FiNavigation className="w-3.5 h-3.5 text-emerald-700" /> Road route
                      </Link>
                      {p.latitude != null && p.longitude != null && (
                        <a
                          href={directionsHref(p)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800 hover:underline"
                        >
                          Google Maps ↗
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {viewMode !== "radar" && activeType === "hotels" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {displayedPlaces.map((h) => (
                  <div key={h.id} className="flex flex-col">
                    <HotelCard hotel={h} />
                    <div className="mt-2 flex flex-wrap items-center justify-between text-xs font-medium">
                      {h.distance_km != null && (
                        <span className="text-emerald-800 font-bold">
                          {h.distance_label || (h.is_approximate ? `≈ ${h.distance_km} km (area point)` : `${h.distance_km} km`)} from {origin?.label}
                        </span>
                      )}
                      <Link
                        to={`/navigation?dest=${encodeURIComponent(h.name)}${origin?.label ? `&origin=${encodeURIComponent(origin.label)}` : ""}`}
                        className="inline-flex items-center gap-1 text-emerald-700 hover:underline font-bold"
                      >
                        <FiNavigation className="w-3 h-3" /> Road route
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {viewMode !== "radar" && activeType === "hospitals" && (
              <div className="space-y-3">
                {displayedPlaces.map((h) => (
                  <div key={h.id} className="card-base p-4 flex items-start gap-3 hover:shadow-md transition">
                    <FiActivity className="text-rose-600 mt-1 shrink-0 w-5 h-5" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-sm text-slate-900 flex flex-wrap items-center gap-2">
                        {h.name}<VerificationBadge record={h} compact />
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {[
                          h.distance_label || (h.distance_km != null ? (h.is_approximate ? `≈ ${h.distance_km} km (area point)` : `${h.distance_km} km straight-line`) : null),
                          h.district,
                          h.address,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs">
                        {h.phone_number && (
                          <a
                            href={`tel:${h.phone_number}`}
                            className="font-bold text-rose-700 hover:underline inline-flex items-center gap-1"
                          >
                            <FiPhone className="w-3.5 h-3.5" /> {h.phone_number}
                          </a>
                        )}
                        <Link
                          to={`/navigation?dest=${encodeURIComponent(h.name)}${origin?.label ? `&origin=${encodeURIComponent(origin.label)}` : ""}`}
                          className="font-bold text-emerald-700 hover:underline inline-flex items-center gap-1"
                        >
                          <FiNavigation className="w-3.5 h-3.5" /> Road route
                        </Link>
                        {h.latitude != null && h.longitude != null && (
                          <a
                            href={directionsHref(h)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-500 hover:text-slate-700 hover:underline inline-flex items-center gap-1"
                          >
                            Google Maps ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Manual origin picker — options come from the destinations API */}
      {pickerOpen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-20 sm:pt-28"
          onClick={() => setPickerOpen(false)}
          role="presentation"
        >
          <div
            className="card-base w-full max-w-md p-5"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Choose a starting point"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold text-emerald-900">Choose a starting point</h3>
              <button
                type="button"
                onClick={() => setPickerOpen(false)}
                aria-label="Close location picker"
                className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-sm)] text-[var(--ny-text-muted)] transition hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>

            <div className="relative mb-3">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search destinations or cities…"
                aria-label="Search destinations to use as a starting point"
                className="input-field w-full !pl-9"
              />
            </div>

            {searching && <p className="text-sm text-gray-400 py-4 text-center">Searching…</p>}

            {!searching && searchError && (
              <p role="alert" className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2 my-2 text-center">
                {searchError}
              </p>
            )}

            {!searching && !searchError && query.trim().length >= 2 && matches.length === 0 && (
              <p className="text-sm text-gray-400 py-4 text-center">
                No destinations match “{query.trim()}”.
              </p>
            )}

            {!searching && matches.length > 0 && (
              <ul className="space-y-1 max-h-72 overflow-y-auto">
                {matches.map((d) => (
                  <li key={d.id}>
                    <button
                      type="button"
                      onClick={() => chooseOrigin(d)}
                      className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-emerald-50 transition-colors flex items-center justify-between gap-3"
                    >
                      <span className="text-sm font-semibold text-emerald-900 truncate">
                        {d.name}
                      </span>
                      <span className="text-xs text-gray-400 shrink-0">
                        {[d.city, d.district, d.province].filter(Boolean).slice(0, 2).join(", ")}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {!searching && query.trim().length < 2 && (
              <p className="text-xs text-gray-400 py-3 text-center">
                Type at least 2 characters — suggestions come from recorded destinations.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NearbyPlaces
