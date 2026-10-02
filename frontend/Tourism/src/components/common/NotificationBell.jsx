import { useState, useRef, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiBell, FiX, FiCheck, FiAlertTriangle, FiInfo } from "react-icons/fi"

/**
 * Notification bell dropdown with unread count, mark-as-read, and clear all.
 */
export default function NotificationBell({ notifications = [], onMarkRead, onClearAll }) {
  const [open, setOpen] = useState(false)
  const box = useRef(null)
  const unreadCount = notifications.filter(n => !n.read).length

  useEffect(() => {
    if (!open) return undefined
    const onDown = (e) => {
      if (!box.current?.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => { if (e.key === "Escape") setOpen(false) }
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  const getIcon = (type) => {
    switch (type) {
      case "alert": return <FiAlertTriangle size={14} className="text-amber-500" />
      case "success": return <FiCheck size={14} className="text-emerald-500" />
      case "info": return <FiInfo size={14} className="text-blue-500" />
      default: return <FiBell size={14} className="text-gray-400" />
    }
  }

  return (
    <div ref={box} className="relative">
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
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Notifications</h3>
            {notifications.length > 0 && (
              <button
                type="button"
                onClick={onClearAll}
                className="text-xs text-red-500 hover:text-red-600 font-medium"
              >
                Clear all
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
                  className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50 dark:border-slate-700/50 last:border-0 ${
                    !n.read ? "bg-emerald-50/50 dark:bg-emerald-950/20" : ""
                  }`}
                >
                  <div className="mt-0.5 shrink-0">{getIcon(n.type)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{n.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{n.message}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{n.time}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!n.read && (
                      <button
                        type="button"
                        onClick={() => onMarkRead?.(n.id)}
                        className="p-1 rounded text-gray-400 hover:text-emerald-500"
                        aria-label="Mark as read"
                      >
                        <FiCheck size={12} />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => onClearAll?.(n.id)}
                      className="p-1 rounded text-gray-400 hover:text-red-500"
                      aria-label="Remove"
                    >
                      <FiX size={12} />
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
              className="text-xs text-[var(--ny-green)] hover:text-[var(--ny-emerald)] font-semibold text-center block"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
