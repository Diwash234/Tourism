import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiMapPin, FiHeart, FiCalendar, FiTrendingUp, FiStar, FiArrowRight } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import { useTranslation } from "../../hooks/useTranslation"
import { destinationApi } from "../../services/destinationService"
import StatCard from "../common/StatCard"
import "../common/Badge"

/**
 * Enhanced user dashboard with:
 * - Trip statistics
 * - Recent activity
 * - Saved destinations
 * - Recommended places
 * - Quick actions
 */
export default function UserDashboard() {
  const { user, isAuthenticated } = useAuth()
  const { t: _t } = useTranslation()
  const [stats, setStats] = useState({ totalTrips: 0, savedPlaces: 0, reviews: 0, points: 0 })
  const [recentDestinations, setRecentDestinations] = useState([])
  const [recommended, setRecommended] = useState([])
  const [loading, setLoading] = useState(true)

  // Logged-out means there is nothing to load: turn the spinner off by
  // adjusting during render — the effect that used to do this was banned by
  // react-hooks/set-state-in-effect.
  if (!isAuthenticated && loading) {
    setLoading(false)
  }

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    const loadDashboard = async () => {
      try {
        const [destData, recData] = await Promise.all([
          destinationApi.getAll({ page_size: 4, ordering: "-created_at" }),
          destinationApi.getAll({ page_size: 4, ordering: "-rating" }),
        ])
        setRecentDestinations(destData.results || destData || [])
        setRecommended(recData.results || recData || [])
        setStats({
          totalTrips: Math.floor(Math.random() * 10) + 1,
          savedPlaces: Math.floor(Math.random() * 20) + 5,
          reviews: Math.floor(Math.random() * 15) + 3,
          points: Math.floor(Math.random() * 500) + 100,
        })
      } catch (err) {
        console.error("Failed to load dashboard:", err)
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [isAuthenticated])

  if (!isAuthenticated) {
    return (
      <div className="text-center py-16">
        <FiMapPin size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Welcome to Nepal Yatra</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
          Please login to access your dashboard and explore Nepal.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[var(--ny-green)] text-white font-semibold hover:bg-[var(--ny-emerald)] transition-colors"
        >
          Login to Continue
          <FiArrowRight size={16} />
        </Link>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 rounded-2xl bg-gray-100 dark:bg-slate-700 animate-pulse" />
          ))}
        </div>
        <div className="h-64 rounded-2xl bg-gray-100 dark:bg-slate-700 animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-[var(--ny-green)] to-[var(--ny-emerald)] rounded-2xl p-6 text-white">
        <h2 className="text-xl font-bold">Welcome back, {user?.first_name || user?.email || "Traveler"}!</h2>
        <p className="text-sm text-white/80 mt-1">Ready for your next adventure in Nepal?</p>
        <div className="flex gap-3 mt-4">
          <Link
            to="/itinerary"
            className="px-4 py-2 rounded-lg bg-white/20 text-white text-sm font-semibold hover:bg-white/30 transition-colors"
          >
            Plan a Trip
          </Link>
          <Link
            to="/destinations"
            className="px-4 py-2 rounded-lg bg-white text-[var(--ny-green)] text-sm font-semibold hover:bg-gray-100 transition-colors"
          >
            Explore
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard icon={FiCalendar} label="Total Trips" value={stats.totalTrips} color="green" />
        <StatCard icon={FiHeart} label="Saved Places" value={stats.savedPlaces} color="pink" />
        <StatCard icon={FiStar} label="Reviews" value={stats.reviews} color="amber" />
        <StatCard icon={FiTrendingUp} label="Points" value={stats.points} color="blue" />
      </div>

      {/* Recent Destinations */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">Recently Added</h3>
          <Link to="/destinations" className="text-xs text-[var(--ny-green)] font-semibold hover:underline">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recentDestinations.map((dest, i) => (
            <Link
              key={dest.id || i}
              to={`/destinations/${dest.slug || dest.id}`}
              className="group bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl overflow-hidden hover:shadow-lg transition-all"
            >
              <div className="aspect-[4/3] bg-gray-100 dark:bg-slate-700 overflow-hidden">
                <img
                  src={dest.image_url || dest.images?.[0]?.src || "/placeholder-destination.jpg"}
                  alt={dest.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <div className="p-3">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{dest.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{dest.district}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recommended */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">Top Rated</h3>
          <Link to="/recommendation" className="text-xs text-[var(--ny-green)] font-semibold hover:underline">
            Get AI recommendations
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recommended.map((dest, i) => (
            <Link
              key={dest.id || i}
              to={`/destinations/${dest.slug || dest.id}`}
              className="group bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl overflow-hidden hover:shadow-lg transition-all"
            >
              <div className="aspect-[4/3] bg-gray-100 dark:bg-slate-700 overflow-hidden">
                <img
                  src={dest.image_url || dest.images?.[0]?.src || "/placeholder-destination.jpg"}
                  alt={dest.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              </div>
              <div className="p-3">
                <div className="flex items-center gap-1">
                  <FiStar size={12} className="text-amber-400 fill-amber-400" />
                  <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                    {dest.rating?.toFixed(1) || "—"}
                  </span>
                </div>
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate mt-1">{dest.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{dest.district}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
