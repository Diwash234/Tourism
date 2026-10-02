import { useState, useMemo } from "react"
import { FiSearch, FiX, FiFilter } from "react-icons/fi"
import { useDebounce } from "../../hooks/useDebounce"

/**
 * Search bar with integrated filter chips and debounced input.
 * Combines search and filtering in a single component.
 */
export default function SearchWithFilters({
  onSearch,
  onFilterChange,
  filters = [],
  placeholder = "Search...",
  className = "",
}) {
  const [query, setQuery] = useState("")
  const [activeFilters, setActiveFilters] = useState({})
  const debouncedQuery = useDebounce(query, 300)

  useMemo(() => {
    onSearch?.(debouncedQuery)
  }, [debouncedQuery, onSearch])

  const toggleFilter = (key, value) => {
    const newFilters = { ...activeFilters }
    if (newFilters[key] === value) {
      delete newFilters[key]
    } else {
      newFilters[key] = value
    }
    setActiveFilters(newFilters)
    onFilterChange?.(newFilters)
  }

  const clearAll = () => {
    setQuery("")
    setActiveFilters({})
    onSearch?.("")
    onFilterChange?.({})
  }

  const hasActive = query || Object.keys(activeFilters).length > 0

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="relative">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="w-full text-sm rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 pl-10 pr-10 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600"
            aria-label="Clear search"
          >
            <FiX size={14} />
          </button>
        )}
      </div>

      {filters.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <FiFilter size={14} className="text-gray-400" />
          {filters.map((filter) => (
            <button
              key={filter.key}
              type="button"
              onClick={() => toggleFilter(filter.key, filter.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${
                activeFilters[filter.key] === filter.value
                  ? "bg-[var(--ny-green)] text-white border-[var(--ny-green)]"
                  : "border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700"
              }`}
            >
              {filter.label}
            </button>
          ))}
          {hasActive && (
            <button
              type="button"
              onClick={clearAll}
              className="px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-full transition-colors"
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  )
}
