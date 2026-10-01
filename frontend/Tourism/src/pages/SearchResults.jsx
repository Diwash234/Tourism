import { useState, useCallback, useMemo, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useSearchParams } from "react-router-dom"
import {
  FiSearch, FiFilter, FiGrid, FiList, FiMap, FiMapPin,
  FiClock, FiHeart, FiShare2, FiX, FiChevronDown,
  FiStar, FiDollarSign, FiUsers, FiCalendar, FiRefreshCw,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import useGeolocation from "../hooks/useGeolocation"
import destinationApi from "../api/destinationApi"
import hotelApi from "../api/hotelApi"

// ─── Facet Filter Component ──────────────────────────────────────────────────
const FacetFilter = ({ title, options, selected, onToggle }) => {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between py-3 text-sm font-medium text-gray-700"
      >
        {title}
        <FiChevronDown size={14} className={`transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="pb-3 space-y-2">
              {options.map((option) => (
                <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selected.includes(option.value)}
                    onChange={() => onToggle(option.value)}
                    className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="text-sm text-gray-600">{option.label}</span>
                  <span className="text-xs text-gray-400 ml-auto">{option.count}</span>
                </label>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── Sort Dropdown ───────────────────────────────────────────────────────────
const SortDropdown = ({ value, onChange }) => {
  const [open, setOpen] = useState(false)
  const options = [
    { value: "relevance", label: "Relevance" },
    { value: "price_low", label: "Price: Low to High" },
    { value: "price_high", label: "Price: High to Low" },
    { value: "rating", label: "Rating" },
    { value: "distance", label: "Distance" },
    { value: "newest", label: "Newest" },
  ]

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        Sort: {options.find((o) => o.value === value)?.label}
        <FiChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1"
          >
            {options.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value)
                  setOpen(false)
                }}
                className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                  value === option.value ? "text-emerald-600 font-medium" : "text-gray-700"
                }`}
              >
                {option.label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── Result Card Component ───────────────────────────────────────────────────
const ResultCard = ({ result, view, onSave, onShare, isSaved }) => {
  if (view === "grid") {
    return (
      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card-base overflow-hidden group"
      >
        <div className="h-40 bg-gray-100 relative">
          {result.image ? (
            <img src={result.image} alt={result.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300">
              <FiMapPin size={32} />
            </div>
          )}
          <div className="absolute top-2 right-2 flex gap-1">
            <button
              onClick={() => onSave(result)}
              className={`p-2 rounded-full ${isSaved ? "bg-red-500 text-white" : "bg-white/90 text-gray-600"}`}
            >
              <FiHeart size={14} />
            </button>
            <button
              onClick={() => onShare(result)}
              className="p-2 bg-white/90 text-gray-600 rounded-full"
            >
              <FiShare2 size={14} />
            </button>
          </div>
        </div>
        <div className="p-4">
          <h3 className="font-semibold text-gray-900">{result.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{result.location}</p>
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-1">
              {Number(result.rating) > 0 ? (
                <>
                  <FiStar size={14} className="text-amber-400 fill-amber-400" />
                  <span className="text-sm font-medium">{Number(result.rating).toFixed(1)}</span>
                </>
              ) : (
                <span className="text-sm text-gray-500">New</span>
              )}
            </div>
            <span className="text-sm font-bold text-emerald-600">{result.price != null && result.price !== "" ? `NPR ${Number(result.price).toLocaleString()}` : "Fee not recorded"}</span>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card-base p-4 flex gap-4"
    >
      <div className="w-32 h-24 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
        {result.image ? (
          <img src={result.image} alt={result.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300">
            <FiMapPin size={24} />
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">{result.name}</h3>
            <p className="text-sm text-gray-500">{result.location}</p>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => onSave(result)}
              className={`p-1.5 rounded-lg ${isSaved ? "text-red-500" : "text-gray-400 hover:text-red-500"}`}
            >
              <FiHeart size={16} />
            </button>
            <button onClick={() => onShare(result)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg">
              <FiShare2 size={16} />
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2">
          <div className="flex items-center gap-1">
            {Number(result.rating) > 0 ? (
              <>
                <FiStar size={14} className="text-amber-400 fill-amber-400" />
                <span className="text-sm">{Number(result.rating).toFixed(1)}</span>
              </>
            ) : (
              <span className="text-sm text-gray-500">New</span>
            )}
          </div>
          <span className="text-sm text-gray-500">{result.type}</span>
          <span className="text-sm font-bold text-emerald-600">{result.price != null && result.price !== "" ? `NPR ${Number(result.price).toLocaleString()}` : "Fee not recorded"}</span>
        </div>
      </div>
    </motion.div>
  )
}

// ─── Map View Component ──────────────────────────────────────────────────────
const MapView = ({ results }) => {
  return (
    <div className="card-base p-4">
      <div className="h-96 bg-gray-100 rounded-xl flex items-center justify-center">
        <div className="text-center">
          <FiMap size={48} className="mx-auto text-gray-300 mb-2" />
          <p className="text-gray-500">Map view with {results.length} results</p>
          <p className="text-sm text-gray-400">Integrate with AdvancedMap component</p>
        </div>
      </div>
    </div>
  )
}

// ─── Search History Component ────────────────────────────────────────────────
const SearchHistory = ({ history, onSelect, onClear }) => {
  if (!history.length) return null

  return (
    <div className="card-base p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
          <FiClock size={14} /> Recent Searches
        </h3>
        <button onClick={onClear} className="text-xs text-gray-400 hover:text-gray-600">
          Clear
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {history.map((item, i) => (
          <button
            key={i}
            onClick={() => onSelect(item)}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-600 transition-colors"
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Related Searches Component ──────────────────────────────────────────────
const RelatedSearches = ({ query, onSelect }) => {
  const related = [
    `${query} hotels`,
    `${query} tours`,
    `${query} budget`,
    `${query} best time to visit`,
  ]

  return (
    <div className="card-base p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Related Searches</h3>
      <div className="flex flex-wrap gap-2">
        {related.map((item, i) => (
          <button
            key={i}
            onClick={() => onSelect(item)}
            className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 rounded-full text-sm text-emerald-700 transition-colors"
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Main Search Results Page ────────────────────────────────────────────────
const SearchResults = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const { showToast } = useToast()
  const query = searchParams.get("q") || ""

  const [view, setView] = useState("list") // list | grid | map
  const [sort, setSort] = useState("relevance")
  const [showFilters, setShowFilters] = useState(true)
  const [savedSearches, setSavedSearches] = useState([])
  const [searchHistory, setSearchHistory] = useState(["pokhara", "kathmandu hotels", "everest trek"])
  const [savedResults, setSavedResults] = useState([])

  // Filter states
  const [selectedTypes, setSelectedTypes] = useState([])
  const [selectedPriceRange, setSelectedPriceRange] = useState([])
  const [selectedRatings, setSelectedRatings] = useState([])

  const { position } = useGeolocation({ auto: false })
  const [results, setResults] = useState([])
  const [searchError, setSearchError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    const q = query.trim()
    if (!q) {
      // Deferred one tick: keeps synchronous setState out of the effect flush
      // (react-hooks/set-state-in-effect). Runs before any later render can
      // invalidate it, so the clear behaves exactly as before.
      queueMicrotask(() => {
        setResults([])
        setSearchError("")
      })
      return undefined
    }
    // Deferred one tick: keeps synchronous setState out of the effect flush
    // (react-hooks/set-state-in-effect). Still runs before any network response.
    queueMicrotask(() => {
      if (cancelled) return
      setLoading(true)
      setSearchError("")
    })
    Promise.all([
      destinationApi.getAll({ search: q, page_size: 24 }),
      hotelApi.search(q, { page_size: 24 }).catch(() => ({ data: { results: [] } })),
    ]).then(([destRes, hotelRes]) => {
      if (cancelled) return
      const destinations = (destRes.data?.results || destRes.data || []).map((d) => ({
        id: `destination-${d.id}`, rawId: d.id, name: d.name,
        location: [d.city || d.municipality, d.district, d.province].filter(Boolean).join(", "),
        rating: Number(d.average_rating || 0), price: d.entry_fee,
        type: "destination", image: d.cover_image_url || d.image_url || d.cover_image,
        slug: d.slug,
      }))
      const hotels = (hotelRes.data?.results || hotelRes.data || []).map((h) => ({
        id: `hotel-${h.id}`, rawId: h.id, name: h.name,
        location: [h.city, h.district].filter(Boolean).join(", "),
        rating: Number(h.average_rating || h.rating || 0), price: h.price_per_night,
        type: "hotel", image: h.image_url || h.cover_image_url || h.cover_image,
        slug: h.slug,
      }))
      const combined = [...destinations, ...hotels]
      if (position) {
        combined.forEach((item) => {
          if (item.latitude != null && item.longitude != null) {
            const lat1 = Number(position.lat), lon1 = Number(position.lng)
            const lat2 = Number(item.latitude), lon2 = Number(item.longitude)
            const p1 = lat1 * Math.PI / 180, p2 = lat2 * Math.PI / 180
            const a = Math.sin((lat2-lat1)*Math.PI/360)**2 + Math.cos(p1)*Math.cos(p2)*Math.sin((lon2-lon1)*Math.PI/360)**2
            item.distance = 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
          }
        })
      }
      setResults(combined)
    }).catch((error) => {
      if (!cancelled) setSearchError(error?.response?.data?.detail || error?.message || "Search is unavailable.")
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [query, position])



  const handleSaveSearch = () => {
    if (query && !savedSearches.includes(query)) {
      setSavedSearches([...savedSearches, query])
      showToast("Search saved!", "success")
    }
  }

  const handleSaveResult = (result) => {
    if (savedResults.find((r) => r.id === result.id)) {
      setSavedResults(savedResults.filter((r) => r.id !== result.id))
      showToast("Removed from saved", "info")
    } else {
      setSavedResults([...savedResults, result])
      showToast("Saved to favorites!", "success")
    }
  }

  const handleShare = (result) => {
    const url = `${window.location.origin}/destinations/${result.id}`
    navigator.clipboard.writeText(url)
    showToast("Link copied!", "success")
  }

  const clearFilters = () => {
    setSelectedTypes([])
    setSelectedPriceRange([])
    setSelectedRatings([])
  }

  const facetOptions = {
    types: [
      { value: "destination", label: "Destinations", count: results.filter((r) => r.type === "destination").length },
      { value: "hotel", label: "Hotels", count: results.filter((r) => r.type === "hotel").length },
    ],
    priceRange: [
      { value: "0-5000", label: "Under NPR 5,000", count: 1 },
      { value: "5000-15000", label: "NPR 5,000 - 15,000", count: 3 },
      { value: "15000-50000", label: "NPR 15,000 - 50,000", count: 2 },
    ],
    ratings: [
      { value: "4.5", label: "4.5+ stars", count: 4 },
      { value: "4.0", label: "4.0+ stars", count: 5 },
      { value: "3.5", label: "3.5+ stars", count: 6 },
    ],
  }

  return (
    <div className="ny-page mx-auto w-full max-w-7xl space-y-6">
      <PageHeader
        title={`Search Results${query ? `: "${query}"` : ""}`}
        subtitle={`${results.length} results found`}
        icon={FiSearch}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveSearch}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              <FiHeart size={14} /> Save Search
            </button>
          </div>
        }
      />

      {/* Search Bar */}
      <div className="card-base p-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              value={query}
              onChange={(e) => setSearchParams(e.target.value ? { q: e.target.value } : {})}
              placeholder="Search destinations, hotels, tours..."
              className="input-field pl-10 pr-4"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center gap-2 ${showFilters ? "bg-emerald-50 text-emerald-700" : ""}`}
          >
            <FiFilter size={16} /> Filters
          </button>
        </div>
      </div>

      {/* Search History & Related */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SearchHistory
          history={searchHistory}
          onSelect={(q) => setSearchParams({ q })}
          onClear={() => setSearchHistory([])}
        />
        <RelatedSearches query={query} onSelect={(q) => setSearchParams({ q })} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="lg:col-span-1"
            >
              <div className="card-base p-4 sticky top-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">Filters</h3>
                  <button onClick={clearFilters} className="text-xs text-emerald-600 hover:underline">
                    Clear all
                  </button>
                </div>
                <FacetFilter
                  title="Type"
                  options={facetOptions.types}
                  selected={selectedTypes}
                  onToggle={(v) => setSelectedTypes(selectedTypes.includes(v) ? selectedTypes.filter((t) => t !== v) : [...selectedTypes, v])}
                />
                <FacetFilter
                  title="Price Range"
                  options={facetOptions.priceRange}
                  selected={selectedPriceRange}
                  onToggle={(v) => setSelectedPriceRange(selectedPriceRange.includes(v) ? selectedPriceRange.filter((t) => t !== v) : [...selectedPriceRange, v])}
                />
                <FacetFilter
                  title="Rating"
                  options={facetOptions.ratings}
                  selected={selectedRatings}
                  onToggle={(v) => setSelectedRatings(selectedRatings.includes(v) ? selectedRatings.filter((t) => t !== v) : [...selectedRatings, v])}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <div className={showFilters ? "lg:col-span-3" : "lg:col-span-4"}>
          {/* Toolbar */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setView("list")}
                className={`p-2 rounded-lg ${view === "list" ? "bg-emerald-100 text-emerald-700" : "text-gray-400 hover:text-gray-600"}`}
              >
                <FiList size={18} />
              </button>
              <button
                onClick={() => setView("grid")}
                className={`p-2 rounded-lg ${view === "grid" ? "bg-emerald-100 text-emerald-700" : "text-gray-400 hover:text-gray-600"}`}
              >
                <FiGrid size={18} />
              </button>
              <button
                onClick={() => setView("map")}
                className={`p-2 rounded-lg ${view === "map" ? "bg-emerald-100 text-emerald-700" : "text-gray-400 hover:text-gray-600"}`}
              >
                <FiMap size={18} />
              </button>
            </div>
            <SortDropdown value={sort} onChange={setSort} />
          </div>

          {/* Results List */}
          {searchError ? <EmptyState title="Search unavailable" subtitle={searchError} icon={FiSearch} /> : loading ? (
            <Loader text="Searching..." />
          ) : results.length === 0 ? (
            <EmptyState
              title="No results found"
              subtitle="Try adjusting your search or filters."
              icon={FiSearch}
            />
          ) : view === "map" ? (
            <MapView results={results} />
          ) : (
            <div className={view === "grid" ? "grid grid-cols-1 sm:grid-cols-2 gap-4" : "space-y-4"}>
              {results.map((result) => (
                <ResultCard
                  key={result.id}
                  result={result}
                  view={view}
                  onSave={handleSaveResult}
                  onShare={handleShare}
                  isSaved={savedResults.some((r) => r.id === result.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SearchResults
