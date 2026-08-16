import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link, useSearchParams } from "react-router-dom"
import {
  FiCompass, FiPlus, FiX, FiCheck, FiMapPin, FiDollarSign,
  FiCalendar, FiActivity, FiShield, FiTruck, FiLayers, FiTrendingUp,
  FiAward, FiSun, FiNavigation, FiExternalLink
} from "react-icons/fi"
import destinationApi from "../api/destinationApi"
import Loader from "../components/common/Loader"
import useGeolocation from "../hooks/useGeolocation"

const calculateDistanceKm = (lat1, lon1, lat2, lon2) => {
  if (!lat1 || !lon1 || !lat2 || !lon2) return null
  const R = 6371
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return Math.round(R * c)
}

const PRESETS = [
  {
    name: "🏔️ Alpine Trekking Giants",
    ids: ["everest-base-camp", "annapurna-base-camp", "langtang-valley-kyanjin-gompa"],
  },
  {
    name: "🌊 Serene Lakes & Views",
    ids: ["phewa-lake-tal-barahi", "rara-lake-national-park", "nagarkot-himalayan-sunrise-viewpoint"],
  },
  {
    name: "🏛️ Spiritual & UNESCO Heritage",
    ids: ["pashupatinath-temple", "lumbini-sacred-garden-maya-devi-temple", "janakpurdham-janaki-mandir"],
  },
  {
    name: "🐅 Wildlife & Safaris",
    ids: ["chitwan-national-park-info-office", "bandipur-heritage-hill-station", "ilam-tea-gardens-kanyam"],
  },
]

const DEFAULT_DESTINATIONS = [
  {
    id: 1,
    name: "Pokhara & Phewa Lake",
    slug: "phewa-lake-tal-barahi",
    image: "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80",
    province: "Gandaki",
    district: "Kaski",
    altitude: "822m",
    category: "Lakes & Adventure",
    difficulty: "Easy / Leisure",
    daily_budget_npr: "NPR 4,500 ($34)",
    trip_budget_npr: "NPR 22,000 ($165)",
    best_season: "October to April",
    distance_ktm: "204.5 km (6-7 hrs drive / 25 min flight)",
    permits: "None for city / ACAP for trekking",
    activities: ["Boating", "Paragliding", "Sunrise Views", "Peace Pagoda"],
    hospital: "Western Regional / Manipal Hospital",
    police: "Tourist Police Pokhara (1144)",
    highlight: "Freshwater lake reflecting Mt. Machhapuchhre (Fishtail) and Annapurna massif.",
  },
  {
    id: 2,
    name: "Everest Base Camp (EBC)",
    slug: "everest-base-camp-ebc",
    image: "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop&q=80",
    province: "Koshi",
    district: "Solukhumbu",
    altitude: "5,364m",
    category: "Nature & Trekking",
    difficulty: "Challenging / Alpine",
    daily_budget_npr: "NPR 7,000 ($52)",
    trip_budget_npr: "NPR 85,000 ($640)",
    best_season: "March-May & Sept-Nov",
    distance_ktm: "Lukla flight (35 mins) + 12 days trek",
    permits: "Sagarmatha Entry (NPR 3,000) + Khumbu Permit (NPR 2,000)",
    activities: ["Alpine Trekking", "Kala Patthar Summit", "Sherpa Culture", "Glacier Walk"],
    hospital: "Himalayan Rescue Clinic / Lukla Hospital",
    police: "Namche Bazaar Police Post",
    highlight: "Foot of the world's highest peak surrounded by 8,000m giants.",
  },
  {
    id: 3,
    name: "Annapurna Base Camp (ABC)",
    slug: "annapurna-base-camp-abc-sanctuary",
    image: "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    province: "Gandaki",
    district: "Kaski",
    altitude: "4,130m",
    category: "Nature & Trekking",
    difficulty: "Moderate / Challenging",
    daily_budget_npr: "NPR 5,500 ($41)",
    trip_budget_npr: "NPR 45,000 ($338)",
    best_season: "March-May & Oct-Nov",
    distance_ktm: "Pokhara drive + 7-9 days trek",
    permits: "ACAP Permit (NPR 3,000) + TIMS Card (NPR 2,000)",
    activities: ["Sanctuary Amphitheater", "Jhinu Hot Springs", "Machhapuchhre Views"],
    hospital: "Ghandruk Health Post / Pokhara Teaching",
    police: "Ghandruk Police Post",
    highlight: "Natural amphitheater with a 360-degree panoramic wall of high Himalayan peaks.",
  }
]

export default function CompareDestinations() {
  const { position } = useGeolocation()
  const [selectedDestinations, setSelectedDestinations] = useState(DEFAULT_DESTINATIONS)
  const [availablePlaces, setAvailablePlaces] = useState([])
  const [searchQuery, setSearchQuery] = useState("")
  const [showAddDropdown, setShowAddDropdown] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchPlaces = async () => {
      try {
        const { data } = await destinationApi.getDestinations({ page_size: 50 })
        setAvailablePlaces(data.results || data || [])
      } catch (err) {
        console.error(err)
      }
    }
    fetchPlaces()
  }, [])

  const handleAddDestination = (dest) => {
    if (selectedDestinations.length >= 4) return
    if (selectedDestinations.some((d) => d.name === dest.name || d.slug === dest.slug)) return

    const formatted = {
      id: dest.id,
      name: dest.name,
      slug: dest.slug,
      image: dest.cover_image || dest.image || "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800",
      province: dest.province || "Nepal",
      district: dest.district || "District",
      altitude: dest.altitude || "1,400m",
      category: dest.category?.name || "Attraction",
      difficulty: dest.altitude && parseInt(dest.altitude) > 3500 ? "Challenging" : "Easy / Moderate",
      daily_budget_npr: `NPR ${round((dest.daily_budget_usd || 35) * 133).toLocaleString()} ($${dest.daily_budget_usd || 35})`,
      trip_budget_npr: `NPR ${round((dest.trip_budget_usd || 120) * 133).toLocaleString()} ($${dest.trip_budget_usd || 120})`,
      best_season: dest.best_time_to_visit || "October to April",
      distance_ktm: `${dest.distance_from_kathmandu_km || 180} km from Kathmandu`,
      lat: Number(dest.latitude || 27.7172),
      lng: Number(dest.longitude || 85.3240),
      permits: "TIMS / Local Entry where applicable",
      activities: ["Scenic Exploration", "Photography", "Cultural Immersion"],
      hospital: dest.nearest_hospital?.name || "District Hospital",
      police: dest.nearest_police?.name || "Nepal Police",
      highlight: dest.short_description || dest.description?.slice(0, 120) + "...",
    }

    setSelectedDestinations([...selectedDestinations, formatted])
    setShowAddDropdown(false)
    setSearchQuery("")
  }

  const handleRemove = (slug) => {
    if (selectedDestinations.length <= 2) return
    setSelectedDestinations(selectedDestinations.filter((d) => d.slug !== slug))
  }

  function round(num) {
    return Math.round(num)
  }

  return (
    <div className="container-app theme-gold py-8 space-y-6 animate-fadeIn">
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto space-y-2">
        <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
          Side-by-Side Comparison Engine
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 flex items-center justify-center gap-2">
          ⚖️ Compare Nepal Destinations & Treks
        </h1>
        <p className="text-sm text-gray-500">
          Evaluate altitude, budget, difficulty, travel time, and permit regulations side-by-side to choose your ideal Nepal adventure.
        </p>
      </div>

      {/* Preset Quick Tabs */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs font-bold text-gray-400">Curated Comparisons:</span>
        {PRESETS.map((p, i) => (
          <button
            key={i}
            onClick={() => {
              if (i === 0) setSelectedDestinations(DEFAULT_DESTINATIONS)
            }}
            className="px-3 py-1.5 rounded-xl bg-white border border-gray-200 text-xs font-bold text-gray-700 hover:border-purple-600 hover:text-purple-900 shadow-sm transition-all"
          >
            {p.name}
          </button>
        ))}
      </div>

      {/* Add Destination Search Bar */}
      <div className="flex justify-between items-center bg-purple-50/70 border border-purple-100 p-4 rounded-2xl">
        <div>
          <p className="text-xs font-bold text-purple-900">Comparing {selectedDestinations.length} of max 4 destinations</p>
          <p className="text-[11px] text-gray-500">Select any place from all 77 districts to add into the comparison matrix.</p>
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

      {/* Comparison Matrix Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {selectedDestinations.map((dest, idx) => (
          <motion.div
            key={dest.slug || idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl border border-purple-100 overflow-hidden shadow-xl flex flex-col justify-between"
          >
            <div>
              {/* Photo Banner */}
              <div className="h-44 w-full relative bg-slate-900 overflow-hidden">
                <img src={dest.image} alt={dest.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20" />
                {selectedDestinations.length > 2 && (
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
                  <p className="text-[11px] text-purple-200">{dest.district}, {dest.province} Province</p>
                </div>
              </div>

              {/* Metrics Table */}
              <div className="p-4 space-y-3.5 text-xs">
                {/* Altitude */}
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiCompass className="text-purple-600" /> Max Altitude:
                  </span>
                  <span className="font-mono font-black text-gray-900 bg-purple-50 px-2 py-0.5 rounded-md">
                    {dest.altitude}
                  </span>
                </div>

                {/* Difficulty */}
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiActivity className="text-amber-500" /> Difficulty:
                  </span>
                  <span className="font-bold text-gray-800">{dest.difficulty}</span>
                </div>

                {/* Daily Budget */}
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiDollarSign className="text-emerald-600" /> Daily Cost:
                  </span>
                  <span className="font-bold text-emerald-700">{dest.daily_budget_npr}</span>
                </div>

                {/* Full Trip Budget */}
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiTrendingUp className="text-blue-600" /> Trip Budget:
                  </span>
                  <span className="font-bold text-blue-700">{dest.trip_budget_npr}</span>
                </div>

                {/* Best Season */}
                <div className="flex justify-between items-center py-1.5 border-b border-gray-100">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiSun className="text-amber-500" /> Best Season:
                  </span>
                  <span className="font-bold text-gray-800">{dest.best_season}</span>
                </div>

                {/* Distance & Transit */}
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiTruck className="text-purple-600" /> Road & Transit Distance:
                  </span>
                  <p className="text-[11px] text-gray-700">{dest.distance_ktm}</p>
                </div>

                {/* Distance From Current GPS Location */}
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiNavigation className="text-emerald-600" /> From Your GPS Location:
                  </span>
                  <p className="text-[11px] font-bold text-emerald-800">
                    {dest.lat && dest.lng && position?.lat && position?.lng ? (
                      `${calculateDistanceKm(position.lat, position.lng, dest.lat, dest.lng)} km away from you`
                    ) : (
                      "📍 Using Pokhara GPS baseline: " + (calculateDistanceKm(28.2096, 83.9856, dest.lat || 27.7172, dest.lng || 85.3240) || "120") + " km away"
                    )}
                  </p>
                </div>

                {/* Permits */}
                <div className="py-1.5 border-b border-gray-100 space-y-1">
                  <span className="font-bold text-gray-500 flex items-center gap-1.5">
                    <FiShield className="text-rose-600" /> Permits Required:
                  </span>
                  <p className="text-[11px] text-gray-700">{dest.permits}</p>
                </div>

                {/* Highlight Info */}
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] text-gray-600 leading-relaxed italic">"{dest.highlight}"</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 pt-0 flex gap-2">
              <Link
                to={`/destinations/${dest.slug}`}
                className="flex-1 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs text-center transition-colors shadow"
              >
                View 24-Pt Details
              </Link>
              <Link
                to={`/navigation?dest=${encodeURIComponent(dest.name)}`}
                className="px-3.5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs text-center transition-colors shadow"
                title="Open GTA Navigation HUD"
              >
                Route ➔
              </Link>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
