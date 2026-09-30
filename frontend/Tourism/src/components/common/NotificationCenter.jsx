import { useState, useEffect } from "react"
import { FiBell, FiX, FiCheck, FiAlertTriangle, FiInfo, FiTrash2 } from "react-icons/fi"

const NOTIFICATION_TYPES = {
  alert: { icon: FiAlertTriangle, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30" },
  success: { icon: FiCheck, color: "text-emerald-500", bg: "bg-emerald-50 dark:bg-emerald-950/30" },
  info: { icon: FiInfo, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-950/30" },
}

/**
 * Full notification center with:
 * - Unread count badge
 * - Mark as read / mark all as read
 * - Delete individual / clear all
 * - Filter by type
 * - localStorage persistence
 */
export default function NotificationCenter() {
  const [notifications, setNotifications] = useState(() => {
    try {
      const stored = localStorage.getItem("ny-notifications")
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    localStorage.setItem("ny-notifications", JSON.stringify(notifications))
  }, [notifications])

  const unreadCount = notifications.filter(n => !n.read).length

  const markAsRead = (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const clearAll = () => {
    setNotifications([])
  }

  const filtered = notifications.filter(n => {
    if (filter === "all") return true
    if (filter === "unread") return !n.read
    return n.type === filter
  })

  const formatTime = (isoString) => {
    const date = new Date(isoString)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return "Just now"
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="relative">
      {/* Bell Button */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="relative p-2 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        aria-expanded={open}
      >
        <FiBell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white animate-pulse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 max-h-[70vh] flex flex-col rounded-2xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllAsRead}
                  className="text-xs text-[var(--ny-green)] font-semibold hover:underline"
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  type="button"
                  onClick={clearAll}
                  className="p-1 rounded text-gray-400 hover:text-red-500"
                  aria-label="Clear all notifications"
                >
                  <FiTrash2 size={14} />
                </button>
              )}
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-1 px-4 py-2 border-b border-gray-100 dark:border-slate-700 overflow-x-auto">
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
                className={`px-2.5 py-1 text-[10px] font-semibold rounded-full whitespace-nowrap transition-colors ${
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
          <div className="flex-1 overflow-y-auto">
            {filtered.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <FiBell size={32} className="mx-auto text-gray-300 dark:text-gray-600 mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">No notifications</p>
              </div>
            ) : (
              filtered.map(notification => {
                const config = NOTIFICATION_TYPES[notification.type] || NOTIFICATION_TYPES.info
                const Icon = config.icon
                return (
                  <div
                    key={notification.id}
                    className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50 dark:border-slate-700/50 last:border-0 transition-colors ${
                      !notification.read ? "bg-[var(--ny-soft-green)]" : ""
                    }`}
                  >
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg shrink-0 ${config.bg}`}>
                      <Icon size={14} className={config.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{notification.title}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{notification.message}</p>
                      <p className="text-[10px] text-gray-400 mt-1">{formatTime(notification.timestamp)}</p>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {!notification.read && (
                        <button
                          type="button"
                          onClick={() => markAsRead(notification.id)}
                          className="p-1 rounded text-gray-400 hover:text-[var(--ny-green)]"
                          aria-label="Mark as read"
                        >
                          <FiCheck size={12} />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => removeNotification(notification.id)}
                        className="p-1 rounded text-gray-400 hover:text-red-500"
                        aria-label="Remove notification"
                      >
                        <FiX size={12} />
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
