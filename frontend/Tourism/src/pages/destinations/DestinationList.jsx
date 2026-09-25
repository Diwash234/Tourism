import { useEffect, useState, useCallback, useRef } from "react"
import { useSearchParams, Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { FiChevronDown, FiFilter, FiMapPin, FiNavigation, FiPlus, FiX } from "react-icons/fi"

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
      </section>

      {type === "attraction" && !query && <div className="ny-horizontal-scroll no-scrollbar -mx-1 w-full overflow-x-auto px-1 pb-1" aria-label="Browse destinations alphabetically"><div className="flex w-max items-center gap-1.5"><span className="mr-1 whitespace-nowrap text-xs font-bold uppercase tracking-[0.08em] text-[var(--ny-text-muted)]">A–Z</span><button type="button" onClick={() => { setLetter(""); setPage(1) }} className={`grid h-11 min-w-11 place-items-center rounded-[var(--ny-radius-sm)] px-2 text-xs font-semibold ${letter === "" ? "bg-[var(--ny-green)] text-white" : "text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"}`} aria-label="Show all destinations">All</button>{ALPHABET.map((L) => <button key={L} type="button" onClick={() => { setLetter(L); setPage(1) }} className={`grid h-11 min-w-11 place-items-center rounded-[var(--ny-radius-sm)] px-2 text-xs font-semibold ${letter === L ? "bg-[var(--ny-green)] text-white" : "text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]"}`} aria-label={`Show destinations starting with ${L}`}>{L}</button>)}</div></div>}

      {!loading && !loadError && <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-[var(--ny-text-secondary)]"><span>Showing <strong className="text-[var(--ny-text)]">{totalCount.toLocaleString()}</strong> places{isGpsSorted ? " nearest to your location" : ""}{query ? ` for “${query}”` : ""}{letter ? ` starting with “${letter}”` : ""}</span>{(query || letter || categoryChip) && <button type="button" onClick={() => { setQuery(""); setLetter(""); setCategoryChip(""); setPage(1) }} className="inline-flex min-h-11 items-center gap-1 font-semibold text-[var(--ny-green)] hover:underline"><FiX size={14} aria-hidden="true" /> Clear filters</button>}</div>}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => <DestinationCardSkeleton key={i} />)}
        </div>
      ) : loadError ? (
        <ErrorState title="Could not load destinations" message={loadError} onRetry={() => setReloadNonce((value) => value + 1)} />
      ) : destinations.length > 0 ? (
        <div className="space-y-8">
          {/* Section heading completes the page hierarchy:
              breadcrumb -> h1 (page) -> h2 (results) -> cards -> h2 (featured) */}
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="text-xl sm:text-2xl font-black">
              {query ? `Results for “${query}”` : letter ? `Destinations starting with “${letter}”` : "All Nepal destinations"}
            </h2>
            <p className="text-xs text-gray-500 font-bold">
              {destinations.length} shown{isGpsSorted ? " · nearest first" : ""}
            </p>
          </div>
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3 gap-6"
          >
            {destinations.map((d) => (
              <DestinationCard
                key={d.id}
                destination={d}
                isFavorite={!!favoriteMap[d.id]}
                onToggleFavorite={() => handleToggleFavorite(d.id)}
              />
            ))}
          </motion.div>

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
            title={query || letter || categoryChip ? "No destinations match these filters" : "No destinations are available yet"}
            subtitle={query || letter || categoryChip ? "Try a different search, clear a filter, or browse the complete catalogue." : "The live catalogue is still loading or has no published places for this view."}
            action={query ? <button type="button" onClick={handleResearchQuery} disabled={researching} className="ny-btn ny-btn-secondary">{researching ? "Checking…" : "Research this place"}</button> : (query || letter || categoryChip) && <button type="button" onClick={() => { setQuery(""); setLetter(""); setCategoryChip(""); setPage(1) }} className="ny-btn ny-btn-primary">Clear filters</button>}
            secondaryAction={<Link to="/destinations" className="ny-btn ny-btn-secondary">Browse all destinations</Link>}
          />
        </>
      )}

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
