import { useState, useRef, useEffect } from "react"
import { FiSearch, FiMapPin, FiNavigation, FiCompass, FiArrowRight, FiX } from "react-icons/fi"
import { motion, AnimatePresence } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { resolveFuzzyPlaceLocation } from "../../utils/nepalGeocoder"

const SearchBar = ({
  placeholder = "Search any place (e.g. pkr, bihadi, walling, galeswor, ebc)...",
  onSearch,
  className = "",
  defaultValue = "",
}) => {
  const [query, setQuery] = useState(defaultValue)
  const [geocodedResult, setGeocodedResult] = useState(null)
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (query.trim().length >= 2) {
      const match = resolveFuzzyPlaceLocation(query.trim())
      setGeocodedResult(match)
      setIsOpen(true)
    } else {
      setGeocodedResult(null)
      setIsOpen(false)
    }
  }, [query])

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
    if (geocodedResult) {
      navigate(`/destinations?q=${encodeURIComponent(geocodedResult.correctedName)}`)
    } else if (query.trim()) {
      onSearch?.(query.trim()) || navigate(`/destinations?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleSelectSuggestion = (place) => {
    setQuery(place.correctedName)
    setIsOpen(false)
    if (place.slug) {
      navigate(`/destinations/${place.slug}`)
    } else {
      navigate(`/destinations?q=${encodeURIComponent(place.correctedName)}`)
    }
  }

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <FiSearch className="absolute left-4 text-purple-600 pointer-events-none" size={18} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
          placeholder={placeholder}
          className="w-full pl-11 pr-10 py-3 sm:py-3.5 bg-white border border-purple-200/90 rounded-2xl text-xs sm:text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-600/10 shadow-lg shadow-purple-900/5 transition-all"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("")
              setGeocodedResult(null)
              setIsOpen(false)
            }}
            className="absolute right-3.5 p-1 rounded-full text-gray-400 hover:text-gray-700 transition-colors"
          >
            <FiX size={14} />
          </button>
        )}
      </form>

      {/* INTELLIGENT AUTO-ATTACHING GEOCODED DROPDOWN */}
      <AnimatePresence>
        {isOpen && geocodedResult && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className="absolute left-0 right-0 top-full mt-2 bg-white rounded-3xl border border-purple-200 shadow-2xl p-4 z-50 text-left space-y-3"
          >
            <div className="flex justify-between items-center border-b border-gray-100 pb-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full">
                ⚡ Intelligent Nepal Geo-Attacher ({geocodedResult.confidence}% match)
              </span>
              <span className="text-[10px] text-gray-400 font-mono">
                {geocodedResult.district}, {geocodedResult.province}
              </span>
            </div>

            {geocodedResult.didYouMean && (
              <p className="text-xs text-purple-900 font-bold bg-amber-50 border border-amber-200/80 p-2 rounded-xl">
                💡 {geocodedResult.didYouMean}
              </p>
            )}

            {/* Resolved Place Card with Auto-Attached GPS & Altitude */}
            <div
              onClick={() => handleSelectSuggestion(geocodedResult)}
              className="flex items-center gap-3 p-3 rounded-2xl bg-gradient-to-br from-purple-50/70 to-slate-50 border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="w-16 h-16 rounded-xl overflow-hidden bg-slate-900 shrink-0 relative">
                <img src={geocodedResult.image} alt={geocodedResult.correctedName} className="w-full h-full object-cover group-hover:scale-110 transition-transform" />
              </div>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-extrabold text-sm text-gray-900 truncate group-hover:text-purple-700 transition-colors">
                    {geocodedResult.canonicalName}
                  </h4>
                  <span className="text-[10px] font-bold text-amber-600 bg-amber-100/60 px-2 py-0.5 rounded-md shrink-0">
                    {geocodedResult.category}
                  </span>
                </div>

                {/* Auto-Attached GPS Coordinates & Altitude */}
                <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                  <span className="px-2 py-0.5 rounded bg-purple-700 text-white font-mono font-bold flex items-center gap-1">
                    <FiMapPin size={10} /> {geocodedResult.latitude?.toFixed(4)}° N, {geocodedResult.longitude?.toFixed(4)}° E
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                    ⛰️ {geocodedResult.altitude}
                  </span>
                  <span className="text-gray-500 truncate">
                    🏛️ {geocodedResult.municipality || geocodedResult.district}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2 pt-1">
              <button
                type="button"
                onClick={() => handleSelectSuggestion(geocodedResult)}
                className="flex-1 py-2 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs flex items-center justify-center gap-1 shadow"
              >
                <FiCompass size={12} /> Explore {geocodedResult.correctedName}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false)
                  navigate(`/navigation?dest=${encodeURIComponent(geocodedResult.correctedName)}`)
                }}
                className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs flex items-center justify-center gap-1 shadow"
              >
                <FiNavigation size={12} /> Route HUD ➔
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default SearchBar
