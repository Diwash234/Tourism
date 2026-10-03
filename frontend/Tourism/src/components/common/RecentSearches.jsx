import { useState } from "react"
import { FiClock, FiX } from "react-icons/fi"
import { useNavigate } from "react-router-dom"

const STORAGE_KEY = "ny_recent_searches"
const MAX_RECENT = 5

/**
 * Reads the persisted searches. Kept at module scope so the hook can
 * initialise its state with a lazy initializer instead of a synchronous
 * setState inside an effect (banned by react-hooks/set-state-in-effect).
 */
const readSearches = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")
  } catch {
    return []
  }
}

export function useRecentSearches() {
  const [searches, setSearches] = useState(readSearches)

  const addSearch = (query) => {
    if (!query?.trim()) return
    const trimmed = query.trim()
    const updated = [trimmed, ...searches.filter(s => s !== trimmed)].slice(0, MAX_RECENT)
    setSearches(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const removeSearch = (query) => {
    const updated = searches.filter(s => s !== query)
    setSearches(updated)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  }

  const clearAll = () => {
    setSearches([])
    localStorage.removeItem(STORAGE_KEY)
  }

  return { searches, addSearch, removeSearch, clearAll }
}

export default function RecentSearches({ onSelect, visible }) {
  const { searches, removeSearch, clearAll } = useRecentSearches()
  const _navigate = useNavigate()

  if (!visible || searches.length === 0) return null

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-200 dark:border-slate-700 p-2 z-50">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Recent Searches</span>
        <button
          type="button"
          onClick={clearAll}
          className="text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          Clear all
        </button>
      </div>
      {searches.map((query) => (
        <div key={query} className="flex items-center gap-2 group">
          <button
            type="button"
            onClick={() => onSelect?.(query)}
            className="flex-1 flex items-center gap-2 px-2 py-2 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors text-left"
          >
            <FiClock size={14} className="text-gray-400 shrink-0" />
            <span className="truncate">{query}</span>
          </button>
          <button
            type="button"
            onClick={() => removeSearch(query)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
            aria-label={`Remove ${query}`}
          >
            <FiX size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
