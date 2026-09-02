import { useEffect, useState, useCallback } from "react"
import { useSearchParams, Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { FiMapPin, FiPlus, FiSearch, FiStar } from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"

import DestinationCard from "../../components/cards/DestinationCard"
import DestinationCardSkeleton from "../../components/cards/DestinationCardSkeleton"
import SearchBar from "../../components/common/SearchBar"
import Pagination from "../../components/common/Pagination"
import Breadcrumbs from "../../components/common/Breadcrumbs"

import useGeolocation from "../../hooks/useGeolocation"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import usePublicConfig from "../../hooks/usePublicConfig"
import { CMSExtras } from "../../components/cms/CMSBlock"

// Nepal palette
const GREEN = "#1f6b4d"
const GREEN_DARK = "#174f38"
const TERRACOTTA = "#c2603a"
const GOLD = "#b8862f"
const WARM_BG = "#faf8f4"
const INK = "#1f3329"

const PAGE_SIZE = 12

// Top-level type chips
const TYPE_OPTIONS = [
  { label: "🏔️ Attractions", value: "attraction" },
  { label: "🏨 Hotels & Stays", value: "hotel" },
  { label: "🌐 All Places", value: "all" },
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
  const { showBlock, copy, extras } = usePublicConfig().pageCMS("destinations", ["intro", "search", "featured"])
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const initialQuery = searchParams.get("q") || ""
  const initialLetter = searchParams.get("letter") || ""
  const initialChip = searchParams.get("cat") || ""
  const initialType = searchParams.get("type") || "attraction"

  const [destinations, setDestinations] = useState([])
  const [featuredDestinations, setFeaturedDestinations] = useState([])
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(parseInt(searchParams.get("page") || "1", 10))
  const [categoryChip, setCategoryChip] = useState(initialChip)
  const [type, setType] = useState(initialType)
  const [query, setQuery] = useState(initialQuery)
  const [letter, setLetter] = useState(initialLetter)
  const [favoriteMap, setFavoriteMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [researching, setResearching] = useState(false)
  const [didYouMean, setDidYouMean] = useState(null)

  const { position } = useGeolocation()

  // Fetch featured destinations
  useEffect(() => {
    destinationApi.getDestinations({ featured: true, page_size: 6, limit: 6 })
      .then(({ data }) => {
        const list = data.results || data || []
        setFeaturedDestinations(Array.isArray(list) ? list : [])
      })
      .catch(() => setFeaturedDestinations([]))
  }, [])

  // Sync URL with filter state
  useEffect(() => {
    const sp = new URLSearchParams()
    if (query) sp.set("q", query)
    if (letter) sp.set("letter", letter)
    if (categoryChip) sp.set("cat", categoryChip)
    if (type && type !== "attraction") sp.set("type", type)
    if (page > 1) sp.set("page", String(page))
    setSearchParams(sp, { replace: true })
  }, [query, letter, categoryChip, type, page, setSearchParams])

  // Fetch destinations
  useEffect(() => {
    setLoading(true)

    const chipParams = chipToQuery(categoryChip)

    const params = {
      page,
      limit: PAGE_SIZE,
      type,
      ordering: "name",
    }

    if (chipParams.category) params.category = chipParams.category
    if (query) {
      params.search = query
      params.q = query
    }
    if (chipParams.search && !query) {
      params.search = chipParams.search
    }
    if (letter) {
      params.letter = letter
    }
    if (position) {
      params.latitude = position.lat
      params.longitude = position.lng
    }

    destinationApi
      .getAll(params)
      .then(({ data }) => {
        const results = data.results || data || []
        setDestinations(results)
        setTotalPages(
          data.total_pages ||
          data.totalPages ||
          Math.ceil((data.count || results.length) / PAGE_SIZE) ||
          1
        )
        setTotalCount(data.count || results.length)
        setDidYouMean(null)
        if (query && results.length === 0 && !letter) {
          destinationApi
            .autocomplete(query, { type })
            .then((res) => {
              const dym = res.data?.did_you_mean
              if (dym) setDidYouMean(dym)
            })
            .catch(() => {})
        }
      })
      .catch(() => {
        setDestinations([])
        setTotalPages(1)
        setTotalCount(0)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [page, categoryChip, type, query, letter, position])

  useEffect(() => {
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
        showToast(`Researched & verified "${data.name}"! Opening details...`, "success")
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

  const chipActive = "text-white shadow-md"
  const chipIdle = "bg-white text-[#1f6b4d] border border-[#1f6b4d]/30 hover:bg-[#1f6b4d]/5"
  const catActive = "bg-[#c2603a] text-white border border-[#c2603a] shadow"
  const catIdle = "bg-white text-[#1f3329] border border-[#1f6b4d]/20 hover:border-[#1f6b4d]/60"

  return (
    <div className="container-app py-6 sm:py-8 space-y-6 animate-fadeIn">
      <Breadcrumbs items={[{ label: "Destinations Explorer", to: "/destinations" }]} />

      {/* Hero header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#1f6b4d]/20 pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full text-xs font-black uppercase tracking-wider"
                style={{ background: `${TERRACOTTA}15`, color: TERRACOTTA }}>
            Himalayan Atlas
          </span>
          <h1 className="text-3xl md:text-4xl font-extrabold mt-1 flex items-center gap-2"
              style={{ color: INK, fontFamily: 'ui-serif, Georgia, "Noto Serif Devanagari", serif' }}>
            <FiMapPin style={{ color: TERRACOTTA }} /> {copy("intro", "title", "Explore Nepal")}
          </h1>
          <p className="text-gray-600 text-sm mt-1 max-w-xl">
            {copy("intro", "body", "Discover real temples, stupas, caves, lakes, Himalayan viewpoints, national parks and heritage sites across Nepal's 7 provinces.")}
          </p>
        </div>

        <Link
          to="/destinations/submit"
          className="px-5 py-2.5 rounded-xl text-white font-bold text-xs flex items-center gap-2 shadow-lg transition-all hover:scale-[1.02] shrink-0"
          style={{ background: GREEN, boxShadow: `0 10px 24px -10px ${GREEN}` }}
        >
          <FiPlus size={16} /> Submit a Place
        </Link>
      </div>

      {/* Featured Destinations Showcase */}
      {featuredDestinations.length > 0 && !query && !letter && (
        <section className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 text-white border border-emerald-800/40 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-emerald-800/60 pb-3">
            <div>
              <span className="px-3 py-0.5 rounded-full bg-amber-400 text-slate-950 text-[10px] font-black uppercase tracking-wider">
                Featured Destinations
              </span>
              <h2 className="text-xl sm:text-2xl font-black text-white mt-1">
                ⭐ Hand-Picked Top Nepal Attractions
              </h2>
              <p className="text-xs text-emerald-200">
                Verified high-rated destinations with real local photos, ratings, and instant travel guides.
              </p>
            </div>
            <Link to="/recommendation" className="text-xs text-amber-300 font-bold hover:underline">
              AI Recommendation Matching ➔
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {featuredDestinations.slice(0, 3).map((d) => (
              <div key={`feat-${d.id}`} className="rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-md flex flex-col justify-between p-4 space-y-3">
                <div className="h-40 relative rounded-xl overflow-hidden bg-slate-950">
                  <img src={d.cover_image_url || "/images/destinations/kathmandu/durbar-square.jpg"} alt={d.name} className="w-full h-full object-cover" />
                  <span className="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full bg-amber-400 text-slate-950 text-[10px] font-black uppercase shadow">
                    ⭐ Featured
                  </span>
                  <span className="absolute bottom-2.5 left-2.5 text-white font-extrabold text-sm drop-shadow">
                    {d.name}
                  </span>
                </div>

                <div className="space-y-1">
                  <p className="text-xs text-slate-400 flex items-center gap-1">
                    <FiMapPin size={12} className="text-amber-400" /> {d.display_city || d.district || "Nepal"}
                  </p>
                  <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                    {d.short_description || "Verified destination with rich cultural and natural heritage."}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-300">
                    ★ {d.average_rating || "4.8"}
                  </span>
                  <Link
                    to={`/destinations/${d.slug}`}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow"
                  >
                    Explore Destination ➔
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Type chips */}
      <div className="flex flex-wrap gap-2">
        {TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => { setType(opt.value); setPage(1); setCategoryChip("") }}
            className={`px-4 py-2 rounded-full text-sm font-bold transition-all ${type === opt.value ? chipActive : chipIdle}`}
            style={type === opt.value ? { background: GREEN } : {}}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Search bar with autocomplete */}
      <SearchBar
        className="flex-1"
        defaultValue={initialQuery}
        placeholder="Search by name, district (e.g. Mahendra Cave, Phewa, Rara, Pathibhara)…"
        fetchSuggestions={fetchSuggestions}
        onSearch={(val) => {
          setQuery(val)
          setPage(1)
          setLetter("")
        }}
      />

      {/* Category chips */}
      {type !== "hotel" && (
        <div className="flex flex-wrap gap-2">
          {CATEGORY_CHIPS.map((c) => (
            <button
              key={c.value}
              onClick={() => { setCategoryChip(c.value); setPage(1); setLetter("") }}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all border ${categoryChip === c.value ? catActive : catIdle}`}
            >
              <span className="mr-1">{c.icon}</span>{c.label}
            </button>
          ))}
        </div>
      )}

      {/* A-Z alphabet bar for quick browsing */}
      {type === "attraction" && !query && (
        <div className="flex flex-wrap items-center gap-1.5 px-1">
          <span className="text-[10px] font-black uppercase tracking-wider mr-1" style={{ color: GOLD }}>
            A–Z:
          </span>
          <button
            onClick={() => { setLetter(""); setPage(1) }}
            className={`w-7 h-7 rounded-md text-[11px] font-black transition ${letter === "" ? "text-white" : "text-[#1f6b4d] hover:bg-[#1f6b4d]/10"}`}
            style={letter === "" ? { background: GREEN } : {}}
          >
            All
          </button>
          {ALPHABET.map((L) => (
            <button
              key={L}
              onClick={() => { setLetter(L); setPage(1) }}
              className={`w-6 h-7 rounded-md text-[11px] font-bold transition ${letter === L ? "text-white" : "text-[#1f6b4d] hover:bg-[#1f6b4d]/10"}`}
              style={letter === L ? { background: TERRACOTTA } : {}}
            >
              {L}
            </button>
          ))}
        </div>
      )}

      {/* Results meta */}
      {!loading && (
        <div className="flex items-center justify-between text-xs text-gray-500 px-1">
          <span>
            Showing <b style={{ color: INK }}>{totalCount.toLocaleString()}</b> places
            {query && <> for "<b style={{ color: TERRACOTTA }}>{query}</b>"</>}
            {letter && <> starting with <b style={{ color: TERRACOTTA }}>{letter}</b></>}
          </span>
          {(query || letter || categoryChip) && (
            <button
              onClick={() => { setQuery(""); setLetter(""); setCategoryChip(""); setPage(1) }}
              className="text-[#c2603a] font-bold hover:underline"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => <DestinationCardSkeleton key={i} />)}
        </div>
      ) : destinations.length > 0 ? (
        <div className="space-y-8">
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
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
        <div className="p-8 sm:p-12 text-center max-w-xl mx-auto space-y-5 border rounded-3xl shadow-2xl"
             style={{
               borderColor: "rgba(31,107,77,0.3)",
               background: `linear-gradient(135deg, #ffffff, ${WARM_BG})`,
             }}>
          <div className="w-16 h-16 rounded-full mx-auto flex items-center justify-center font-black text-2xl shadow-sm"
               style={{ background: `${TERRACOTTA}15`, color: TERRACOTTA }}>
            ✨
          </div>

          <div className="space-y-2">
            <h3 className="font-extrabold text-2xl" style={{ color: INK }}>
              Destination Not Found
            </h3>
            <p className="text-sm text-gray-600 max-w-md mx-auto leading-relaxed">
              No matching attractions yet. Try the AI Discovery to research and verify{` `}
              <b style={{ color: TERRACOTTA }}>"{query || letter || "this destination"}"</b>?
            </p>
          </div>

          {didYouMean && (
            <div className="rounded-2xl border p-4 text-left"
                 style={{ borderColor: `${GOLD}55`, background: `${GOLD}12` }}>
              <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#7a5a10] mb-1">
                ✨ Did you mean
              </div>
              <button
                onClick={() => { setQuery(didYouMean.name); setDidYouMean(null); setPage(1) }}
                className="w-full flex items-center justify-between gap-3 text-left group"
              >
                <span className="font-black text-lg" style={{ color: INK }}>
                  💡 {didYouMean.name}
                </span>
                <span className="text-xs font-bold px-3 py-1.5 rounded-xl text-white shadow group-hover:scale-105 transition-all"
                      style={{ background: TERRACOTTA }}>
                  Search instead →
                </span>
              </button>
            </div>
          )}

          <button
            onClick={handleResearchQuery}
            disabled={researching || !query}
            className="px-8 py-3.5 text-white font-black text-sm rounded-2xl shadow-xl hover:scale-105 transition-all disabled:opacity-50"
            style={{ background: GREEN }}
          >
            {researching ? "Researching..." : `Research "${query || "Place"}" ➔`}
          </button>
        </div>
      )}
      {extras?.length > 0 && <CMSExtras sections={extras} />}
    </div>
  )
}
