import { useState } from "react"
import { FiFilter, FiX, FiChevronDown } from "react-icons/fi"

/**
 * Filter bar with search, sort, and filter dropdowns.
 * Collapsible on mobile.
 */
export default function FilterBar({ filters, onFilterChange, onSortChange, sortOptions, onSearchChange, searchPlaceholder = "Search..." }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1">
          {onSearchChange && (
            <input
              type="search"
              placeholder={searchPlaceholder}
              onChange={e => onSearchChange(e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          )}
        </div>
        <button
          type="button"
          onClick={() => setMobileOpen(v => !v)}
          className="lg:hidden flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-slate-600 rounded-lg"
        >
          <FiFilter size={14} />
          Filters
          <FiChevronDown size={14} className={`transition-transform ${mobileOpen ? "rotate-180" : ""}`} />
        </button>
      </div>

      <div className={`mt-3 flex-wrap items-center gap-2 ${mobileOpen ? "flex" : "hidden lg:flex"}`}>
        {filters.map((filter, i) => (
          <select
            key={i}
            value={filter.value}
            onChange={e => onFilterChange(filter.key, e.target.value)}
            className="text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">{filter.label}</option>
            {filter.options.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        ))}

        {onSortChange && sortOptions && (
          <select
            onChange={e => onSortChange(e.target.value)}
            className="text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {sortOptions.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        )}

        <button
          type="button"
          onClick={() => { filters.forEach(f => onFilterChange(f.key, "")); onSearchChange?.("") }}
          className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
        >
          <FiX size={14} />
          Clear
        </button>
      </div>
    </div>
  )
}
