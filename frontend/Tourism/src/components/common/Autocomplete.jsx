import { useState, useRef, useEffect, useCallback } from "react"
import { FiSearch, FiX } from "react-icons/fi"

/**
 * Accessible autocomplete with keyboard navigation,
 * debounced search, and custom rendering.
 */
export default function Autocomplete({
  suggestions = [],
  onSelect,
  onSearch,
  placeholder = "Search...",
  renderItem,
  debounceMs = 300,
  maxResults = 10,
  className = "",
}) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(-1)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const containerRef = useRef(null)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query.trim()) {
      setResults([])
      setLoading(false)
      return
    }
    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const filtered = onSearch
          ? await onSearch(query)
          : suggestions.filter(s =>
              (typeof s === "string" ? s : s.label || s.name || "")
                .toLowerCase()
                .includes(query.toLowerCase())
            )
        setResults(filtered.slice(0, maxResults))
        setHighlighted(filtered.length > 0 ? 0 : -1)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, debounceMs)
    return () => clearTimeout(debounceRef.current)
  }, [query, suggestions, onSearch, debounceMs, maxResults])

  // Close on outside click
  useEffect(() => {
    const onDown = (e) => {
      if (!containerRef.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [])

  const handleKeyDown = useCallback((e) => {
    if (!open || results.length === 0) return
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setHighlighted(i => (i + 1) % results.length)
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setHighlighted(i => (i - 1 + results.length) % results.length)
    } else if (e.key === "Enter" && highlighted >= 0) {
      e.preventDefault()
      const item = results[highlighted]
      setQuery(typeof item === "string" ? item : item.label || item.name || "")
      setOpen(false)
      onSelect?.(item)
    } else if (e.key === "Escape") {
      setOpen(false)
    }
  }, [open, results, highlighted, onSelect])

  const handleSelect = (item) => {
    setQuery(typeof item === "string" ? item : item.label || item.name || "")
    setOpen(false)
    onSelect?.(item)
  }

  const clear = () => {
    setQuery("")
    setResults([])
    inputRef.current?.focus()
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full text-sm rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-9 pr-9 py-2.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          aria-controls="autocomplete-list"
        />
        {query && (
          <button
            type="button"
            onClick={clear}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-full text-gray-400 hover:text-gray-600"
            aria-label="Clear search"
          >
            <FiX size={14} />
          </button>
        )}
      </div>

      {open && (results.length > 0 || loading) && (
        <ul
          id="autocomplete-list"
          role="listbox"
          className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl py-1"
        >
          {loading && (
            <li className="px-4 py-2 text-xs text-gray-400 text-center">Searching...</li>
          )}
          {!loading && results.map((item, i) => {
            const label = typeof item === "string" ? item : item.label || item.name || ""
            return (
              <li
                key={i}
                role="option"
                aria-selected={i === highlighted}
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setHighlighted(i)}
                className={`px-4 py-2.5 text-sm cursor-pointer transition-colors ${
                  i === highlighted
                    ? "bg-[var(--ny-soft-green)] text-[var(--ny-green)]"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                }`}
              >
                {renderItem ? renderItem(item) : label}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
