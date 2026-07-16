import { useEffect, useState } from "react"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import DestinationCard from "../components/cards/DestinationCard"
import useToast from "../hooks/useToast"

const Favorites = () => {
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    userApi
      .getFavorites()
      .then(({ data }) => setFavorites(data.items || data || []))
      .catch(() => setFavorites([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleRemove = async (id) => {
    try {
      await userApi.removeFavorite(id)
      setFavorites((prev) => prev.filter((d) => d.id !== id))
      showToast("Removed from favorites", "info")
    } catch {
      showToast("Could not remove favorite", "error")
    }
  }

  if (loading) return <Loader />

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Favorite Places</h1>
      {favorites.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {favorites.map((d) => (
            <DestinationCard key={d.id} destination={d} isFavorite onToggleFavorite={handleRemove} />
          ))}
        </div>
      ) : (
        <EmptyState title="No favorites yet" subtitle="Save destinations you love to find them here." />
      )}
    </div>
  )
}

export default Favorites