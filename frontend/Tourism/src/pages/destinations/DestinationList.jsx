import { useEffect, useState, useCallback, useRef, useMemo } from "react"
import { useSearchParams, Link, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiChevronDown, FiFilter, FiMapPin, FiNavigation, FiPlus, FiX,
  FiGrid, FiList, FiCompass, FiShield, FiSun, FiCheck, FiArrowRight
} from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"

import DestinationCard from "../../components/cards/DestinationCard"
import DestinationCardSkeleton from "../../components/cards/DestinationCardSkeleton"
import SearchBar from "../../components/common/SearchBar"
import Pagination from "../../components/common/Pagination"
import Breadcrumbs from "../../components/common/Breadcrumbs"
import EmptyState from "../../components/common/EmptyState"
import ErrorState from "../../components/ui/ErrorState"

import useGeolocation from "../../hooks/useGeolocation"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import usePublicConfig from "../../hooks/usePublicConfig"
import { CMSExtras } from "../../components/cms/CMSBlock"

// Category values are sent to the existing catalogue API; the presentation
// below deliberately uses one restrained visual language.
const PAGE_SIZE = 12

// Top-level type chips
const TYPE_OPTIONS = [
  { label: "Attractions", value: "attraction" },
  { label: "Hotels & stays", value: "hotel" },
  { label: "All places", value: "all" },
]

const NEPAL_PROVINCES = [
  { id: "", label: "All Provinces" },
  { id: "Bagmati", label: "Bagmati" },
  { id: "Gandaki", label: "Gandaki" },
  { id: "Koshi", label: "Koshi" },
  { id: "Lumbini", label: "Lumbini" },
  { id: "Karnali", label: "Karnali" },
  { id: "Sudurpashchim", label: "Sudurpashchim" },
  { id: "Madhesh", label: "Madhesh" },
]

const ALTITUDE_TIERS = [
  { id: "all", label: "All Altitudes" },
  { id: "low", label: "🌿 Lowlands (<1,000m)" },
  { id: "mid", label: "⛰️ Mid-Hills (1,000–2,500m)" },
  { id: "high", label: "🏔️ High Himalaya (>2,500m)" },
]

// Fine-grained category chips
const CATEGORY_CHIPS = [
  { label: "All", value: "", icon: "✨" },
  { label: "Mountains", value: "mountains", icon: "🏔️" },
  { label: "Hills", value: "hills", icon: "⛰️" },
  { label: "Trekking", value: "trekking", icon: "🥾" },
  { label: "Lakes", value: "lakes", icon: "🌊" },
  { label: "Rivers", value: "rivers", icon: "🏞️" },
  { label: "Waterfalls", value: "waterfalls", icon: "💧" },
  { label: "Caves", value: "caves", icon: "🕳️" },
  { label: "Viewpoints", value: "viewpoints", icon: "🔭" },
  { label: "Valleys", value: "valleys", icon: "🌄" },
  { label: "Temples", value: "temples", icon: "🛕" },
  { label: "Buddhist Sites", value: "buddhist-sites", icon: "☸️" },
  { label: "Pilgrimage", value: "pilgrimage", icon: "🙏" },
  { label: "Heritage", value: "heritage", icon: "🏛️" },
  { label: "Museums", value: "museums", icon: "🖼️" },
  { label: "Wildlife", value: "wildlife", icon: "🐅" },
  { label: "Bird Watching", value: "bird-watching", icon: "🦜" },
  { label: "Forests", value: "forests", icon: "🌳" },
  { label: "National Parks", value: "eco-tourism", icon: "🌿" },
  { label: "Villages", value: "villages", icon: "🏡" },
  { label: "Cities", value: "cities", icon: "🏙️" },
  { label: "Tea & Coffee", value: "tea-coffee", icon: "🍃" },
  { label: "Adventure", value: "adventure", icon: "🧗" },
  { label: "Air Sports", value: "air-sports", icon: "🪂" },
  { label: "Water Sports", value: "water-sports", icon: "🚣" },
  { label: "Camping", value: "camping", icon: "⛺" },
  { label: "Cycling", value: "cycling", icon: "🚴" },
  { label: "Hot Springs", value: "hot-springs", icon: "♨️" },
  { label: "Winter/Snow", value: "winter", icon: "❄️" },
  { label: "Festivals", value: "festivals", icon: "🎉" },
  { label: "Culture", value: "culture", icon: "🎭" },
  { label: "Food", value: "food-culinary", icon: "🍛" },
  { label: "Shopping", value: "shopping", icon: "🛍️" },
  { label: "Scenic Routes", value: "scenic-routes", icon: "🛣️" },
  { label: "Natural Wonders", value: "natural-wonders", icon: "🌟" },
]

const PRIMARY_CATEGORY_KEYS = new Set(["", "mountains", "trekking", "lakes", "temples", "heritage", "wildlife", "cities"])

const CHIP_TO_PARAMS = {}
CATEGORY_CHIPS.forEach((c) => {
  if (c.value) CHIP_TO_PARAMS[c.value] = { category: c.value }
})

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("")

function chipToQuery(chip) {
  return CHIP_TO_PARAMS[chip] || {}
}

export default function DestinationList() {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const { extras } = usePublicConfig().pageCMS("destinations", ["intro", "search", "featured"])
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const initialQuery = searchParams.get("q") || ""
  const initialLetter = searchParams.get("letter") || ""
  const initialChip = searchParams.get("cat") || ""
  const initialType = searchParams.get("type") || "attraction"
  const urlState = searchParams.toString()

  const [destinations, setDestinations] = useState([])
  const [featuredDestinations, setFeaturedDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(parseInt(searchParams.get("page") || "1", 10))
  const [categoryChip, setCategoryChip] = useState(initialChip)
  const [showAllCategories, setShowAllCategories] = useState(Boolean(initialChip && !PRIMARY_CATEGORY_KEYS.has(initialChip)))
  const [type, setType] = useState(initialType)
  const [query, setQuery] = useState(initialQuery)
  const [letter, setLetter] = useState(initialLetter)
  const [favoriteMap, setFavoriteMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [reloadNonce, setReloadNonce] = useState(0)
  const [researching, setResearching] = useState(false)
  const requestSequence = useRef(0)
  const [didYouMean, setDidYouMean] = useState(null)
  const [isGpsSorted, setIsGpsSorted] = useState(false)
  const [viewMode, setViewMode] = useState("grid")
  const [selectedProvince, setSelectedProvince] = useState("")
  const [altitudeTier, setAltitudeTier] = useState("all")
  const [compareList, setCompareList] = useState([])
  const [showCompareModal, setShowCompareModal] = useState(false)

  const handleToggleCompare = (destination) => {
    setCompareList((prev) => {
      const exists = prev.some((d) => d.id === destination.id)
      if (exists) {
        return prev.filter((d) => d.id !== destination.id)
      }
      if (prev.length >= 3) {
        showToast("You can compare up to 3 destinations at once.", "info")
        return prev
      }
      return [...prev, destination]
    })
  }

  const displayedDestinations = useMemo(() => {
    return destinations.filter((d) => {
      if (selectedProvince && d.province && !d.province.toLowerCase().includes(selectedProvince.toLowerCase())) {
        return false
      }
      if (altitudeTier !== "all") {
        const alt = Number(d.altitude) || 0
        if (altitudeTier === "low" && alt >= 1000) return false
        if (altitudeTier === "mid" && (alt < 1000 || alt > 2500)) return false
        if (altitudeTier === "high" && alt <= 2500) return false
      }
      return true
    })
  }, [destinations, selectedProvince, altitudeTier])

  // Keep browser back/forward and same-path query navigation authoritative.
  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams(urlState)
      const nextPage = Number.parseInt(params.get("page") || "1", 10)
      setQuery(params.get("q") || "")
      setLetter(params.get("letter") || "")
      const nextCategory = params.get("cat") || ""
      setCategoryChip(nextCategory)
      setShowAllCategories(Boolean(nextCategory && !PRIMARY_CATEGORY_KEYS.has(nextCategory)))
      setType(params.get("type") || "attraction")
      setPage(Number.isFinite(nextPage) && nextPage > 0 ? nextPage : 1)
    }, 0)
    return () => clearTimeout(timer)
  }, [urlState])

  const { position, locating, error: locationError, retry: requestLocation, clear: clearLocation } = useGeolocation({ auto: false })

  // Fetch featured destinations
  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    destinationApi.getDestinations({ featured: true, page_size: 6, limit: 6 })
      .then(({ data }) => {
        const list = data.results || data || []
        setFeaturedDestinations(Array.isArray(list) ? list : [])
      })
      .catch(() => setFeaturedDestinations([]))
    }, 0)
    return () => clearTimeout(t)
  }, [])

  // Sync URL with filter state
  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    const sp = new URLSearchParams()
    if (query) sp.set("q", query)
    if (letter) sp.set("letter", letter)
    if (categoryChip) sp.set("cat", categoryChip)
    if (type && type !== "attraction") sp.set("type", type)
    if (page > 1) sp.set("page", String(page))
    setSearchParams(sp, { replace: true })
    }, 0)
    return () => clearTimeout(t)
  }, [query, letter, categoryChip, type, page, setSearchParams])

  // Fetch destinations — GPS proximity nearest first when position active & no explicit search query.
  useEffect(() => {
    // Deferred one tick keeps synchronous state updates outside the effect flush.
    const timer = setTimeout(() => {
      const currentRequest = ++requestSequence.current
      setLoading(true)
      setLoadError("")
      setDidYouMean(null)

      const chipParams = chipToQuery(categoryChip)
      const isCurrent = () => currentRequest === requestSequence.current

      const applyResults = (data, sorted = false) => {
        if (!isCurrent()) return
        const results = data?.results || data || []
        const list = Array.isArray(results) ? results : []
        setDestinations(list)
        setTotalPages(data?.total_pages || data?.totalPages || Math.ceil((data?.count || list.length) / PAGE_SIZE) || 1)
        setTotalCount(data?.count || list.length)
        setIsGpsSorted(sorted)
        setLoading(false)
        return list
      }

      const fallbackFetch = () => {
        if (!isCurrent()) return
        setIsGpsSorted(false)
        const params = { page, limit: PAGE_SIZE, ...(type !== "all" ? { type } : {}), ordering: "name" }
        if (chipParams.category) params.category = chipParams.category
        if (query) {
          params.search = query
          params.q = query
        }
        if (chipParams.search && !query) params.search = chipParams.search
        if (letter) params.letter = letter
        if (position) {
          params.latitude = position.lat
          params.longitude = position.lng
        }

        destinationApi.getAll(params)
          .then(({ data }) => {
            const list = applyResults(data)
            if (query && list.length === 0 && !letter && isCurrent()) {
              destinationApi.autocomplete(query, { type })
                .then((res) => {
                  if (isCurrent() && res.data?.did_you_mean) setDidYouMean(res.data.did_you_mean)
                })
                .catch(() => {})
            }
          })
          .catch(() => {
            if (!isCurrent()) return
            setDestinations([])
            setTotalPages(1)
            setTotalCount(0)
            setLoadError("We couldn't load destinations right now. Check your connection and try again.")
            setLoading(false)
          })
      }

      if (position?.lat && position?.lng && !query && !letter && !categoryChip && type !== "hotel") {
        setIsGpsSorted(true)
        destinationApi.nearby(position.lat, position.lng, { radius_km: 250, page, limit: PAGE_SIZE, type })
          .then(({ data }) => {
            const list = data?.results || data || []
            if (Array.isArray(list) && list.length) applyResults(data, true)
            else fallbackFetch()
          })
          .catch(() => fallbackFetch())
      } else {
        fallbackFetch()
      }
    }, 0)
    return () => clearTimeout(timer)
  }, [page, categoryChip, type, query, letter, position, reloadNonce])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    if (!isAuthenticated) {
      setFavoriteMap({})
      return
    }
    userApi
      .getFavorites()
      .then(({ data }) => {
        const list = data.results || data || []
        const map = {}
        list.forEach((fav) => {
          map[fav.destination] = fav.id
        })
        setFavoriteMap(map)
      })
      .catch(() => {})
    }, 0)
    return () => clearTimeout(t)
  }, [isAuthenticated])

  const handleToggleFavorite = async (destId) => {
    if (!isAuthenticated) {
      return showToast("Please login to save favorites", "info")
    }
    const recordId = favoriteMap[destId]
    try {
      if (recordId) {
        await userApi.removeFavorite(recordId)
        setFavoriteMap((prev) => {
          const next = { ...prev }
          delete next[destId]
          return next
        })
        showToast("Removed from favorites", "info")
      } else {
        const { data } = await userApi.addFavorite(destId)
        setFavoriteMap((prev) => ({ ...prev, [destId]: data.id }))
        showToast("Saved to favorites ❤️", "success")
      }
    } catch {
      showToast("Could not update favorites", "error")
    }
  }

  const handleResearchQuery = async () => {
    if (!query) return
    setResearching(true)
    try {
      const { data } = await destinationApi.researchDestination(query)
      if (data.slug) {
        showToast(`A matching record was found for "${data.name}". Opening details…`, "success")
        navigate(`/destinations/${data.slug}`)
      } else {
        showToast(data.message || "Destination researched!", "info")
      }
    } catch {
      showToast("Research service error. Try another place name.", "error")
    } finally {
      setResearching(false)
    }
  }

  const fetchSuggestions = useCallback(async (q, signal) => {
    try {
      const res = await destinationApi.autocomplete(q, { type: type === "hotel" ? "hotel" : "attraction" })
      if (signal?.aborted) return []
      return res.data?.results || res.data || []
    } catch {
      return []
    }
  }, [type])

  // Category values are sent to the existing catalogue API; the presentation
  // below deliberately uses one restrained visual language.
  // Filter out any raw admin placeholder texts from extras
  const cleanExtras = (extras || []).filter((sec) => {
    const body = String(sec?.body || "").toLowerCase()
    return !body.includes("managed from") && !body.includes("configure featured")
  })
  const visibleCategoryChips = showAllCategories
    ? CATEGORY_CHIPS
    : CATEGORY_CHIPS.filter((chip) => PRIMARY_CATEGORY_KEYS.has(chip.value))

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <Breadcrumbs items={[{ label: "Destinations Explorer", to: "/destinations" }]} />

      <header className="flex flex-col gap-5 border-b border-[var(--ny-border)] pb-6 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="ny-kicker">Himalayan atlas</span>
            {isGpsSorted && <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--ny-soft-green)] px-3 py-1 text-xs font-semibold text-[var(--ny-green)]"><FiNavigation size={13} aria-hidden="true" /> Nearest first</span>}
          </div>
          <h1 className="mt-3 flex items-center gap-2"><FiMapPin className="text-[var(--ny-green)]" aria-hidden="true" /> Explore Nepal destinations</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ny-text-secondary)]">Discover recorded temples, lakes, Himalayan viewpoints, national parks and heritage places across Nepal's seven provinces.</p>
        </div>
        <Link to="/destinations/submit" className="ny-btn ny-btn-secondary shrink-0"><FiPlus size={16} aria-hidden="true" /> Submit a place</Link>
      </header>

      <section className="ny-panel p-4 sm:p-5" aria-label="Destination filters">
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Place type">
          {TYPE_OPTIONS.map((opt) => (
            <button key={opt.value} type="button" onClick={() => { setType(opt.value); setPage(1); setCategoryChip("") }} className={`ny-btn min-h-11 px-4 text-sm ${type === opt.value ? "ny-btn-primary" : "ny-btn-secondary"}`} aria-pressed={type === opt.value}>{opt.label}</button>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_auto_auto] lg:items-center">
          <SearchBar className="min-w-0 md:col-span-2 lg:col-span-1" defaultValue={initialQuery} placeholder="Search destinations, districts or places" fetchSuggestions={fetchSuggestions} onSearch={(val) => { setQuery(val); setPage(1); setLetter("") }} />
          {type !== "hotel" && <button type="button" onClick={() => setShowAllCategories((value) => !value)} className="ny-btn ny-btn-secondary min-h-11 justify-center whitespace-nowrap" aria-expanded={showAllCategories} aria-controls="destination-category-filters"><FiFilter size={16} aria-hidden="true" /> {showAllCategories ? "Fewer filters" : "More filters"} <FiChevronDown size={15} className={showAllCategories ? "rotate-180 transition" : "transition"} aria-hidden="true" /></button>}
          <button type="button" onClick={position ? clearLocation : requestLocation} disabled={locating} className="ny-btn ny-btn-ghost min-h-11 justify-center whitespace-nowrap text-xs"><FiNavigation size={15} aria-hidden="true" />{locating ? "Finding location…" : position ? "Turn off nearby" : "Use my location"}</button>
        </div>
        {locationError && <p className="mt-3 text-xs text-[var(--ny-text-muted)]">Location was not shared. You can browse all destinations or try again.</p>}
        {type !== "hotel" && <div id="destination-category-filters" className="mt-4 border-t border-[var(--ny-border)] pt-4"><div className={`${showAllCategories ? "max-w-full flex-nowrap overflow-x-auto no-scrollbar" : "flex flex-wrap"} gap-2`} role="group" aria-label="Destination categories">{visibleCategoryChips.map((c) => <button key={c.value} type="button" onClick={() => { setCategoryChip(c.value); setPage(1); setLetter("") }} className={`shrink-0 rounded-full border min-h-11 px-3.5 py-2 text-xs font-semibold transition ${categoryChip === c.value ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white" : "border-[var(--ny-border)] bg-white text-[var(--ny-text-secondary)] hover:border-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"}`} aria-pressed={categoryChip === c.value}>{c.label}</button>)}</div>{!showAllCategories && <p className="mt-3 text-xs text-[var(--ny-text-muted)]">Showing the most useful categories first. Use More filters for the complete catalogue.</p>}</div>}

        {/* Province Quick Filter Bar */}
        <div className="mt-3 pt-3 border-t border-[var(--ny-border)] flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 text-xs">
          <span className="font-bold text-slate-500 shrink-0 text-[11px] mr-1">Province:</span>
          {NEPAL_PROVINCES.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelectedProvince(p.id)}
              className={`shrink-0 px-2.5 py-1 rounded-full text-xs font-bold transition ${
                selectedProvince === p.id
                  ? "bg-emerald-800 text-white shadow-2xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Altitude Tier & Layout View Switcher */}
        <div className="mt-3 pt-3 border-t border-[var(--ny-border)] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-bold text-slate-500 text-[11px] mr-1">Altitude Zone:</span>
            {ALTITUDE_TIERS.map((a) => (
              <button
                key={a.id}
                type="button"
                onClick={() => setAltitudeTier(a.id)}
                className={`px-2.5 py-1 rounded-full font-bold transition ${
                  altitudeTier === a.id
                    ? "bg-amber-600 text-white shadow-2xs"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {a.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
            <button
              type="button"
              onClick={() => setViewMode("grid")}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                viewMode === "grid" ? "bg-white text-emerald-900 shadow-2xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FiGrid className="inline mr-1" /> Grid
            </button>
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                viewMode === "list" ? "bg-white text-emerald-900 shadow-2xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FiList className="inline mr-1" /> Compact List
            </button>
          </div>
        </div>
      </section>

      {type === "attraction" && !query && <div className="ny-horizontal-scroll no-scrollbar -mx-1 w-full overflow-x-auto px-1 pb-1" aria-label="Browse destinations alphabetically"><div className="flex w-max items-center gap-1.5"><span className="mr-1 whitespace-nowrap text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-muted)]">A–Z</span><button type="button" onClick={() => { setLetter(""); setPage(1) }} className={`grid h-11 min-w-11 place-items-center rounded-[var(--ny-radius-sm)] px-2 text-xs font-semibold ${letter === "" ? "bg-[var(--ny-green)] text-white" : "text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"}`} aria-label="Show all destinations">All</button>{ALPHABET.map((L) => <button key={L} type="button" onClick={() => { setLetter(L); setPage(1) }} className={`grid h-11 min-w-11 place-items-center rounded-[var(--ny-radius-sm)] px-2 text-xs font-semibold ${letter === L ? "bg-[var(--ny-green)] text-white" : "text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"}`} aria-label={`Show destinations starting with ${L}`}>{L}</button>)}</div></div>}

      {!loading && !loadError && <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-[var(--ny-text-secondary)]"><span>Showing <strong className="text-[var(--ny-text)]">{totalCount.toLocaleString()}</strong> places{isGpsSorted ? " nearest to your location" : ""}{query ? ` for “${query}”` : ""}{letter ? ` starting with “${letter}”` : ""}</span>{(query || letter || categoryChip) && <button type="button" onClick={() => { setQuery(""); setLetter(""); setCategoryChip(""); setPage(1) }} className="inline-flex min-h-11 items-center gap-1 font-semibold text-[var(--ny-green)] hover:underline"><FiX size={14} aria-hidden="true" /> Clear filters</button>}</div>}

      {/* Results View */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => <DestinationCardSkeleton key={i} />)}
        </div>
      ) : loadError ? (
        <ErrorState title="Could not load destinations" message={loadError} onRetry={() => setReloadNonce((value) => value + 1)} />
      ) : displayedDestinations.length > 0 ? (
        <div className="space-y-8">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="text-xl sm:text-2xl font-black">
              {query ? `Results for “${query}”` : letter ? `Destinations starting with “${letter}”` : "All Nepal destinations"}
            </h2>
            <p className="text-xs text-gray-500 font-bold">
              {displayedDestinations.length} of {destinations.length} places shown{isGpsSorted ? " · nearest first" : ""}
            </p>
          </div>

          {/* Grid View */}
          {viewMode === "grid" && (
            <motion.div
              layout
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3 gap-6"
            >
              {displayedDestinations.map((d) => (
                <DestinationCard
                  key={d.id}
                  destination={d}
                  isFavorite={!!favoriteMap[d.id]}
                  onToggleFavorite={() => handleToggleFavorite(d.id)}
                  onCompare={handleToggleCompare}
                  isCompared={compareList.some((c) => c.id === d.id)}
                />
              ))}
            </motion.div>
          )}

          {/* Compact List View */}
          {viewMode === "list" && (
            <div className="space-y-3">
              {displayedDestinations.map((d) => {
                const isCompared = compareList.some((c) => c.id === d.id)
                return (
                  <div
                    key={d.id}
                    className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="flex items-start sm:items-center gap-3 min-w-0">
                      <div className="w-14 h-14 rounded-xl bg-slate-100 overflow-hidden shrink-0">
                        {d.cover_image_url || d.cover_image ? (
                          <img
                            src={d.cover_image_url || d.cover_image}
                            alt={d.name}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-xl">🏔️</div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-sm text-slate-900 truncate">{d.name}</h4>
                          {d.category_name && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[10px] font-bold">
                              {d.category_name}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 truncate mt-0.5">
                          {[d.district, d.province].filter(Boolean).join(", ")}
                        </p>
                        <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-600">
                          {d.altitude && <span className="font-semibold text-amber-800">⛰️ {d.altitude}m</span>}
                          {Number(d.average_rating) > 0 && <span className="text-amber-500 font-bold">★ {Number(d.average_rating).toFixed(1)}</span>}
                          {d.best_time_to_visit && <span>Best: {d.best_time_to_visit}</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                      <button
                        type="button"
                        onClick={() => handleToggleCompare(d)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                          isCompared ? "bg-emerald-700 text-white" : "border border-slate-300 hover:bg-slate-50 text-slate-700"
                        }`}
                      >
                        {isCompared ? "✓ Compared" : "+ Compare"}
                      </button>
                      <Link
                        to={`/destinations/${d.slug}`}
                        className="px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs flex items-center gap-1"
                      >
                        Explore <FiArrowRight size={13} />
                      </Link>
                      <Link
                        to={`/navigation?dest=${encodeURIComponent(d.name)}`}
                        className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs flex items-center gap-1"
                        title="Road navigation"
                      >
                        <FiNavigation size={13} /> Route
                      </Link>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex justify-center pt-4">
              <Pagination
                currentPage={page}
                totalPages={Math.min(totalPages, 100)}
                onPageChange={(p) => { setPage(p); window.scrollTo({ top: 0, behavior: "smooth" }) }}
              />
            </div>
          )}
        </div>
      ) : (
        <>
          {didYouMean && <div className="ny-panel mb-4 flex flex-wrap items-center justify-between gap-3 p-4 text-sm"><span className="text-[var(--ny-text-secondary)]">Did you mean <strong className="text-[var(--ny-text)]">{didYouMean.name}</strong>?</span><button type="button" onClick={() => { setQuery(didYouMean.name); setDidYouMean(null); setPage(1) }} className="ny-btn ny-btn-secondary min-h-10 px-3">Use suggestion</button></div>}
          <EmptyState
            title={query || letter || categoryChip || selectedProvince || altitudeTier !== "all" ? "No destinations match these filters" : "No destinations are available yet"}
            subtitle="Try clearing a filter or searching for another destination."
            action={<button type="button" onClick={() => { setQuery(""); setLetter(""); setCategoryChip(""); setSelectedProvince(""); setAltitudeTier("all"); setPage(1) }} className="ny-btn ny-btn-primary">Clear all filters</button>}
            secondaryAction={<Link to="/destinations" className="ny-btn ny-btn-secondary">Browse all destinations</Link>}
          />
        </>
      )}

      {/* Floating Comparison Dock */}
      {compareList.length > 0 && (
        <div className="fixed bottom-4 left-4 right-4 z-40 max-w-2xl mx-auto p-3.5 rounded-2xl bg-slate-900 text-white shadow-2xl border border-slate-700 flex flex-wrap items-center justify-between gap-3 animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-black uppercase tracking-wider text-amber-400">⚖️ Compare ({compareList.length}/3):</span>
            <div className="flex items-center gap-1.5 overflow-x-auto max-w-[280px]">
              {compareList.map((c) => (
                <span key={c.id} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-200">
                  <span className="truncate max-w-[90px]">{c.name}</span>
                  <button type="button" onClick={() => handleToggleCompare(c)} className="text-slate-400 hover:text-white">✕</button>
                </span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowCompareModal(true)}
              className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs shadow-md"
            >
              Compare Side-by-Side
            </button>
            <button
              type="button"
              onClick={() => setCompareList([])}
              className="px-2.5 py-2 text-xs font-bold text-slate-400 hover:text-white"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Comparison Modal */}
      <AnimatePresence>
        {showCompareModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6 shadow-2xl border border-slate-200 space-y-6"
            >
              <div className="flex items-center justify-between border-b pb-4">
                <div>
                  <span className="text-[10px] font-black uppercase tracking-widest text-emerald-800">Himalayan Destinations Matrix</span>
                  <h3 className="text-xl font-black text-slate-900 mt-1">Side-by-Side Comparison</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCompareModal(false)}
                  className="p-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600"
                >
                  <FiX size={18} />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {compareList.map((item) => (
                  <div key={item.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="h-32 rounded-xl overflow-hidden bg-slate-200 mb-3">
                        {item.cover_image_url || item.cover_image ? (
                          <img src={item.cover_image_url || item.cover_image} alt={item.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-3xl">🏔️</div>
                        )}
                      </div>
                      <h4 className="font-black text-base text-slate-900">{item.name}</h4>
                      <p className="text-xs text-slate-500">{[item.district, item.province].filter(Boolean).join(", ")}</p>

                      <div className="space-y-2 mt-4 text-xs">
                        <div className="flex justify-between border-b pb-1">
                          <span className="text-slate-500">Altitude</span>
                          <span className="font-bold text-amber-800">{item.altitude ? `${item.altitude}m` : "Sub-alpine (<1500m)"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1">
                          <span className="text-slate-500">Best Season</span>
                          <span className="font-bold text-slate-800">{item.best_time_to_visit || "Autumn / Spring"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1">
                          <span className="text-slate-500">Entry / Budget</span>
                          <span className="font-bold text-emerald-800">{item.budget_estimate ? `NPR ${item.budget_estimate}` : item.entry_fee || "Standard Fee"}</span>
                        </div>
                        <div className="flex justify-between border-b pb-1">
                          <span className="text-slate-500">Safety Risk</span>
                          <span className="font-bold text-slate-800">{item.risk_level || "Low"}</span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2 pt-2 border-t">
                      <Link
                        to={`/destinations/${item.slug}`}
                        className="w-full py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs text-center block"
                      >
                        Explore Destination →
                      </Link>
                      <Link
                        to={`/navigation?dest=${encodeURIComponent(item.name)}`}
                        className="w-full py-2 rounded-xl border border-slate-300 hover:bg-white text-slate-800 font-bold text-xs text-center block"
                      >
                        Navigate Route ➔
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {featuredDestinations.length > 0 && !query && !letter && (
        <section className="space-y-5 border-t border-[var(--ny-border)] pt-10" aria-labelledby="featured-destinations-title">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div><p className="ny-kicker">A closer look</p><h2 id="featured-destinations-title" className="mt-2">Featured destinations</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">A few places currently marked for discovery.</p></div>
            <Link to="/recommendation" className="text-sm font-semibold text-[var(--ny-green)] hover:underline">Get recommendations →</Link>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3">{featuredDestinations.slice(0, 3).map((d) => <DestinationCard key={`featured-${d.id}`} destination={d} />)}</div>
        </section>
      )}

      {cleanExtras?.length > 0 && <CMSExtras sections={cleanExtras} />}
    </div>
  )
}
