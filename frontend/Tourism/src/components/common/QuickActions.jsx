import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { FiZap, FiMap, FiCalendar, FiDollarSign, FiShield, FiMessageCircle, FiBook, FiNavigation } from "react-icons/fi"

const ACTIONS = [
  { to: "/itinerary", icon: FiCalendar, label: "Plan Trip", color: "bg-emerald-500" },
  { to: "/budget-estimator", icon: FiDollarSign, label: "Budget", color: "bg-amber-500" },
  { to: "/emergency", icon: FiShield, label: "Emergency", color: "bg-red-500" },
  { to: "/navigation", icon: FiNavigation, label: "Navigate", color: "bg-blue-500" },
  { to: "/chatbot", icon: FiMessageCircle, label: "AI Assistant", color: "bg-purple-500" },
  { to: "/explore-map", icon: FiMap, label: "Explore Map", color: "bg-teal-500" },
  { to: "/language", icon: FiBook, label: "Phrasebook", color: "bg-pink-500" },
]

/**
 * Quick Actions floating menu ÔÇö provides one-click access to the most
 * used features from any page.
 */
export default function QuickActions() {
  const [open, setOpen] = useState(false)
  const box = useRef(null)

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

  return (
    <div ref={box} className="fixed left-4 bottom-20 z-[55]">
      {open && (
        <div className="absolute bottom-14 left-0 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 p-3 w-56 mb-2">
          <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-2 mb-2">Quick Actions</p>
          <div className="grid grid-cols-2 gap-1">
            {ACTIONS.map(({ to, icon: Icon, label, color }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setOpen(false)}
                className="flex flex-col items-center gap-1.5 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors group"
              >
                <div className={`w-9 h-9 rounded-xl ${color} text-white flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform`}>
                  <Icon size={16} />
                </div>
                <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        aria-label="Quick actions"
        aria-expanded={open}
        className={`flex items-center justify-center w-12 h-12 rounded-full shadow-lg transition-all duration-300 hover:scale-110 ${
          open
            ? "bg-gray-700 text-white rotate-45"
            : "bg-[var(--ny-green)] text-white"
        }`}
      >
        <FiZap size={22} />
      </button>
    </div>
  )
}
