import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { FiSearch, FiX, FiFilter, FiMapPin, FiStar } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { destinationApi } from "../../services/destinationService"

/**
 * Advanced search with filters for category, province, budget, rating, and activity.
 * Debounced search with real-time results.
 */
export default function AdvancedSearch({ onResultSelect: _onResultSelect, className = "" }) {
  const { t: _t } = useTranslation()
  const [query, setQuery] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({
    category: "",
    province: "",
    budget: "",
    minRating: "",
    activity: "",
  })
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const provinces = ["Bagmati", "Gandaki", "Karnali", "Koshi", "Lumbini", "Madhesh", "Sudurpashchim"]
  const categories = ["Mountain", "Temple", "Lake", "City", "Village", "National Park", "Heritage Site"]
  const budgets = ["Budget", "Mid-range", "Luxury"]
  const activities = ["Trekking", "Sightseeing", "Photography", "Cultural", "Adventure", "Relaxation"]

  // Debounced search
  useEffect(() => {
    if (!query.trim() && !Object.values(filters).some(v => v)) {
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      setSearched(true)
      try {
        const params = {}
        if (query) params.search = query
        if (filters.category) params.category = filters.category
        if (filters.province) params.province = filters.province
        if (filters.budget) params.budget_level = filters.budget
        if (filters.minRating) params.min_rating = filters.minRating
        if (filters.activity) params.activity = filters.activity

        const data = await destinationApi.getAll(params)
        setResults(data.results || data || [])
      } catch (err) {
        console.error("Search failed:", err)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 400)

    return () => clearTimeout(timer)
  }, [query, filters])

  // Resetting results when the search becomes empty used to happen in the
  // effect above, but a synchronous setState there is banned by
  // react-hooks/set-state-in-effect — so the reset happens in the event
  // handlers that change `query`/`filters` instead.
  const clearResultsIfEmpty = (nextQuery, nextFilters) => {
    if (!nextQuery.trim() && !Object.values(nextFilters).some(v => v)) {
      setResults([])
      setSearched(false)
    }
  }

  const handleQueryChange = (value) => {
    setQuery(value)
    clearResultsIfEmpty(value, filters)
  }

  const handleFilterChange = (key, value) => {
    const nextFilters = { ...filters, [key]: value }
    setFilters(nextFilters)
    clearResultsIfEmpty(query, nextFilters)
  }

  const clearFilters = () => {
    const emptyFilters = { category: "", province: "", budget: "", minRating: "", activity: "" }
    setFilters(emptyFilters)
    setQuery("")
    clearResultsIfEmpty("", emptyFilters)
  }

  const activeFilterCount = Object.values(filters).filter(v => v).length

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="search"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Search destinations, activities, places..."
          className="w-full text-sm rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-11 pr-20 py-3 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {query && (
            <button
              type="button"
              onClick={() => handleQueryChange("")}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600"
              aria-label="Clear search"
            >
              <FiX size={16} />
            </button>
          )}
          <button
            type="button"
            onClick={() => setShowFilters(v => !v)}
            className={`p-1.5 rounded-lg transition-colors ${
              showFilters || activeFilterCount > 0
                ? "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30"
                : "text-gray-400 hover:text-gray-600"
            }`}
            aria-label="Toggle filters"
          >
            <FiFilter size={16} />
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-600 text-[9px] font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Filters</h4>
            {activeFilterCount > 0 && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs text-red-500 hover:text-red-600 font-medium"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <div>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Category</label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange("category", e.target.value)}
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">All</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Province</label>
              <select
                value={filters.province}
                onChange={(e) => handleFilterChange("province", e.target.value)}
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">All</option>
                {provinces.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Budget</label>
              <select
                value={filters.budget}
                onChange={(e) => handleFilterChange("budget", e.target.value)}
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">Any</option>
                {budgets.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Min Rating</label>
              <select
                value={filters.minRating}
                onChange={(e) => handleFilterChange("minRating", e.target.value)}
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">Any</option>
                <option value="4">4+ Stars</option>
                <option value="3">3+ Stars</option>
                <option value="2">2+ Stars</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">Activity</label>
              <select
                value={filters.activity}
                onChange={(e) => handleFilterChange("activity", e.target.value)}
                className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">All</option>
                {activities.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" />
        </div>
      ) : searched && results.length === 0 ? (
        <div className="text-center py-12">
          <FiSearch className="mx-auto text-gray-300 dark:text-gray-600 mb-3" size={40} />
          <p className="text-sm text-gray-500 dark:text-gray-400">No destinations match your search criteria</p>
          <button
            type="button"
            onClick={clearFilters}
            className="mt-3 text-xs text-[var(--ny-green)] font-semibold hover:underline"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((dest, i) => (
            <Link
              key={dest.id || i}
              to={`/destinations/${dest.slug || dest.id}`}
              className="group bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
            >
              <div className="relative aspect-[4/3] overflow-hidden bg-gray-100 dark:bg-slate-700">
                <img
                  src={dest.image_url || dest.images?.[0]?.src || "/placeholder-destination.jpg"}
                  alt={dest.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                {dest.rating && (
                  <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-full bg-black/60 text-white text-xs font-semibold">
                    <FiStar size={12} className="fill-amber-400" />
                    {dest.rating.toFixed(1)}
                  </div>
                )}
                <div className="absolute bottom-3 left-3 right-3">
                  <p className="text-white text-sm font-bold truncate">{dest.name}</p>
                  <p className="text-white/80 text-xs flex items-center gap-1 mt-0.5">
                    <FiMapPin size={10} />
                    {dest.district}
                  </p>
                </div>
              </div>
              <div className="p-4">
                {dest.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                    {dest.description}
                  </p>
                )}
                {dest.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {dest.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-[var(--ny-soft-green)] text-[var(--ny-green)]"
                      >
                        {tag}
                      </span>
                    ))}
                    {dest.tags.length > 3 && (
                      <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400">
                        +{dest.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
