import { useEffect, useState } from "react"
import { FiMapPin, FiCompass } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"
import DestinationCard from "../../components/cards/DestinationCard"
import SearchBar from "../../components/common/SearchBar"
import Filter from "../../components/common/Filter"
import Pagination from "../../components/common/Pagination"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import PageHeader from "../../components/common/PageHeader"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import { searchDestinations } from "../../data/nepalDestinations"

const CATEGORY_OPTIONS = [
  { label: "Mountains", value: "mountains" },
  { label: "Lakes", value: "lakes" },
  { label: "Heritage", value: "heritage" },
  { label: "Adventure", value: "adventure" },
]

const TABS = [
  { key: "all", label: "All Destinations" },
  { key: "favorites", label: "Favorite Places" },
  { key: "popular", label: "Most Visited" },
]

const PAGE_SIZE = 9

const DestinationList = () => {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [tab, setTab] = useState("all")
  const [destinations, setDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState("")
  const [query, setQuery] = useState("")
  const [heroMatch, setHeroMatch] = useState(null)
  const [favoriteIds, setFavoriteIds] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)

    if (tab === "favorites") {
      if (!isAuthenticated) {
        showToast("Please login to see your favorite places", "info")
        setDestinations([])
        setLoading(false)
        return
      }
      userApi
        .getFavorites()
        .then(({ data }) => setDestinations(data.items || data || []))
        .catch(() => setDestinations([]))
        .finally(() => setLoading(false))
      return
    }

    const params =
      tab === "popular"
        ? { page, limit: PAGE_SIZE, sort: "popular", q: query }
        : { page, limit: PAGE_SIZE, category, q: query }

    destinationApi
      .getAll(params)
      .then(({ data }) => {
        const items = data.items || data || []
        if (items.length) {
          setDestinations(items)
          setTotalPages(data.totalPages || 1)
          setHeroMatch(query && items.length ? items[0] : null)
        } else {
          throw new Error("empty")
        }
      })
      .catch(() => {
        const fallback = searchDestinations(query, category)
        setDestinations(fallback)
        setTotalPages(1)
        setHeroMatch(query && fallback.length ? fallback[0] : null)
      })
      .finally(() => setLoading(false))
  }, [page, category, query, tab, isAuthenticated])

  const handleToggleFavorite = async (id) => {
    if (!isAuthenticated) {
      showToast("Please login to save favorites", "info")
      return
    }
    try {
      if (favoriteIds.includes(id)) {
        await userApi.removeFavorite(id)
        setFavoriteIds((prev) => prev.filter((f) => f !== id))
      } else {
        await userApi.addFavorite(id)
        setFavoriteIds((prev) => [...prev, id])
      }
      if (tab === "favorites") {
        setDestinations((prev) => prev.filter((d) => d.id !== id || favoriteIds.includes(id)))
      }
    } catch {
      showToast("Could not update favorites", "error")
    }
  }

  return (
    <div className="container-app py-10">
      <PageHeader
        title="Explore Destinations"
        subtitle="Search by name or region — photos, ratings, and heritage tags update as you browse."
        icon={FiCompass}
        theme="rose"
      />

      <div className="flex gap-2 mb-6 border-b border-gray-100">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setPage(1) }}
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
              tab === t.key
                ? "border-rose-500 text-rose-600"
                : "border-transparent text-gray-400 hover:text-gray-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab !== "favorites" && (
        <div className="flex flex-col sm:flex-row gap-4 mb-4 items-stretch sm:items-center">
          <SearchBar className="flex-1" onSearch={(q) => { setQuery(q); setPage(1) }} />
          <Filter
            label=""
            options={CATEGORY_OPTIONS}
            value={category}
            onChange={(v) => { setCategory(v); setPage(1) }}
          />
        </div>
      )}

      {heroMatch && tab !== "favorites" && (
        <div className="relative rounded-xl2 overflow-hidden h-40 mb-8">
          <img
            src={heroMatch.image || "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900"}
            alt={heroMatch.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-4">
            <p className="text-white font-semibold flex items-center gap-1">
              <FiMapPin size={14} /> Showing results near {heroMatch.location || heroMatch.name}
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <Loader />
      ) : destinations.length ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard
                key={d.id}
                destination={d}
                isFavorite={tab === "favorites" ? true : favoriteIds.includes(d.id)}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </div>
          {tab !== "favorites" && (
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          )}
        </>
      ) : (
        <EmptyState
          title={tab === "favorites" ? "No favorites yet" : "No destinations found"}
          subtitle={
            tab === "favorites"
              ? "Tap the heart icon on any destination to save it here."
              : "Try adjusting your search or filters."
          }
        />
      )}
    </div>
  )
}

export default DestinationList