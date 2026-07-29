import { useEffect, useState } from "react"
import { useSearchParams } from "react-router-dom"
import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"
import DestinationCard from "../../components/cards/DestinationCard"
import SearchBar from "../../components/common/SearchBar"
import useGeolocation from "../../hooks/useGeolocation"
import Filter from "../../components/common/Filter"
import Pagination from "../../components/common/Pagination"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

const CATEGORY_OPTIONS = [
  { label: "Mountains", value: "mountains" },
  { label: "Lakes", value: "lakes" },
  { label: "Heritage", value: "heritage" },
  { label: "Adventure", value: "adventure" },
]

const PAGE_SIZE = 9

const Destinationlist = () => {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [searchParams] = useSearchParams()
  // NEW: without this, a link like /destinations?q=Pokhara (e.g. from the
  // dashboard's hero "AI Search") landed on an unfiltered destination
  // list — the search term was in the URL but nothing ever read it.
  const initialQuery = searchParams.get("q") || ""
  const [destinations, setDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState("")
  const [query, setQuery] = useState(initialQuery)
  const [favoriteMap, setFavoriteMap] = useState({}) // { [destinationId]: favoriteRecordId }
  const favoriteIds = Object.keys(favoriteMap).map(Number)
  const [loading, setLoading] = useState(true)
  const { position } = useGeolocation()

  useEffect(() => {
    setLoading(true)
    const params = { page, limit: PAGE_SIZE }
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
        setDestinations(data.results || data || [])
        setTotalPages(data.total_pages || data.totalPages || 1)
      })
      .catch(() => setDestinations([]))
      .finally(() => setLoading(false))
  }, [page, category, query, position])

  // NEW: favoriteIds was declared but never populated — every card's
  // heart icon always showed as "not favorited" regardless of actual
  // saved state. Fetch once on mount (and again after login state
  // changes) so it reflects reality.
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
        list.forEach((f) => { map[f.destination] = f.id })
        setFavoriteMap(map)
      })
      .catch(() => setFavoriteMap({}))
  }, [isAuthenticated])

  const handleToggleFavorite = async (id) => {
    if (!isAuthenticated) {
      showToast("Please login to save favorites", "info")
      return
    }
    try {
      if (favoriteMap[id]) {
        // FIXED: removeFavorite needs the favorite RECORD's id, not the
        // destination's id — passing the destination id here 404'd
        // silently against the real backend.
        await userApi.removeFavorite(favoriteMap[id])
        setFavoriteMap((prev) => {
          const next = { ...prev }
          delete next[id]
          return next
        })
      } else {
        const { data } = await userApi.addFavorite(id)
        setFavoriteMap((prev) => ({ ...prev, [id]: data.id }))
      }
    } catch {
      showToast("Could not update favorites", "error")
    }
  }

  return (
    <div className="container-app py-10 fade-in">
      <h1 className="section-title">Explore Destinations</h1>

      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <SearchBar
          className="flex-1"
          defaultValue={initialQuery}
          onSearch={(q) => { setQuery(q); setPage(1) }}
        />
        <Filter
          label=""
          options={CATEGORY_OPTIONS}
          value={category}
          onChange={(v) => { setCategory(v); setPage(1) }}
        />
      </div>

      {loading ? (
        <Loader />
      ) : destinations.length ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard
                key={d.id}
                destination={d}
                isFavorite={favoriteIds.includes(d.id)}
                onToggleFavorite={handleToggleFavorite}
              />
            ))}
          </div>
          <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState title="No destinations found" subtitle="Try adjusting your search or filters." />
      )}
    </div>
  )
}

export default Destinationlist