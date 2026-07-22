import { useEffect, useState } from "react"
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
  const [destinations, setDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState("")
  const [query, setQuery] = useState("")
  const [favoriteIds, setFavoriteIds] = useState([])
  const [loading, setLoading] = useState(true)
  const { position } = useGeolocation()

  useEffect(() => {
    setLoading(true)
    const params = { page, limit: PAGE_SIZE }
    if (category) params.category = category
    if (query) params.q = query
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
    } catch {
      showToast("Could not update favorites", "error")
    }
  }

  return (
    <div className="container-app py-10">
      <h1 className="section-title">Explore Destinations</h1>

      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <SearchBar className="flex-1" onSearch={(q) => { setQuery(q); setPage(1) }} />
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