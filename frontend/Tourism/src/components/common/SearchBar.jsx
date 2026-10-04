import { useState, useRef, useEffect } from "react"
import { FiSearch, FiX } from "react-icons/fi"
import { useNavigate } from "react-router-dom"
import { resolveSmartSearch } from "../../utils/smartSearch"
import RecentSearches from "./RecentSearches"

/**
 * Enhanced search bar with recent searches, keyboard navigation,
 * and smart destination matching.
 */
export default function SearchBar({ placeholder = "Search destinationsÔÇª", autoFocus = false, onSearch }) {
  const [query, setQuery] = useState("")
  const [focused, setFocused] = useState(false)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus()
    }
  }, [autoFocus])

  const handleSubmit = (e) => {
    e.preventDefault()
    const destination = resolveSmartSearch(query)
    if (destination) {
      navigate(destination)
      setQuery("")
      onSearch?.(destination)
    }
  }

  const showRecent = focused && query.length === 0

  return (
    <div className="relative w-full">
      <form onSubmit={handleSubmit} role="search" className="relative">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#63E6BE] pointer-events-none" size={16} />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          type="search"
          aria-label="Search destinations"
          enterKeyHint="search"
          placeholder={placeholder}
          className="w-full text-sm rounded-full border border-white/20 bg-white/10 text-white placeholder:text-[#AFC5BC] pl-9 pr-10 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(""); inputRef.current?.focus() }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Clear search"
          >
            <FiX size={14} />
          </button>
        )}
      </form>
      {showRecent && <RecentSearches visible={true} onSelect={(q) => { setQuery(q); inputRef.current?.focus() }} />}
    </div>
  )
}
