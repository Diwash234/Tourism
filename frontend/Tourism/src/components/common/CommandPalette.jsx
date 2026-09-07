import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import {
  Compass,
  MapPin,
  Navigation as NavIcon,
  Shield,
  PhoneCall,
  Heart,
  Package,
  Calendar,
  MessageSquare,
  Search,
  SlidersHorizontal,
  X,
  Sparkles,
  Command,
  LayoutDashboard
} from "lucide-react"

const COMMAND_ITEMS = [
  {
    id: "destinations",
    title: "Explore Destinations",
    category: "Explore",
    path: "/destinations",
    icon: MapPin,
    description: "Discover landmark cities, national parks, and heritage circuits across Nepal."
  },
  {
    id: "explore-map",
    title: "Interactive Nepal Map",
    category: "Explore",
    path: "/explore-map",
    icon: Compass,
    description: "Explore all 7 provinces, district borders, and geographic markers."
  },
  {
    id: "navigation",
    title: "Route & Navigation HUD",
    category: "Explore",
    path: "/navigation",
    icon: NavIcon,
    description: "Calculate road routes, travel duration, and turn-by-turn road steps."
  },
  {
    id: "packages",
    title: "Travel Packages & Circuit Tours",
    category: "Plan",
    path: "/packages",
    icon: Package,
    description: "Browse verified cultural, trekking, and heritage tour packages."
  },
  {
    id: "trip-planner",
    title: "My Trip Planner Workspace",
    category: "Plan",
    path: "/trip-planner",
    icon: Calendar,
    description: "Build custom itineraries, reorder daily stops, and estimate budgets."
  },
  {
    id: "safety",
    title: "Travel Safety & Hazard Alerts",
    category: "Safety",
    path: "/safety",
    icon: Shield,
    description: "DoR road conditions, DHM hydrological river alerts, and weather advisories."
  },
  {
    id: "emergency",
    title: "Emergency Services Directory",
    category: "Safety",
    path: "/emergency",
    icon: PhoneCall,
    description: "National emergency hotlines, medical centers, and tourist police contacts."
  },
  {
    id: "favorites",
    title: "Saved Places & Favorites",
    category: "User",
    path: "/favorites",
    icon: Heart,
    description: "View and organize your bookmarked destinations and packages."
  },
  {
    id: "chatbot",
    title: "Himal AI Assistant",
    category: "AI",
    path: "/chatbot",
    icon: MessageSquare,
    description: "Ask natural language questions about Nepal travel, weather, and permits."
  },
  {
    id: "admin",
    title: "Admin Operations Center",
    category: "Admin",
    path: "/admin",
    icon: LayoutDashboard,
    description: "Data quality center, CMS block builder, audit logs, and system health."
  }
]

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setIsOpen((prev) => !prev)
      }
      if (e.key === "Escape") {
        setIsOpen(false)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const filteredItems = COMMAND_ITEMS.filter((item) =>
    item.title.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase()) ||
    item.description.toLowerCase().includes(query.toLowerCase())
  )

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  const handleSelect = (item) => {
    setIsOpen(false)
    setQuery("")
    navigate(item.path)
  }

  const handleKeyDownInInput = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length))
    } else if (e.key === "Enter" && filteredItems[selectedIndex]) {
      e.preventDefault()
      handleSelect(filteredItems[selectedIndex])
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-20 px-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="relative flex items-center px-4 py-3 border-b border-slate-200 dark:border-slate-800">
          <Search className="w-5 h-5 text-slate-400 mr-3 shrink-0" />
          <input
            type="text"
            autoFocus
            placeholder="Search commands, destinations, safety, maps... (Ctrl+K)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDownInInput}
            className="w-full bg-transparent text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none text-base"
          />
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Command Items List */}
        <div className="max-h-[380px] overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">
              <Sparkles className="w-8 h-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
              <p className="font-medium text-sm">No matching commands found</p>
              <p className="text-xs text-slate-400 mt-1">Try searching for 'map', 'safety', 'packages', or 'itinerary'.</p>
            </div>
          ) : (
            filteredItems.map((item, index) => {
              const Icon = item.icon
              const isSelected = index === selectedIndex
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-rose-50 dark:bg-slate-800/80 border-l-4 border-[#C8102E]"
                      : "hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  }`}
                >
                  <div
                    className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                      isSelected
                        ? "bg-[#C8102E] text-white"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm truncate">
                        {item.title}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase tracking-wider">
                        {item.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1 mt-0.5">
                      {item.description}
                    </p>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Footer Shortcut Bar */}
        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded shadow-xs text-[10px]">↑</kbd>
              <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded shadow-xs text-[10px]">↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded shadow-xs text-[10px]">↵</kbd>
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded shadow-xs text-[10px]">ESC</kbd>
              Close
            </span>
          </div>
          <div className="flex items-center gap-1 text-[#C8102E] font-medium">
            <Command className="w-3 h-3" /> Nepal Yatra HUD
          </div>
        </div>
      </div>
    </div>
  )
}
