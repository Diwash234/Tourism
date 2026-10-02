import { useState, useMemo } from "react"
import { FiFilter, FiX, FiChevronDown, FiMapPin, FiStar, FiDollarSign } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"

/**
 * Advanced filter panel for destination listing.
 * Supports category, province, budget, rating, and activity filters.
 */
export default function DestinationFilters({ destinations, onFilterChange, className = "" }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [filters, setFilters] = useState({
    category: "",
    province: "",
    budget: "",
    rating: "",
    activity: "",
    search: "",
  })

  const categories = useMemo(() => {
    const cats = new Set(destinations.map(d => d.category).filter(Boolean))
    return Array.from(cats).sort()
  }, [destinations])

  const provinces = useMemo(() => {
    const provs = new Set(destinations.map(d => d.province).filter(Boolean))
    return Array.from(provs).sort()
  }, [destinations])

  const activities = useMemo(() => {
    const acts = new Set()
    destinations.forEach(d => {
      d.activities?.forEach(a => acts.add(a))
      d.tags?.forEach(tag => acts.add(tag))
    })
    return Array.from(acts).sort()
  }, [destinations])

  const handleChange = (key, value) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFilterChange?.(newFilters)
  }

  const clearAll = () => {
    const cleared = { category: "", province: "", budget: "", rating: "", activity: "", search: "" }
    setFilters(cleared)
    onFilterChange?.(cleared)
  }

  const activeCount = Object.values(filters).filter(v => v !== "").length

  return (
    <div className={`bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden ${className}`}>
      {/* Filter Header */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <FiFilter size={16} className="text-[var(--ny-green)]" />
          <span className="text-sm font-bold text-gray-900 dark:text-white">Filters</span>
          {activeCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--ny-green)] text-xs font-bold text-white">
              {activeCount}
            </span>
          )}
        </div>
        <FiChevronDown size={16} className={`text-gray-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {/* Filter Panel */}
      {open && (
        <div className="px-5 pb-5 space-y-4 border-t border-[var(--ny-border)]">
          {/* Search */}
          <div className="pt-4">
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              Search
            </label>
            <div className="relative">
              <FiMapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="search"
                value={filters.search}
                onChange={(e) => handleChange("search", e.target.value)}
                placeholder={t("dest.search_placeholder")}
                className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Category */}
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              Category
            </label>
            <select
              value={filters.category}
              onChange={(e) => handleChange("category", e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Province */}
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              Province
            </label>
            <select
              value={filters.province}
              onChange={(e) => handleChange("province", e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Provinces</option>
              {provinces.map(prov => (
                <option key={prov} value={prov}>{prov}</option>
              ))}
            </select>
          </div>

          {/* Budget */}
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              <FiDollarSign size={12} className="inline mr-1" />
              Budget Level
            </label>
            <select
              value={filters.budget}
              onChange={(e) => handleChange("budget", e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Any Budget</option>
              <option value="budget">Budget</option>
              <option value="moderate">Moderate</option>
              <option value="luxury">Luxury</option>
            </select>
          </div>

          {/* Rating */}
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              <FiStar size={12} className="inline mr-1" />
              Minimum Rating
            </label>
            <select
              value={filters.rating}
              onChange={(e) => handleChange("rating", e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Any Rating</option>
              <option value="4">4+ Stars</option>
              <option value="3">3+ Stars</option>
              <option value="2">2+ Stars</option>
            </select>
          </div>

          {/* Activity */}
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              Activity
            </label>
            <select
              value={filters.activity}
              onChange={(e) => handleChange("activity", e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All Activities</option>
              {activities.map(act => (
                <option key={act} value={act}>{act}</option>
              ))}
            </select>
          </div>

          {/* Clear All */}
          {activeCount > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="flex items-center gap-1.5 text-xs font-semibold text-red-500 hover:text-red-600 transition-colors"
            >
              <FiX size={14} />
              Clear all filters
            </button>
          )}
        </div>
      )}
    </div>
  )
}
