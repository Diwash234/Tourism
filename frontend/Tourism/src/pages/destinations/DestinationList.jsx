import { useEffect, useState } from "react"
import { useSearchParams, Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { FiMapPin, FiCompass, FiPlus, FiCpu, FiArrowRight, FiSearch } from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"

import DestinationCard from "../../components/cards/DestinationCard"
import DestinationCardSkeleton from "../../components/cards/DestinationCardSkeleton"
import SearchBar from "../../components/common/SearchBar"
import Filter from "../../components/common/Filter"
import Pagination from "../../components/common/Pagination"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import Breadcrumbs from "../../components/common/Breadcrumbs"

import useGeolocation from "../../hooks/useGeolocation"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import { PAGE_SIZE } from "../../utils/constants"

// Type chips control the "attractions vs hotels" split
const TYPE_OPTIONS = [
  { label: "🏔️ Attractions", value: "attraction" },
  { label: "🏨 Hotels & Stays", value: "hotel" },
  { label: "🌐 All Places", value: "all" },
]

const CATEGORY_OPTIONS = [
  { label: "All Categories", value: "" },
  { label: "🏔️ Mountains & Trekking", value: "nature-trekking" },
  { label: "🌊 Lakes & Water", value: "lakes-water-activities" },
  { label: "🐅 Wildlife & Safari", value: "wildlife" },
  { label: "🏛️ Heritage & Temples", value: "heritage-temples" },
  { label: "🛕 Religious Sites", value: "religious-sites" },
  { label: "📸 Photography Spots", value: "photography-spots" },
  { label: "⭐ Attractions", value: "attraction" },
  { label: "🖼️ Viewpoints", value: "viewpoint" },
  { label: "🏛️ Museums", value: "museum" },
]

export default function DestinationList() {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const initialQuery = searchParams.get("q") || ""

  const [destinations, setDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState("")
  const [type, setType] = useState("attraction") // default: real attractions, not hotels
  const [query, setQuery] = useState(initialQuery)
  const [favoriteMap, setFavoriteMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [researching, setResearching] = useState(false)

  const { position } = useGeolocation()

  useEffect(() => {
    setLoading(true)

    const params = {
      page,
      limit: 12,
      type,
    }

    if (category) params.category = category
    if (query) {
      params.search = query
      params.q = query
    }
    if (position) {
      params.latitude = position.lat
      params.longitude = position.lng
    }

    destinationApi
      .getAll(params)
      .then(({ data }) => {
        const results = data.results || data || []
        setDestinations(results)
        setTotalPages(
          data.total_pages ||
          data.totalPages ||
          Math.ceil((data.count || results.length) / 12) ||
          1
        )
      })
      .catch(() => {
        setDestinations([])
        setTotalPages(1)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [page, category, type, query, position])

  useEffect(() => {
    if (!isAuthenticated) {
      setFavoriteMap({})
      return
    }
    userApi
      .getFavorites()
      .then(({ data }) => {
        const list = data.results || data || []
        const map = {}
        list.forEach((fav) => {
          map[fav.destination] = fav.id
        })
        setFavoriteMap(map)
      })
      .catch(() => {})
  }, [isAuthenticated])

  const handleToggleFavorite = async (destId) => {
    if (!isAuthenticated) {
      return showToast("Please login to save favorites", "info")
    }

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
  }

  // Trigger Research when searching uncataloged place
  const handleResearchQuery = async () => {
    if (!query) return
    setResearching(true)
    try {
      const { data } = await destinationApi.researchDestination(query)
      if (data.slug) {
        showToast(`Researched & verified "${data.name}"! Opening details...`, "success")
        navigate(`/destinations/${data.slug}`)
      } else {
        showToast(data.message || "Destination researched!", "info")
      }
    } catch (err) {
      showToast("Research service error. Try another place name.", "error")
    } finally {
      setResearching(false)
    }
  }

  // Nepal-themed palette: deep green / terracotta / gold
  const chipActive = "bg-[#1f6b4d] text-white shadow-md"
  const chipIdle = "bg-white text-[#1f6b4d] border border-[#1f6b4d]/30 hover:bg-[#1f6b4d]/5"

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[{ label: "Destinations Explorer", to: "/destinations" }]} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1f6b4d]/20 pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-[#c2603a]/10 text-[#c2603a] text-xs font-black uppercase tracking-wider">
            Himalayan Atlas
          </span>
          <h1 className="text-3xl md:text-4xl font-extrabold text-[#1f3329] mt-1 flex items-center gap-2"
              style={{ fontFamily: 'ui-serif, Georgia, "Noto Serif Devanagari", serif' }}>
            <FiMapPin className="text-[#c2603a]" /> Explore Nepal
          </h1>
          <p className="text-gray-600 text-sm mt-1 max-w-xl">
            Discover real temples, stupas, caves, lakes, Himalayan viewpoints and heritage
            sites across Nepal — no hotels or lodges cluttering the map.
          </p>
        </div>

        <Link
          to="/destinations/submit"
          className="px-5 py-2.5 rounded-xl bg-[#1f6b4d] hover:bg-[#174f38] text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-[#1f6b4d]/20 transition-all shrink-0"
        >
          <FiPlus size={16} /> Submit a Place
        </Link>
      </div>

      {/* Type chips (Attractions / Hotels / All) */}
      <div className="flex flex-wrap gap-2">
        {TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => { setType(opt.value); setPage(1) }}
            className={`px-4 py-2 rounded-full text-sm font-bold transition-all ${type === opt.value ? chipActive : chipIdle}`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchBar
          className="flex-1"
          defaultValue={initialQuery}
          placeholder="Search by name, city, temple, trek (e.g. Mahendra Cave, Phewa, Everest)..."
          onSearch={(val) => {
            setQuery(val)
            setPage(1)
          }}
        />

        <Filter
          options={CATEGORY_OPTIONS}
          value={category}
          onChange={(val) => {
            setCategory(val)
            setPage(1)
          }}
          placeholder="All Categories"
        />
      </div>

      {/* Grid or Skeleton or Research Prompt */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <DestinationCardSkeleton key={i} />
          ))}
        </div>
      ) : destinations.length > 0 ? (
        <div className="space-y-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard
                key={d.id}
                destination={d}
                isFavorite={!!favoriteMap[d.id]}
                onToggleFavorite={() => handleToggleFavorite(d.id)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center pt-4">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={(p) => setPage(p)}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="card-base p-8 sm:p-12 text-center max-w-xl mx-auto space-y-5 border border-[#1f6b4d]/30 bg-gradient-to-br from-white to-[#faf8f4] rounded-3xl shadow-2xl">
          <div className="w-16 h-16 rounded-full bg-[#c2603a]/10 text-[#c2603a] mx-auto flex items-center justify-center font-black text-2xl shadow-sm">
            ✨
          </div>

          <div className="space-y-2">
            <h3 className="font-extrabold text-2xl text-[#1f3329]">
              Destination Not Found
            </h3>
            <p className="text-sm text-gray-600 max-w-md mx-auto leading-relaxed">
              No matching attractions yet. Would you like the AI Discovery Sentinel to
              research and assemble a verified record for{" "}
              <b>"{query || "this destination"}"</b>?
            </p>
          </div>

          <button
            onClick={handleResearchQuery}
            disabled={researching || !query}
            className="px-8 py-3.5 bg-[#1f6b4d] hover:bg-[#174f38] text-white font-black text-sm rounded-2xl shadow-xl hover:scale-105 transition-all disabled:opacity-50"
          >
            {researching ? "Researching..." : `Research "${query || "Place"}" ➔`}
          </button>
        </div>
      )}
    </div>
  )
}
