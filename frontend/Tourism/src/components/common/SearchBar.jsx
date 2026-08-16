import { useState, useRef, useEffect, useCallback } from "react"
import { FiSearch, FiMapPin, FiNavigation, FiCompass, FiX } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { resolveFuzzyPlaceLocation } from "../../utils/nepalGeocoder"

// Nepal palette constants matching design system
const INK = "#1f3329"
const MOUNTAIN_GREEN = "#1f6b4d"
const MOUNTAIN_GREEN_DARK = "#174f38"
const TERRACOTTA = "#c2603a"
const GOLD = "#b8862f"
const BG_WARM = "#faf8f4"

const SearchBar = ({
  placeholder = "Search any place (e.g. pkr, phewa, ebc, pashupati)...",
  onSearch,
  className = "",
  defaultValue = "",
  /** Optional: override autocomplete fetcher. If provided, (query) => Promise<[{id,name,slug,cover_image_url,category_name,district}]> */
  fetchSuggestions,
}) => {
  const [query, setQuery] = useState(defaultValue)
  const [geocodedResult, setGeocodedResult] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [loadingSug, setLoadingSug] = useState(false)
  const containerRef = useRef(null)
  const navigate = useNavigate()
  const abortRef = useRef(null)

  // Keep controlled value in sync when parent changes defaultValue
  useEffect(() => {
    if (defaultValue !== query) setQuery(defaultValue)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultValue])

  const loadSuggestions = useCallback(
    async (q) => {
      if (!fetchSuggestions || q.trim().length < 1) {
        setSuggestions([])
        return
      }
      setLoadingSug(true)
      if (abortRef.current) abortRef.current.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl
      try {
        const results = await fetchSuggestions(q.trim(), ctrl.signal)
        if (!ctrl.signal.aborted) setSuggestions(results || [])
      } catch {
        if (!ctrl.signal.aborted) setSuggestions([])
      } finally {
        if (!ctrl.signal.aborted) setLoadingSug(false)
      }
    },
    [fetchSuggestions]
  )

  useEffect(() => {
    const q = query.trim()
    if (q.length >= 2) {
      const match = resolveFuzzyPlaceLocation(q)
      setGeocodedResult(match)
    } else {
      setGeocodedResult(null)
    }
    if (fetchSuggestions && q.length >= 1) {
      loadSuggestions(q)
    } else {
      setSuggestions([])
    }
    setIsOpen(q.length >= 1)
  }, [query, fetchSuggestions, loadSuggestions])

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    setIsOpen(false)
    const q = query.trim()
    if (!q) return
    if (geocodedResult && geocodedResult.slug) {
      navigate(`/destinations/${geocodedResult.slug}`)
    } else {
      onSearch?.(q) || navigate(`/destinations?q=${encodeURIComponent(q)}`)
    }
  }

  const handleSelectSuggestion = (item) => {
    setQuery(item.name)
    setIsOpen(false)
    if (item.slug) {
      navigate(`/destinations/${item.slug}`)
    } else {
      navigate(`/destinations?q=${encodeURIComponent(item.name)}`)
    }
  }

  const handleSelectGeocoded = (place) => {
    setQuery(place.correctedName)
    setIsOpen(false)
    if (place.slug) navigate(`/destinations/${place.slug}`)
    else navigate(`/destinations?q=${encodeURIComponent(place.correctedName)}`)
  }

  const hasDropdown = isOpen && (suggestions.length > 0 || geocodedResult || loadingSug)

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <FiSearch className="absolute left-4 pointer-events-none" size={18} style={{ color: MOUNTAIN_GREEN }} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={(e) => {
            if (query.trim().length >= 1) setIsOpen(true)
            e.currentTarget.style.borderColor = MOUNTAIN_GREEN
          }}
          onBlur={(e) => (e.currentTarget.style.borderColor = "rgba(31,107,77,0.25)")}
          placeholder={placeholder}
          className="w-full pl-11 pr-10 py-3 sm:py-3.5 bg-white border rounded-2xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-4 transition-all shadow-lg"
          style={{
            borderColor: "rgba(31,107,77,0.25)",
            boxShadow: "0 8px 24px -8px rgba(31,51,41,0.18)",
          }}
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("")
              setGeocodedResult(null)
              setSuggestions([])
              setIsOpen(false)
              onSearch?.("")
            }}
            className="absolute right-3.5 p-1 rounded-full text-gray-400 hover:text-gray-700 transition-colors"
          >
            <FiX size={14} />
          </button>
        )}
      </form>

      <AnimatePresence>
        {hasDropdown && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl border shadow-2xl p-3 z-50 text-left space-y-2 max-h-96 overflow-y-auto"
            style={{ borderColor: "rgba(31,107,77,0.2)", boxShadow: "0 20px 50px -12px rgba(31,51,41,0.25)" }}
          >
            {/* Destination name suggestions */}
            {suggestions.length > 0 && (
              <div>
                <div className="flex items-center gap-2 px-1 pb-1 mb-1 border-b border-gray-100">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full"
                        style={{ background: `${MOUNTAIN_GREEN}15`, color: MOUNTAIN_GREEN_DARK }}>
                    Destinations
                  </span>
                  {loadingSug && <span className="text-[10px] text-gray-400">searching…</span>}
                </div>
                <div className="space-y-1">
                  {suggestions.slice(0, 8).map((s) => (
                    <button
                      type="button"
                      key={s.id || s.slug}
                      onClick={() => handleSelectSuggestion(s)}
                      className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-[#1f6b4d]/5 transition-all text-left group"
                    >
                      <div className="w-11 h-11 rounded-lg overflow-hidden bg-gray-100 shrink-0 flex items-center justify-center">
                        {s.cover_image_url ? (
                          <img
                            src={s.cover_image_url}
                            alt={s.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            onError={(e) => { e.currentTarget.style.display = "none" }}
                          />
                        ) : (
                          <span style={{ color: TERRACOTTA }}>
                            <FiMapPin size={16} />
                          </span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold truncate" style={{ color: INK }}>{s.name}</div>
                        <div className="text-[11px] text-gray-500 truncate">
                          {s.category_name || "Attraction"}
                          {s.district ? ` · ${s.district}` : ""}
                        </div>
                      </div>
                      <FiArrowRight className="text-gray-300 group-hover:text-[#c2603a] transition-colors shrink-0" size={16} />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Geocoded fuzzy match (Nepal place aliases) */}
            {geocodedResult && (
              <div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-1 mb-1 px-1">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full"
                        style={{ background: `${TERRACOTTA}15`, color: TERRACOTTA }}>
                    ⚡ Fuzzy match ({geocodedResult.confidence}%)
                  </span>
                  <span className="text-[10px] text-gray-400 font-mono">
                    {geocodedResult.district}, {geocodedResult.province}
                  </span>
                </div>

                {geocodedResult.didYouMean && (
                  <p className="text-[11px] font-semibold m-1 p-2 rounded-lg"
                     style={{ background: `${GOLD}20`, color: "#7a5a10" }}>
                    💡 {geocodedResult.didYouMean}
                  </p>
                )}

                <button
                  type="button"
                  onClick={() => handleSelectGeocoded(geocodedResult)}
                  className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-[#c2603a]/5 transition-all text-left group border"
                  style={{ borderColor: "rgba(194,96,58,0.25)", background: "linear-gradient(135deg, rgba(194,96,58,0.05), rgba(31,107,77,0.04))" }}
                >
                  <div className="w-14 h-14 rounded-lg overflow-hidden bg-gray-900 shrink-0 relative">
                    {geocodedResult.image ? (
                      <img src={geocodedResult.image} alt={geocodedResult.correctedName} className="w-full h-full object-cover group-hover:scale-110 transition-transform" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center" style={{ background: BG_WARM }}>
                        <FiMapPin size={20} style={{ color: TERRACOTTA }} />
                      </div>
                    )}
                  </div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-extrabold text-sm truncate" style={{ color: INK }}>
                        {geocodedResult.canonicalName}
                      </h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md shrink-0"
                            style={{ background: `${GOLD}25`, color: "#7a5a10" }}>
                        {geocodedResult.category}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                      <span className="px-2 py-0.5 rounded text-white font-bold flex items-center gap-1" style={{ background: MOUNTAIN_GREEN }}>
                        <FiMapPin size={10} /> {Number(geocodedResult.latitude).toFixed(3)}°, {Number(geocodedResult.longitude).toFixed(3)}°
                      </span>
                      {geocodedResult.altitude && (
                        <span className="px-2 py-0.5 rounded font-bold" style={{ background: "#fef3c7", color: "#92400e" }}>
                          ⛰️ {geocodedResult.altitude}
                        </span>
                      )}
                      <span className="text-gray-500 truncate">
                        🏛️ {geocodedResult.municipality || geocodedResult.district}
                      </span>
                    </div>
                  </div>
                </button>

                <div className="flex gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => handleSelectGeocoded(geocodedResult)}
                    className="flex-1 py-2 rounded-xl text-white font-bold text-xs flex items-center justify-center gap-1 shadow hover:opacity-90 transition"
                    style={{ background: MOUNTAIN_GREEN }}
                  >
                    <FiCompass size={12} /> Explore
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsOpen(false)
                      navigate(`/navigation?dest=${encodeURIComponent(geocodedResult.correctedName)}`)
                    }}
                    className="px-4 py-2 rounded-xl font-black text-xs flex items-center justify-center gap-1 shadow hover:opacity-90 transition"
                    style={{ background: GOLD, color: "#1f1a08" }}
                  >
                    <FiNavigation size={12} /> Route ➔
                  </button>
                </div>
              </div>
            )}

            {loadingSug && suggestions.length === 0 && !geocodedResult && (
              <div className="p-4 text-center text-xs text-gray-400">Searching destinations…</div>
            )}
            {!loadingSug && suggestions.length === 0 && !geocodedResult && query.trim().length >= 1 && (
              <div className="p-3 text-center text-xs text-gray-500">
                Press <span className="font-bold" style={{ color: MOUNTAIN_GREEN }}>Enter</span> to search for "{query}"
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default SearchBar
