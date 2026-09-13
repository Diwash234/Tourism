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
import {
  FiMapPin,
  FiSearch,
  FiCrosshair,
  FiRefreshCw,
  FiNavigation,
  FiX,
  FiActivity,
  FiPhone,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import MapView from "../components/map/MapView"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import DestinationCard from "../components/cards/DestinationCard"
import HotelCard from "../components/cards/HotelCard"
import useGeolocation from "../hooks/useGeolocation"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import destinationApi from "../api/destinationApi"
import hotelApi from "../api/hotelApi"
import emergencyApi from "../api/emergencyApi"
import userApi from "../api/userApi"

const RADIUS_OPTIONS_KM = [5, 10, 25, 50, 100, 250]
const DEFAULT_RADIUS_KM = 25
const PAGE_SIZE = 24

const RESULT_TYPES = [
  { key: "destinations", label: "Destinations", noun: "destinations" },
  { key: "pois", label: "Real-world places", noun: "places" },
  { key: "hotels", label: "Hotels", noun: "hotels" },
  { key: "hospitals", label: "Hospitals", noun: "hospitals" },
]

const NearbyPlaces = () => {
  const { position, error: geoError, code: geoCode, locating, retry: retryGeo } = useGeolocation()
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

  const [activeType, setActiveType] = useState("destinations")
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
  const [matches, setMatches] = useState([])
  const [searching, setSearching] = useState(false)

  const [favoriteMap, setFavoriteMap] = useState({})
  // Real-world POIs (OpenStreetMap) — structured payload for the pois tab
  const [poiData, setPoiData] = useState(null)
  const [poiCat, setPoiCat] = useState("")

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
      const fail = () => {
        if (id !== requestId.current) return
        setPlaces([])
        setTotal(0)
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
          .getPOIsByCoords({ latitude: origin.lat, longitude: origin.lng, radius_km: Math.min(radiusKm, 25) })
          .then(({ data }) => {
            const all = Object.values(data?.categories || {}).flatMap((group) => group.results || [])
            setPoiData(data)
            setPoiCat((prev) => (prev && data?.categories?.[prev] ? prev : Object.keys(data?.categories || {})[0] || ""))
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
  }, [origin, radiusKm, activeType, reloadNonce])

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
        setSearching(false)
        return
      }
      setSearching(true)
      destinationApi
        .getAll({ search: q, page_size: 6 })
        .then(({ data }) => {
          const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
          setMatches(list.filter((d) => d.latitude != null && d.longitude != null))
        })
        .catch(() => setMatches([]))
        .finally(() => setSearching(false))
    }, 350)
    return () => clearTimeout(t)
  }, [query, pickerOpen])

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
    panel = geoError ? (geoCode === 1 ? "denied" : "location_error") : "locating"
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
        className="btn-primary !px-4 !py-2 text-sm"
      >
        <FiRefreshCw className="w-4 h-4" /> Try Again
      </button>
      <button
        type="button"
        onClick={() => setPickerOpen(true)}
        className="btn-outline !px-4 !py-2 text-sm"
      >
        <FiSearch className="w-4 h-4" /> Choose Location
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
    <div className="container-app py-10 fade-in theme-forest">
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
            onClick={() => setActiveType(t.key)}
            className={
              activeType === t.key
                ? "px-4 py-2 rounded-xl text-sm font-semibold bg-himalaya-600 text-white shadow-premium"
                : "px-4 py-2 rounded-xl text-sm font-semibold text-emerald-800 border border-emerald-200 hover:bg-emerald-50 transition-colors"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Search controls: origin + radius drive both the map and the list */}
      <div className="card-base p-4 mb-6 flex flex-wrap items-center gap-x-4 gap-y-3">
        <div className="flex items-center gap-2 min-w-0">
          <FiMapPin className="text-himalaya-500 shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-gray-400">Searching from</p>
            <p className="text-sm font-semibold text-emerald-900 truncate max-w-[220px] sm:max-w-none">
              {origin ? origin.label : locating ? "Finding your location…" : "Location not set"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 ml-auto">
          <button
            type="button"
            onClick={handleUseMyLocation}
            aria-label="Use my current location"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-semibold text-emerald-800 border border-emerald-200 hover:bg-emerald-50 transition-colors"
          >
            <FiCrosshair className="w-4 h-4" /> Use My Location
          </button>
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-semibold text-emerald-800 border border-emerald-200 hover:bg-emerald-50 transition-colors"
          >
            <FiSearch className="w-4 h-4" /> Choose Location
          </button>
          <label className="flex items-center gap-2 text-sm font-medium text-emerald-900">
            <span className="sr-only">Search radius in kilometres</span>
            Within
            <select
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="input-field !py-1.5 !px-2 text-sm w-auto"
            >
              {RADIUS_OPTIONS_KM.map((r) => (
                <option key={r} value={r}>
                  {r} km
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="rounded-xl2 overflow-hidden shadow-premium mb-6">
        <MapView
          userLocation={origin ? { lat: origin.lat, lng: origin.lng } : null}
          nearbyAttractions={places}
          height="420px"
        />
      </div>

      {/* Status panels — each failure mode gets its own message + recovery */}
      <div aria-live="polite">
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
            subtitle="The service didn't respond. Please retry — if it keeps failing, try again in a moment."
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
            subtitle={`Nothing in our database is within ${radiusKm} km of ${origin?.label}. Try a larger radius or a different starting point.`}
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
            <p className="text-sm text-gray-500 mb-4">{resultsSummary}</p>

            {activeType === "pois" && poiData && (
              <div className="space-y-5">
                {poiData.provider_error && (
                  <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                    {poiData.provider_error} Verified database places below are still shown.
                  </p>
                )}
                {(poiData.verified_database_places || []).length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-emerald-900 mb-2">Verified destinations near you</h3>
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
                        {row.opening_hours && <span className="text-gray-500">{row.opening_hours}</span>}
                        <a className="text-emerald-700 hover:underline" href={row.source_url} target="_blank" rel="noopener noreferrer">OpenStreetMap ↗</a>
                        <a className="text-emerald-700 hover:underline" href={directionsHref(row)} target="_blank" rel="noopener noreferrer"><FiNavigation className="w-3 h-3 inline" /> Directions</a>
                      </div>
                      <p className="text-[10px] text-gray-400 mt-2">{row.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeType === "destinations" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {places.map((p) => (
                  <div key={p.id} className="flex flex-col">
                    <DestinationCard
                      destination={p}
                      onToggleFavorite={handleToggleFavorite}
                      isFavorite={!!favoriteMap[p.id]}
                    />
                    {p.latitude != null && p.longitude != null && (
                      <a
                        href={directionsHref(p)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1.5 self-start inline-flex items-center gap-1 text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline"
                      >
                        <FiNavigation className="w-3 h-3" /> Get directions
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeType === "hotels" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {places.map((h) => (
                  <div key={h.id} className="flex flex-col">
                    <HotelCard hotel={h} />
                    {h.distance_km != null && (
                      <p className="mt-1.5 self-start text-xs font-medium text-emerald-700">
                        {h.distance_km} km from {origin?.label}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeType === "hospitals" && (
              <div className="space-y-3">
                {places.map((h) => (
                  <div key={h.id} className="card-base p-4 flex items-start gap-3">
                    <FiActivity className="text-himalaya-500 mt-1 shrink-0" aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-sm text-emerald-900">{h.name}</p>
                      <p className="text-xs text-gray-500">
                        {[
                          h.distance_km != null ? `${h.distance_km} km away` : null,
                          h.district,
                          h.address,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5">
                        {h.phone_number && (
                          <a
                            href={`tel:${h.phone_number}`}
                            className="text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline inline-flex items-center gap-1"
                          >
                            <FiPhone className="w-3 h-3" /> {h.phone_number}
                          </a>
                        )}
                        {h.latitude != null && h.longitude != null && (
                          <a
                            href={directionsHref(h)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline inline-flex items-center gap-1"
                          >
                            <FiNavigation className="w-3 h-3" /> Get directions
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
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
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

            {!searching && query.trim().length >= 2 && matches.length === 0 && (
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
                Type at least 2 characters — suggestions come from destinations in our database.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default NearbyPlaces
