import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { FiBell, FiCheck, FiX, FiAlertTriangle, FiInfo } from "react-icons/fi"

/**
 * Notification dropdown for the navbar. Shows recent notifications with
 * unread indicator, mark-as-read, and clear-all functionality.
 */
export default function NotificationDropdown() {
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState([
    { id: 1, type: "alert", title: "Weather Alert", message: "Heavy rainfall expected in Pokhara region", time: "2h ago", read: false },
    { id: 2, type: "info", title: "New Destination", message: "Mustang Valley has been added to explore", time: "5h ago", read: false },
    { id: 3, type: "success", title: "Trip Planned", message: "Your itinerary for Kathmandu is ready", time: "1d ago", read: true },
  ])
  const box = useRef(null)

  const unreadCount = notifications.filter(n => !n.read).length

  useEffect(() => {
    if (!open) return undefined
    const onDown = (event) => {
      if (!box.current?.contains(event.target)) setOpen(false)
    }
    const onKey = (event) => { if (event.key === "Escape") setOpen(false) }
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const markRead = (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
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
    <div ref={box} className="relative shrink-0">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="relative p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        aria-expanded={open}
      >
        <FiBell size={18} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-2rem)] bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-gray-200 dark:border-slate-700 z-[80] overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Notifications</h3>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={markAllRead}
                className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <FiBell size={32} className="mx-auto text-gray-300 dark:text-gray-600 mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">No notifications</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50 dark:border-slate-700/50 last:border-0 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors ${!n.read ? "bg-emerald-50/50 dark:bg-emerald-950/20" : ""}`}
                >
                  <div className="mt-0.5 shrink-0">{getIcon(n.type)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{n.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{n.message}</p>
                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">{n.time}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!n.read && (
                      <button
                        type="button"
                        onClick={() => markRead(n.id)}
                        className="p-1 rounded text-gray-400 hover:text-emerald-500 transition-colors"
                        aria-label="Mark as read"
                      >
                        <FiCheck size={14} />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => removeNotification(n.id)}
                      className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Remove notification"
                    >
                      <FiX size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="px-4 py-2 border-t border-gray-100 dark:border-slate-700">
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold text-center block"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
