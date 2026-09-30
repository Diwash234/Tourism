import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiBell, FiX, FiCheck, FiAlertTriangle, FiInfo, FiTrash2 } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"

/**
 * Full notification center page component.
 * Shows all notifications with filtering, marking as read, and deletion.
 */
export default function NotificationCenter() {
  const { t } = useTranslation()
  const [notifications, setNotifications] = useState([])
  const [filter, setFilter] = useState("all")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load from localStorage or API
    const stored = localStorage.getItem("ny-notifications")
    if (stored) {
      setNotifications(JSON.parse(stored))
    } else {
      // Default sample notifications
      setNotifications([
        { id: 1, type: "alert", title: "Weather Alert", message: "Heavy rainfall expected in Pokhara region", time: "2h ago", read: false },
        { id: 2, type: "info", title: "New Destination", message: "Mustang Valley has been added to explore", time: "5h ago", read: false },
        { id: 3, type: "success", title: "Trip Planned", message: "Your itinerary for Kathmandu is ready", time: "1d ago", read: true },
      ])
    }
    setLoading(false)
  }, [])

  const saveNotifications = (updated) => {
    setNotifications(updated)
    localStorage.setItem("ny-notifications", JSON.stringify(updated))
  }

  const markAsRead = (id) => {
    saveNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n))
  }

  const markAllAsRead = () => {
    saveNotifications(notifications.map(n => ({ ...n, read: true })))
  }

  const removeNotification = (id) => {
    saveNotifications(notifications.filter(n => n.id !== id))
  }

  const clearAll = () => {
    saveNotifications([])
  }

  const filtered = notifications.filter(n => {
    if (filter === "all") return true
    if (filter === "unread") return !n.read
    return n.type === filter
  })

  const unreadCount = notifications.filter(n => !n.read).length

  const getIcon = (type) => {
    switch (type) {
      case "alert": return <FiAlertTriangle size={16} className="text-amber-500" />
      case "success": return <FiCheck size={16} className="text-emerald-500" />
      case "info": return <FiInfo size={16} className="text-blue-500" />
      default: return <FiBell size={16} className="text-gray-400" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FiBell size={20} className="text-[var(--ny-green)]" />
            Notifications
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? "s" : ""}` : "All caught up!"}
          </p>
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={markAllAsRead}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-[var(--ny-soft-green)] text-[var(--ny-green)] hover:bg-emerald-100 transition-colors"
            >
              <FiCheck size={14} />
              Mark all read
            </button>
          )}
          {notifications.length > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
            >
              <FiTrash2 size={14} />
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {[
          { key: "all", label: "All" },
          { key: "unread", label: "Unread" },
          { key: "alert", label: "Alerts" },
          { key: "info", label: "Info" },
          { key: "success", label: "Success" },
        ].map(tab => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setFilter(tab.key)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap transition-colors ${
              filter === tab.key
                ? "bg-[var(--ny-green)] text-white"
                : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notification List */}
      {filtered.length === 0 ? (
        <div className="text-center py-12">
          <FiBell size={40} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">No notifications to display</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(notification => (
            <div
              key={notification.id}
              className={`flex items-start gap-3 p-4 rounded-xl border transition-all ${
                !notification.read
                  ? "bg-[var(--ny-soft-green)] border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-900"
                  : "bg-white dark:bg-slate-800 border-[var(--ny-border)]"
              }`}
            >
              <div className="mt-0.5 shrink-0">{getIcon(notification.type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">{notification.title}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{notification.message}</p>
                <p className="text-[10px] text-gray-400 mt-1">{notification.time}</p>
              </div>
              <div className="flex gap-1 shrink-0">
                {!notification.read && (
                  <button
                    type="button"
                    onClick={() => markAsRead(notification.id)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] transition-colors"
                    aria-label="Mark as read"
                  >
                    <FiCheck size={14} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => removeNotification(notification.id)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                  aria-label="Remove notification"
                >
                  <FiX size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
