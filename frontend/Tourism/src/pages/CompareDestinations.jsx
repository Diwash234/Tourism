import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Link, useSearchParams } from "react-router-dom"
import {
  FiCompass, FiPlus, FiX, FiDollarSign,
  FiActivity, FiShield, FiTruck, FiTrendingUp,
  FiSun, FiNavigation,
} from "react-icons/fi"
import destinationApi from "../api/destinationApi"
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
    name: "Wildlife & Safaris",
    ids: ["chitwan-national-park-info-office", "bandipur-heritage-hill-station", "ilam-tea-gardens-kanyam"],
  },
]

function formatComparePlace(dest) {
  if (!dest) return null
  const budget = dest.budget_estimation
  return {
    id: dest.id,
    name: dest.name,
    slug: dest.slug,
    image: dest.cover_image_url || dest.cover_image || "",
    province: dest.province || "",
    district: dest.district || "",
    altitude: dest.altitude || "Not recorded",
    category: dest.category_name || dest.category?.name || dest.category || "Attraction",
    difficulty: dest.feature_profile?.difficulty || "Not recorded",
    daily_budget_npr: budget?.estimated_daily_budget != null
      ? `Recorded daily: ${budget.estimated_daily_budget}`
      : dest.budget_estimate != null
        ? `Recorded estimate: ${dest.budget_estimate}`
        : "Budget not recorded",
    trip_budget_npr: budget?.estimated_trip_budget != null
      ? `Recorded trip: ${budget.estimated_trip_budget}`
      : "Trip budget not recorded",
    best_season: dest.recommended_season || dest.best_time_to_visit || "Not recorded",
    distance_ktm: dest.distance_from_kathmandu_km != null
      ? `${dest.distance_from_kathmandu_km} km from Kathmandu`
      : "Distance not recorded",
    lat: dest.latitude != null ? Number(dest.latitude) : null,
    lng: dest.longitude != null ? Number(dest.longitude) : null,
    permits: dest.travel_safety_tips || "Permit rules not recorded",
    highlight: dest.short_description || dest.description || "No description recorded",
    location: placeLocationLabel(dest),
  }
}

export default function CompareDestinations() {
  const { position } = useGeolocation()
  const [searchParams] = useSearchParams()
  const requestedSlug = searchParams.get("dest") || searchParams.get("destination") || ""
  const [selectedDestinations, setSelectedDestinations] = useState([])
  const [availablePlaces, setAvailablePlaces] = useState([])
  const [searchQuery, setSearchQuery] = useState("")
  const [showAddDropdown, setShowAddDropdown] = useState(false)
  const [loading, setLoading] = useState(true)
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
      try {
        const { data } = await destinationApi.getDestinations({ page_size: 50 })
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
      } finally {
        setLoading(false)
      }
    }
    bootstrap()
  }, [requestedSlug])

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

  return (
    <div className="container-app theme-gold py-8 space-y-6 animate-fadeIn">
      <div className="text-center max-w-3xl mx-auto space-y-2">
        <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
          Side-by-Side Comparison
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 flex items-center justify-center gap-2">
          Compare recorded Nepal destinations
        </h1>
        <p className="text-sm text-gray-500">
          Only stored fields are shown. Empty values stay “Not recorded”.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs font-bold text-gray-400">Catalogue presets:</span>
        {PRESETS.map((p) => (
          <button
            key={p.name}
            onClick={() => handlePreset(p)}
            className="px-3 py-1.5 rounded-xl bg-white border border-gray-200 text-xs font-bold text-gray-700 hover:border-purple-600 hover:text-purple-900 shadow-sm transition-all"
          >
            {p.name}
          </button>
        ))}
      </div>
      {presetError && <p className="text-center text-xs text-amber-800">{presetError}</p>}

      <div className="flex justify-between items-center bg-purple-50/70 border border-purple-100 p-4 rounded-2xl">
        <div>
          <p className="text-xs font-bold text-purple-900">Comparing {selectedDestinations.length} of max 4 destinations</p>
          <p className="text-[11px] text-gray-500">Add any approved place from the live catalogue.</p>
        </div>

        {selectedDestinations.length < 4 && (
          <div className="relative">
            <button
              onClick={() => setShowAddDropdown(!showAddDropdown)}
              className="px-4 py-2 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center gap-1.5 shadow transition-all"
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
                  {availablePlaces
                    .filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
                    .slice(0, 8)
                    .map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handleAddDestination(p)}
                        className="w-full text-left p-2 rounded-xl hover:bg-purple-50 text-xs font-semibold text-gray-800 flex items-center justify-between"
                      >
                        <span className="truncate">{p.name}</span>
                        <span className="text-[10px] text-purple-600 font-bold ml-2">Add +</span>
                      </button>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!selectedDestinations.length && (
        <p className="text-center text-sm text-slate-600">No recorded destinations are available to compare yet.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {selectedDestinations.map((dest, idx) => (
          <motion.div
            key={dest.slug || idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl border border-purple-100 overflow-hidden shadow-xl flex flex-col justify-between"
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
                    <FiCompass className="text-purple-600" /> Max Altitude:
                  </span>
                  <span className="font-mono font-black text-gray-900 bg-purple-50 px-2 py-0.5 rounded-md">
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
                    <FiTruck className="text-purple-600" /> From Kathmandu:
                  </span>
                  <p className="text-[11px] text-gray-700">{dest.distance_ktm}</p>
                </div>
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiNavigation className="text-emerald-600" /> From Your GPS:
                  </span>
                  <p className="text-[11px] font-bold text-emerald-800">
                    {hasValidCoords(dest.lat, dest.lng) && position?.lat && position?.lng
                      ? `${calculateDistanceKm(position.lat, position.lng, dest.lat, dest.lng)} km away from you`
                      : formatCoords(dest.lat, dest.lng) || "Coordinates not recorded"}
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
                className="flex-1 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs text-center transition-colors shadow"
              >
                View details
              </Link>
              <Link
                to={`/navigation?dest=${encodeURIComponent(dest.name)}`}
                className="px-3.5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs text-center transition-colors shadow"
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
