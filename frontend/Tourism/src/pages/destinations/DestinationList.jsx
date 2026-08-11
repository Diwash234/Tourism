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

const CATEGORY_OPTIONS = [
  { label: "All Categories", value: "" },
  { label: "🏔️ Mountains & Trekking", value: "mountains" },
  { label: "🌊 Lakes & Water", value: "lakes" },
  { label: "🐅 Forest & Wildlife", value: "wildlife" },
  { label: "🏛️ Heritage & Temples", value: "heritage" },
  { label: "🪂 Adventure Sports", value: "adventure" },
  { label: "📸 Photography Spots", value: "photography" },
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
  }, [page, category, query, position])

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

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[{ label: "Destinations Explorer", to: "/destinations" }]} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
            Himalayan Atlas
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
            <FiMapPin className="text-purple-700" /> Explore Nepal Destinations
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Over 5,800+ verified mountain passes, cultural heritage temples, serene lakes, and hidden valleys.
          </p>
        </div>

        <Link
          to="/destinations/submit"
          className="px-5 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-900/20 transition-all shrink-0"
        >
          <FiPlus size={16} /> Submit a Place
        </Link>
      </div>

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchBar
          className="flex-1"
          defaultValue={initialQuery}
          placeholder="Search by name, city, temple, trek (e.g. Swargadwari, Waling, Pokhara, Everest)..."
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
        /* Research & Discovery Card when no local match exists */
        <div className="card-base p-8 sm:p-12 text-center max-w-xl mx-auto space-y-5 border border-purple-200 bg-gradient-to-br from-white to-purple-50/70 rounded-3xl shadow-2xl">
          <div className="w-16 h-16 rounded-full bg-purple-100 text-purple-700 mx-auto flex items-center justify-center font-black text-2xl shadow-sm">
            ✨
          </div>

          <div className="space-y-2">
            <h3 className="font-extrabold text-2xl text-gray-900">
              Destination Not Found in Local Index
            </h3>
            <p className="text-xs sm:text-sm text-gray-600 max-w-md mx-auto leading-relaxed">
              Would you like the <b>AI Destination Discovery Sentinel</b> to research and assemble a verified record for <b>"{query || "this destination"}"</b> from Nepal Tourism Board, municipal archives, and Wikimedia?
            </p>
          </div>

          <button
            onClick={handleResearchQuery}
            disabled={researching || !query}
            className="btn-primary px-8 py-3.5 bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 text-white font-black text-xs sm:text-sm rounded-2xl shadow-xl hover:scale-105 transition-all disabled:opacity-50"
          >
            {researching ? "Researching & Collecting Verified Data..." : `Research & Discover "${query || "Place"}" with AI ➔`}
          </button>
        </div>
      )}
    </div>
  )
}
