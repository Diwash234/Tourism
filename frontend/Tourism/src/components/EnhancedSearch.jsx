import { useState, useEffect, useCallback, useRef } from "react"
import {
  FiSearch,
  FiFilter,
  FiStar,
  FiMapPin,
  FiCheckCircle,
  FiX,
  FiChevronDown,
  FiGrid,
  FiList,
} from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import Pagination from "./common/Pagination"

const DEBOUNCE_MS = 300
const PAGE_SIZE = 12

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "nature", label: "Nature" },
  { value: "cultural", label: "Cultural" },
  { value: "adventure", label: "Adventure" },
  { value: "religious", label: "Religious" },
  { value: "historical", label: "Historical" },
]

const DISTRICTS = [
  { value: "", label: "All Districts" },
  { value: "kathmandu", label: "Kathmandu" },
  { value: "pokhara", label: "Pokhara" },
  { value: "chitwan", label: "Chitwan" },
  { value: "lumbini", label: "Lumbini" },
  { value: "bhaktapur", label: "Bhaktapur" },
  { value: "lalitpur", label: "Lalitpur" },
]

const SORT_OPTIONS = [
  { value: "relevance", label: "Relevance" },
  { value: "rating", label: "Highest Rated" },
  { value: "distance", label: "Nearest" },
  { value: "popularity", label: "Most Popular" },
]

/**
 * Enhanced search component with autocomplete, filters, sorting,
 * paginated results grid, loading skeleton, and empty state.
 */
const EnhancedSearch = ({ onResultSelect, initialQuery = "" }) => {
  const [query, setQuery] = useState(initialQuery)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState("grid")
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Filter state
  const [category, setCategory] = useState("")
  const [district, setDistrict] = useState("")
  const [minRating, setMinRating] = useState(0)
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [sortBy, setSortBy] = useState("relevance")

  const debounceRef = useRef(null)
  const searchInputRef = useRef(null)

  // Fetch autocomplete suggestions
  const fetchSuggestions = useCallback(async (searchText) => {
    if (!searchText || searchText.length < 2) {
      setSuggestions([])
      return
    }
    try {
      const { data } = await axiosClient.get("/destinations/autocomplete/", {
        params: { q: searchText, limit: 5 },
      })
      setSuggestions(data?.results || data || [])
    } catch {
      setSuggestions([])
    }
  }, [])

  // Fetch search results
  const fetchResults = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        search: query,
        page,
        page_size: PAGE_SIZE,
        ordering: sortBy === "relevance" ? "" : sortBy,
      }
      if (category) params.category = category
      if (district) params.district = district
      if (minRating > 0) params.min_rating = minRating
      if (verifiedOnly) params.verified = true

      const { data } = await axiosClient.get("/destinations/", { params })
      setResults(data?.results || data || [])
      setTotalCount(data?.count || 0)
      setTotalPages(Math.ceil((data?.count || 0) / PAGE_SIZE))
    } catch (err) {
      setError(
        err?.response?.data?.message || "Search failed. Please try again later."
      )
    } finally {
      setLoading(false)
    }
  }, [query, page, category, district, minRating, verifiedOnly, sortBy])

  // Debounced search trigger
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      fetchResults()
      fetchSuggestions(query)
    }, DEBOUNCE_MS)
    return () => clearTimeout(debounceRef.current)
  }, [query, fetchResults, fetchSuggestions])

  // Reset page on filter change
  useEffect(() => {
    setPage(1)
  }, [category, district, minRating, verifiedOnly, sortBy, query])

  const handleSearch = (e) => {
    e.preventDefault()
    setShowSuggestions(false)
    fetchResults()
  }

  const clearFilters = () => {
    setCategory("")
    setDistrict("")
    setMinRating(0)
    setVerifiedOnly(false)
    setSortBy("relevance")
  }

  const hasActiveFilters = category || district || minRating > 0 || verifiedOnly

  return (
    <div className="ny-card p-5">
      {/* Search input with autocomplete */}
      <form onSubmit={handleSearch} className="relative mb-4">
        <div className="relative">
          <FiSearch size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-ny-text-muted" />
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Search destinations, hotels, activities..."
            className="input-field pl-11 pr-10 py-3 text-base"
            aria-label="Search"
          />
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("")
                setSuggestions([])
                searchInputRef.current?.focus()
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-ny-text-muted hover:text-ny-text"
              aria-label="Clear search"
            >
              <FiX size={18} />
            </button>
          )}
        </div>

        {/* Autocomplete suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white rounded-xl border border-ny-border shadow-lg overflow-hidden">
            {suggestions.map((item) => (
              <button
                key={item.id || item.slug}
                type="button"
                onMouseDown={() => {
                  setQuery(item.name || item.title)
                  setShowSuggestions(false)
                }}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-ny-soft-green transition-colors text-left"
              >
                <FiMapPin size={14} className="text-ny-text-muted flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ny-text truncate">{item.name || item.title}</p>
                  {item.district && (
                    <p className="text-xs text-ny-text-muted">{item.district}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Filter toggle and sort */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={`ny-btn ny-btn-sm ${showFilters ? "ny-btn-primary" : "ny-btn-secondary"}`}
        >
          <FiFilter size={14} />
          Filters
          {hasActiveFilters && (
            <span className="ml-1 w-5 h-5 rounded-full bg-ny-gold text-ny-green-deepest text-xs flex items-center justify-center font-bold">
              !
            </span>
          )}
          <FiChevronDown size={12} className={`transition-transform ${showFilters ? "rotate-180" : ""}`} />
        </button>

        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-field py-2 text-sm"
            aria-label="Sort by"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <div className="flex border border-ny-border rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={`p-2 ${viewMode === "grid" ? "bg-ny-green text-white" : "bg-white text-ny-text-muted"}`}
              aria-label="Grid view"
            >
              <FiGrid size={14} />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`p-2 ${viewMode === "list" ? "bg-ny-green text-white" : "bg-white text-ny-text-muted"}`}
              aria-label="List view"
            >
              <FiList size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="p-4 rounded-xl bg-ny-soft-green/50 border border-ny-border mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="ny-field-label" htmlFor="filter-category">Category</label>
              <select
                id="filter-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="input-field py-2 text-sm"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="ny-field-label" htmlFor="filter-district">District</label>
              <select
                id="filter-district"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="input-field py-2 text-sm"
              >
                {DISTRICTS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="ny-field-label" htmlFor="filter-rating">Min Rating</label>
              <select
                id="filter-rating"
                value={minRating}
                onChange={(e) => setMinRating(Number(e.target.value))}
                className="input-field py-2 text-sm"
              >
                <option value={0}>Any rating</option>
                <option value={3}>3+ stars</option>
                <option value={4}>4+ stars</option>
                <option value={4.5}>4.5+ stars</option>
              </select>
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer py-2">
                <input
                  type="checkbox"
                  checked={verifiedOnly}
                  onChange={(e) => setVerifiedOnly(e.target.checked)}
                  className="accent-ny-green w-4 h-4"
                />
                <span className="text-sm text-ny-text flex items-center gap-1">
                  <FiCheckCircle size={14} className="text-ny-green" /> Verified only
                </span>
              </label>
            </div>
          </div>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="mt-3 text-sm text-ny-green hover:text-ny-green-dark font-medium"
            >
              Clear all filters
            </button>
          )}
        </div>
      )}

      {/* Results count */}
      {totalCount > 0 && (
        <p className="text-sm text-ny-text-muted mb-3">
          {totalCount} result{totalCount !== 1 ? "s" : ""} found
        </p>
      )}

      {/* Loading skeleton */}
      {loading ? (
        <div className={`grid gap-4 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`} role="status" aria-label="Loading results">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-4 rounded-xl border border-ny-border">
              <div className="ny-skeleton h-40 w-full rounded-lg mb-3" />
              <div className="ny-skeleton h-5 w-3/4 mb-2" />
              <div className="ny-skeleton h-4 w-1/2 mb-1" />
              <div className="ny-skeleton h-4 w-1/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="ny-empty">
          <span className="ny-empty-icon"><FiSearch size={24} /></span>
          <h3>Search failed</h3>
          <p>{error}</p>
        </div>
      ) : results.length === 0 ? (
        <div className="ny-empty">
          <span className="ny-empty-icon"><FiSearch size={24} /></span>
          <h3>No results found</h3>
          <p>Try adjusting your search terms or filters.</p>
        </div>
      ) : (
        <>
          {/* Results grid/list */}
          <div className={`grid gap-4 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"}`}>
            {results.map((item) => (
              <button
                key={item.id || item.slug}
                type="button"
                onClick={() => onResultSelect?.(item)}
                className={`text-left p-4 rounded-xl border border-ny-border hover:border-ny-green/50 hover:shadow-md transition-all ${
                  viewMode === "list" ? "flex items-center gap-4" : ""
                }`}
              >
                {item.image && (
                  <img
                    src={item.image}
                    alt={item.name}
                    className={`rounded-lg object-cover ${viewMode === "list" ? "w-20 h-20 flex-shrink-0" : "w-full h-40 mb-3"}`}
                    loading="lazy"
                  />
                )}
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-bold text-ny-text truncate">{item.name}</h4>
                    {item.verified && (
                      <FiCheckCircle size={14} className="text-ny-green flex-shrink-0" />
                    )}
                  </div>
                  {item.district && (
                    <p className="text-xs text-ny-text-muted flex items-center gap-1 mb-1">
                      <FiMapPin size={10} /> {item.district}
                    </p>
                  )}
                  {item.rating && (
                    <div className="flex items-center gap-1">
                      <FiStar size={12} className="text-ny-gold fill-ny-gold" />
                      <span className="text-xs font-semibold text-ny-text">{item.rating}</span>
                      {item.review_count && (
                        <span className="text-xs text-ny-text-muted">({item.review_count})</span>
                      )}
                    </div>
                  )}
                  {item.category && (
                    <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-ny-soft-green text-ny-green font-medium">
                      {item.category}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  )
}

export default EnhancedSearch
