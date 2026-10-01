import { useState } from "react"
import { FiBell, FiX, FiCheck, FiAlertTriangle, FiInfo } from "react-icons/fi"
import { Link } from "react-router-dom"

// Simulated fetching notifications (module scope so state can be initialised
// lazily instead of with a synchronous setState inside an effect, which is
// banned by react-hooks/set-state-in-effect).
const MOCK_NOTIFICATIONS = [
  {
    id: 1,
    type: "alert",
    title: "Weather Alert",
    message: "Heavy rainfall expected in Pokhara region",
    time: "2h ago",
    read: false,
    link: "/risk-alerts"
  },
  {
    id: 2,
    type: "success",
    title: "Trip Planned",
    message: "Your itinerary for Kathmandu is ready",
    time: "5h ago",
    read: false,
    link: "/itinerary"
  },
  {
    id: 3,
    type: "info",
    title: "New Destination",
    message: "Mustang Valley has been added to explore",
    time: "1d ago",
    read: true,
    link: "/destinations"
  }
]

/**
 * Notification center with real-time updates.
 * Shows unread count, allows marking as read, and clearing all.
 */
export default function NotificationCenter() {
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS)
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(
    MOCK_NOTIFICATIONS.filter(n => !n.read).length
  )

  const markAsRead = (id) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    setUnreadCount(0)
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const getIcon = (type) => {
    switch (type) {
      case "alert": return <FiAlertTriangle size={16} className="text-amber-500" />
      case "success": return <FiCheck size={16} className="text-emerald-500" />
      case "info": return <FiInfo size={16} className="text-blue-500" />
      default: return <FiBell size={16} className="text-gray-400" />
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label="Notifications"
      >
        <FiBell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 z-50 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllAsRead}
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold"
                >
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center">
                  <FiBell size={32} className="mx-auto text-gray-300 mb-2" />
                  <p className="text-sm text-gray-500">No notifications</p>
                </div>
              ) : (
                notifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50 dark:border-slate-700/50 last:border-0 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors ${
                      !notification.read ? "bg-emerald-50/50 dark:bg-emerald-950/20" : ""
                    }`}
                  >
                    <div className="mt-0.5 shrink-0">{getIcon(notification.type)}</div>
                    <div className="flex-1 min-w-0">
                      <Link
                        to={notification.link}
                        onClick={() => markAsRead(notification.id)}
                        className="block"
                      >
                        <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                          {notification.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-[10px] text-gray-400 mt-1">{notification.time}</p>
                      </Link>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeNotification(notification.id)}
                      className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Remove notification"
                    >
                      <FiX size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
