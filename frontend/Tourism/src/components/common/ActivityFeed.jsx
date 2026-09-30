import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiUser, FiMapPin, FiStar, FiHeart, FiMessageCircle, FiCalendar } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"

const ACTIVITY_TYPES = {
  review: { icon: FiStar, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30" },
  favorite: { icon: FiHeart, color: "text-red-500", bg: "bg-red-50 dark:bg-red-950/30" },
  visit: { icon: FiMapPin, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30" },
  comment: { icon: FiMessageCircle, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-950/30" },
  booking: { icon: FiCalendar, color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-950/30" },
  signup: { icon: FiUser, color: "text-gray-500", bg: "bg-gray-50 dark:bg-gray-800" },
}

/**
 * Real-time activity feed showing recent user actions across the platform.
 * Simulates live updates with periodic refresh.
 */
export default function ActivityFeed({ limit = 10, className = "" }) {
  const { t } = useTranslation()
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate fetching activities
    const sampleActivities = [
      { id: 1, type: "review", user: "Sita Sharma", action: "reviewed", target: "Pokhara", rating: 5, time: "2m ago" },
      { id: 2, type: "favorite", user: "Ram Thapa", action: "saved", target: "Annapurna Base Camp", time: "5m ago" },
      { id: 3, type: "visit", user: "Maya Gurung", action: "visited", target: "Lumbini", time: "12m ago" },
      { id: 4, type: "booking", user: "Hari Prasad", action: "booked", target: "Hotel Yak & Yeti", time: "18m ago" },
      { id: 5, type: "comment", user: "Gita Rai", action: "commented on", target: "Everest Base Camp", time: "25m ago" },
      { id: 6, type: "review", user: "Bikash Tamang", action: "reviewed", target: "Chitwan National Park", rating: 4, time: "32m ago" },
      { id: 7, type: "signup", user: "Anita Magar", action: "joined as", target: "Local Guide", time: "45m ago" },
      { id: 8, type: "visit", user: "Suresh Limbu", action: "visited", target: "Kathmandu Durbar Square", time: "1h ago" },
    ]
    
    const timer = setTimeout(() => {
      setActivities(sampleActivities.slice(0, limit))
      setLoading(false)
    }, 500)
    return () => clearTimeout(timer)
  }, [limit])

  if (loading) {
    return (
      <div className={`space-y-3 ${className}`}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 animate-pulse">
            <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-slate-600" />
            <div className="flex-1 space-y-2">
              <div className="h-3 bg-gray-200 dark:bg-slate-600 rounded w-3/4" />
              <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Recent Activity</h3>
        <span className="text-[10px] text-gray-400 uppercase tracking-wider">Live</span>
      </div>
      {activities.map(activity => {
        const config = ACTIVITY_TYPES[activity.type] || ACTIVITY_TYPES.signup
        const Icon = config.icon
        return (
          <div key={activity.id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${config.bg}`}>
              <Icon size={16} className={config.color} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-700 dark:text-gray-300">
                <span className="font-semibold">{activity.user}</span>{" "}
                {activity.action}{" "}
                <Link to={`/destinations/${activity.target?.toLowerCase().replace(/\s+/g, '-')}`} className="font-semibold text-[var(--ny-green)] hover:underline">
                  {activity.target}
                </Link>
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-gray-400">{activity.time}</span>
                {activity.rating && (
                  <div className="flex items-center gap-0.5">
                    {Array.from({ length: activity.rating }).map((_, i) => (
                      <span key={i} className="text-amber-400 text-[10px]">★</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
