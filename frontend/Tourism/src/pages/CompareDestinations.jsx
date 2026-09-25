import { useState, useEffect } from "react"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { motion } from "framer-motion"
import { Link, useSearchParams } from "react-router-dom"
import {
  FiCompass, FiPlus, FiX, FiDollarSign,
  FiActivity, FiShield, FiTruck, FiTrendingUp,
  FiSun, FiNavigation,
  FiColumns,
} from "react-icons/fi"
import destinationApi from "../api/destinationApi"
import EmptyState from "../components/common/EmptyState"
import Loader from "../components/common/Loader"
import useGeolocation from "../hooks/useGeolocation"
import { formatCoords, hasValidCoords, placeLocationLabel } from "../utils/placeUtils"

const calculateDistanceKm = (lat1, lon1, lat2, lon2) => {
  if (!hasValidCoords(lat1, lon1) || !hasValidCoords(lat2, lon2)) return null
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return Math.round(R * c)
}

const PRESETS = [
  {
    name: "Alpine Trekking Giants",
    ids: ["everest-base-camp", "annapurna-base-camp", "langtang-valley-kyanjin-gompa"],
  },
  {
    name: "Serene Lakes & Views",
    ids: ["phewa-lake-tal-barahi", "rara-lake-national-park", "nagarkot-himalayan-sunrise-viewpoint"],
  },
  {
    name: "Spiritual & UNESCO Heritage",
    ids: ["pashupatinath-temple", "lumbini-sacred-garden-maya-devi-temple", "janakpurdham-janaki-mandir"],
  },
  {
    name: "Wildlife & lowlands",
    ids: ["chitwan-national-park-info-office", "bardiya-national-park", "koshi-tappu-wildlife-reserve"],
  },
]

// Kathmandu reference point (Kathmandu Metropolitan City, per the internal
// geocoder index) used to DERIVE a straight-line distance when the curated
// road-distance field is missing. Golden rule: never say "not recorded"
// when the value can be calculated from coordinates.
const KATHMANDU = { lat: 27.7172, lng: 85.324 }
const UNAVAILABLE = "Information unavailable"

function formatComparePlace(dest) {
  if (!dest) return null
  const budget = dest.budget_estimation
  const lat = dest.latitude != null ? Number(dest.latitude) : null
  const lng = dest.longitude != null ? Number(dest.longitude) : null
  const straightFromKtm = calculateDistanceKm(KATHMANDU.lat, KATHMANDU.lng, lat, lng)
  return {
    id: dest.id,
    name: dest.name,
    slug: dest.slug,
    image: dest.cover_image_url || dest.cover_image || "",
    province: dest.province || "",
    district: dest.district || "",
    altitude: dest.altitude || UNAVAILABLE,
    category: dest.category_name || dest.category?.name || dest.category || "Attraction",
    difficulty: dest.feature_profile?.difficulty || UNAVAILABLE,
    daily_budget_npr: budget?.estimated_daily_budget != null
      ? `Recorded daily: NPR ${budget.estimated_daily_budget}`
      : dest.budget_estimate != null
        ? `Recorded estimate: ${dest.budget_estimate}`
        : UNAVAILABLE,
    trip_budget_npr: budget?.estimated_trip_budget != null
      ? `Recorded trip: NPR ${budget.estimated_trip_budget}`
      : UNAVAILABLE,
    best_season: dest.recommended_season || dest.best_time_to_visit || UNAVAILABLE,
    distance_ktm: dest.distance_from_kathmandu_km != null
      ? `${dest.distance_from_kathmandu_km} km from Kathmandu (road)`
      : straightFromKtm != null
        ? `≈ ${straightFromKtm} km from Kathmandu (straight line)`
        : UNAVAILABLE,
    lat,
    lng,
    permits: dest.travel_safety_tips || UNAVAILABLE,
    highlight: dest.short_description || dest.description || UNAVAILABLE,
    location: placeLocationLabel(dest),
  }
}

export default function CompareDestinations() {
  const { position, error: geoError, locating, retry: retryGeo } = useGeolocation({ auto: false })
  const [searchParams] = useSearchParams()
  const requestedSlug = searchParams.get("dest") || searchParams.get("destination") || ""
  const [selectedDestinations, setSelectedDestinations] = useState([])
  const [availablePlaces, setAvailablePlaces] = useState([])
  const [searchQuery, setSearchQuery] = useState("")
  // All-Nepal search: when the loaded list has no match, ask the live catalogue
  const [serverMatches, setServerMatches] = useState(null)
  useEffect(() => {
    const q = searchQuery.trim()
    if (q.length < 2) {
      const t0 = setTimeout(() => setServerMatches(null), 0)
      return () => clearTimeout(t0)
    }
    const t = setTimeout(async () => {
      try {
        const { data } = await destinationApi.getDestinations({ search: q, page_size: 12 })
        setServerMatches(data.results || [])
      } catch {
        setServerMatches(null)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [searchQuery])
  const [showAddDropdown, setShowAddDropdown] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [retry, setRetry] = useState(0)
  const [presetError, setPresetError] = useState("")

  const loadBySlugs = async (slugs) => {
    const rows = []
    for (const slug of slugs) {
      try {
        const { data } = await destinationApi.getById(slug)
        const formatted = formatComparePlace(data)
        if (formatted) rows.push(formatted)
      } catch {
        // Skip slugs that are not in the live catalogue.
      }
    }
    return rows
  }

  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true)
      setLoadError("")
      try {
        const { data } = await destinationApi.getDestinations({ page_size: 200 })
        const list = data.results || data || []
        setAvailablePlaces(list)
        const fromQuery = requestedSlug ? await loadBySlugs([requestedSlug]) : []
        const extras = list
          .filter((place) => !fromQuery.some((row) => row.slug === place.slug))
          .slice(0, Math.max(0, 3 - fromQuery.length))
          .map(formatComparePlace)
          .filter(Boolean)
        setSelectedDestinations([...fromQuery, ...extras].slice(0, 4))
      } catch {
        setSelectedDestinations([])
         setLoadError("We could not load the destination catalogue for comparison.")
      } finally {
        setLoading(false)
      }
    }
    bootstrap()
  }, [requestedSlug, retry])

  const handleAddDestination = (dest) => {
    if (selectedDestinations.length >= 4) return
    if (selectedDestinations.some((d) => d.name === dest.name || d.slug === dest.slug)) return
    const formatted = formatComparePlace(dest)
    if (!formatted) return
    setSelectedDestinations([...selectedDestinations, formatted])
    setShowAddDropdown(false)
    setSearchQuery("")
  }

  const handlePreset = async (preset) => {
    setPresetError("")
    setLoading(true)
    const fromList = availablePlaces.filter((place) =>
      preset.ids.some((token) => (place.slug || "").includes(token) || (place.name || "").toLowerCase().includes(token.replace(/-/g, " ")))
    ).slice(0, 4)
    const rows = fromList.length ? fromList.map(formatComparePlace).filter(Boolean) : await loadBySlugs(preset.ids)
    if (!rows.length) setPresetError("Those recorded places are not in the live catalogue.")
    setSelectedDestinations(rows.slice(0, 4))
    setLoading(false)
  }

  const handleRemove = (slug) => {
    if (selectedDestinations.length <= 1) return
    setSelectedDestinations(selectedDestinations.filter((d) => d.slug !== slug))
  }

  if (loading && !selectedDestinations.length) return <Loader />
  if (loadError && !selectedDestinations.length) return <div className="ny-page container-app py-10"><div className="ny-panel mx-auto max-w-xl p-6 text-center" role="alert"><p className="font-bold text-[var(--ny-danger)]">Comparison unavailable</p><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{loadError}</p><button type="button" onClick={() => setRetry((value) => value + 1)} className="ny-btn ny-btn-secondary mt-4">Try again</button></div></div>

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="compare" />
      <header>
        <span className="ny-kicker">Side-by-side comparison</span>
        <PageHeader title="Compare recorded Nepal destinations" subtitle="Choose up to four places and scan the stored facts that matter for your trip. Missing values stay clearly marked as information unavailable." icon={FiColumns} />
      </header>

      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs font-bold text-gray-400">Catalogue presets:</span>
        {PRESETS.map((p) => (
          <button
            key={p.name}
            onClick={() => handlePreset(p)}
            className="ny-btn ny-btn-secondary min-h-10 px-3 text-xs"
          >
            {p.name}
          </button>
        ))}
      </div>
      {presetError && <p className="text-center text-xs text-amber-800">{presetError}</p>}

      <div className="ny-panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <button type="button" onClick={retryGeo} disabled={locating} className="ny-btn ny-btn-secondary min-h-11 self-start text-xs sm:self-auto"><FiNavigation size={15} aria-hidden="true" />{position ? "Location active" : locating ? "Finding location…" : geoError ? "Try location again" : "Use my location"}</button>
        <div>
          <p className="text-xs font-bold text-[#102A2E]">Comparing {selectedDestinations.length} of max 4 destinations</p>
          <p className="text-[11px] text-gray-500">Add any approved place from the live catalogue.</p>
        </div>

        {selectedDestinations.length < 4 && (
          <div className="relative">
            <button
              onClick={() => setShowAddDropdown(!showAddDropdown)}
              className="px-4 py-2 rounded-xl bg-[#102A2E] hover:bg-[#1D5146] text-white font-bold text-xs flex items-center gap-1.5 shadow transition-all"
            >
              <FiPlus size={14} /> Add Place to Compare
            </button>

            {showAddDropdown && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl border border-gray-200 shadow-2xl p-3 z-30 space-y-2">
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search destination name..."
                  className="input-field py-1.5 text-xs w-full"
                  autoFocus
                />
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {[...availablePlaces
                    .filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase())),
                   ...(serverMatches || []).filter((sp) => !availablePlaces.some((ap) => ap.slug === sp.slug))]
                    .slice(0, 12)
                    .map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handleAddDestination(p)}
                        className="w-full text-left p-2 rounded-xl hover:bg-[#F7F8F5] text-xs font-semibold text-gray-800 flex items-center justify-between"
                      >
                        <span className="truncate">{p.name}</span>
                        <span className="text-[10px] text-emerald-700 font-bold ml-2">Add +</span>
                      </button>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!selectedDestinations.length && <EmptyState title="No destinations selected" subtitle="Add places from the catalogue to compare their recorded information." action={<Link to="/destinations" className="ny-btn ny-btn-primary">Browse destinations</Link>} />}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {selectedDestinations.map((dest, idx) => (
          <motion.div
            key={dest.slug || idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="ny-card flex flex-col overflow-hidden"
          >
            <div>
              <div className="h-44 w-full relative bg-slate-900 overflow-hidden">
                {dest.image ? (
                  <img src={dest.image} alt={dest.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white/70 text-sm">No recorded photo</div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20" />
                {selectedDestinations.length > 1 && (
                  <button
                    onClick={() => handleRemove(dest.slug)}
                    className="absolute top-3 right-3 p-1.5 rounded-full bg-black/60 text-white hover:bg-rose-600 transition-colors"
                    title="Remove from comparison"
                     aria-label={`Remove ${dest.name} from comparison`}
                  >
                    <FiX size={14} />
                  </button>
                )}
                <div className="absolute bottom-3 left-3 right-3 text-white">
                  <span className="px-2 py-0.5 rounded-full bg-amber-400 text-gray-950 text-[10px] font-black uppercase">
                    {dest.category}
                  </span>
                  <h3 className="text-lg font-black mt-1 leading-tight">{dest.name}</h3>
                  <p className="text-[11px] text-purple-200">{dest.location}</p>
                </div>
              </div>

              <div className="p-4 space-y-3.5 text-xs">
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiCompass className="text-emerald-700" /> Max Altitude:
                  </span>
                  <span className="font-mono font-black text-gray-900 bg-[#F7F8F5] px-2 py-0.5 rounded-md">
                    {dest.altitude}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiActivity className="text-amber-500" /> Difficulty:
                  </span>
                  <span className="font-bold text-gray-800">{dest.difficulty}</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiDollarSign className="text-emerald-600" /> Daily Cost:
                  </span>
                  <span className="font-bold text-emerald-700">{dest.daily_budget_npr}</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiTrendingUp className="text-blue-600" /> Trip Budget:
                  </span>
                  <span className="font-bold text-blue-700">{dest.trip_budget_npr}</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiSun className="text-amber-500" /> Best Season:
                  </span>
                  <span className="font-bold text-gray-800">{dest.best_season}</span>
                </div>
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiTruck className="text-emerald-700" /> From Kathmandu:
                  </span>
                  <p className="text-[11px] text-gray-700">{dest.distance_ktm}</p>
                </div>
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiNavigation className="text-emerald-600" /> From Your GPS:
                  </span>
                  <p className="text-[11px] font-bold text-emerald-800">
                    {hasValidCoords(dest.lat, dest.lng) && position?.lat != null && position?.lng != null
                      ? `≈ ${calculateDistanceKm(position.lat, position.lng, dest.lat, dest.lng)} km away from you (straight line)`
                      : hasValidCoords(dest.lat, dest.lng)
                        ? `Coordinates ${formatCoords(dest.lat, dest.lng)} — enable location to measure`
                        : "Information unavailable"}
                  </p>
                </div>
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiShield className="text-rose-600" /> Safety notes:
                  </span>
                  <p className="text-[11px] text-gray-700">{dest.permits}</p>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] text-gray-600 leading-relaxed italic">"{dest.highlight}"</p>
                </div>
              </div>
            </div>

            <div className="p-4 pt-0 flex gap-2">
              <Link
                to={`/destinations/${dest.slug}`}
                className="ny-btn ny-btn-primary flex-1"
              >
                View details
              </Link>
              <Link
                to={`/navigation?dest=${encodeURIComponent(dest.name)}`}
                className="ny-btn ny-btn-secondary px-3.5"
                title="Open navigation"
              >
                Route
              </Link>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
