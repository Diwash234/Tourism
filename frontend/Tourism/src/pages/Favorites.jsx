import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FiHeart, FiLogIn, FiCompass } from "react-icons/fi"
import { Link } from "react-router-dom"
import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import DestinationCard from "../components/cards/DestinationCard"

const Favorites = () => {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const { showToast } = useToast()

  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  const loadFavorites = async () => {
    setLoading(true)
    try {
      const { data } = await userApi.getFavorites()
      const list = data?.results || (Array.isArray(data) ? data : [])
      setFavorites(list)
    } catch (err) {
      console.error("Failed to load favorites:", err)
      setFavorites([])
      if (err.response?.status === 401) {
        showToast("Please log in to view your saved favourites", "info")
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!authLoading) {
      if (isAuthenticated) {
        loadFavorites()
      } else {
        setLoading(false)
      }
    }
  }, [isAuthenticated, authLoading])

  const handleRemove = async (favId) => {
    try {
      await userApi.removeFavorite(favId)
      setFavorites((prev) => prev.filter((fav) => fav.id !== favId))
      showToast("Removed from favourites", "info")
    } catch (err) {
      showToast("Could not remove favourite", "error")
    }
  }

  if (authLoading || loading) return <Loader />

  if (!isAuthenticated) {
    return (
      <div className="container-app py-12 text-center max-w-md mx-auto space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto text-2xl">
          <FiHeart />
        </div>
        <h2 className="text-2xl font-black text-gray-900">Saved Favourites</h2>
        <p className="text-sm text-gray-500">
          Log in to your account to view and manage your saved destinations and trails across Nepal.
        </p>
        <div className="pt-2">
          <Link
            to="/login?redirect=/favorites"
            className="px-6 py-3 rounded-2xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-sm inline-flex items-center gap-2 shadow-lg shadow-purple-700/20 transition-all"
          >
            <FiLogIn size={16} /> Log In to View Favourites
          </Link>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="container-app py-8 space-y-6"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-gray-900 flex items-center gap-2">
            <FiHeart className="text-rose-500 fill-rose-500" />
            My Saved Favourites
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            {favorites.length} {favorites.length === 1 ? "destination" : "destinations"} saved to your personal Nepal collection.
          </p>
        </div>

        <Link
          to="/destinations"
          className="px-4 py-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-900 font-bold text-xs inline-flex items-center gap-1.5 border border-purple-200 transition-all self-start sm:self-auto"
        >
          <FiCompass size={14} /> Explore More Places
        </Link>
      </div>

      {favorites.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {favorites.map((fav) => {
            const dest = fav.destination_detail || fav.destination || {}
            return (
              <DestinationCard
                key={fav.id}
                destination={typeof dest === "object" ? dest : { id: dest }}
                isFavorite={true}
                onToggleFavorite={() => handleRemove(fav.id)}
              />
            )
          })}
        </div>
      ) : (
        <EmptyState
          title="No favourites saved yet"
          subtitle="Click the heart icon on any destination or trekking trail to save it here for quick access."
          action={
            <Link
              to="/destinations"
              className="px-5 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow"
            >
              <FiCompass size={14} /> Discover Destinations ➔
            </Link>
          }
        />
      )}
    </motion.div>
  )
}

export default Favorites
