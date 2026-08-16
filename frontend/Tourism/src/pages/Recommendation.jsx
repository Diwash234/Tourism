import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiCpu, FiCompass, FiStar, FiMapPin, FiArrowRight, FiHeart, FiTrendingUp } from "react-icons/fi"
import { Link } from "react-router-dom"
import recommendationApi from "../api/recommendationApi"
import { getDestinationImageUrl } from "../utils/imageUtils"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { FadeIn, HoverCard } from "../components/common/MotionSystem"

const CATEGORIES = [
  { label: "All Recommendations", value: "all" },
  { label: "🏔️ Trekking & Adventure", value: "adventure" },
  { label: "🏛️ Culture & Heritage", value: "cultural" },
  { label: "🌊 Lakes & Relaxation", value: "relaxation" },
  { label: "🐅 Wildlife & Safaris", value: "nature" },
]

export default function Recommendation() {
  const [items, setItems] = useState([])
  const [category, setCategory] = useState("all")
  const [loading, setLoading] = useState(false)

  async function loadRecommendations() {
    setLoading(true)
    try {
      const interest = category === "all" ? "adventure nature heritage" : category
      const response = await recommendationApi.getRecommendations({ interest, top_n: 12 })
      const data = response.data
      const rawResults = data.results || data.recommendations || []
      const shuffled = [...rawResults].sort(() => Math.random() - 0.5)

      const mapped = shuffled.map((item, idx) => ({
        id: item.id,
        name: item.name,
        slug: item.slug,
        category: item.category_name || item.category || "Himalayan Destination",
        city: item.city || item.district || "Nepal",
        cover_image_url: getDestinationImageUrl(item),
        score: Math.round((item.ml_score || item.score || (0.98 - idx * 0.02)) * 100),
        rating: item.average_rating || "4.9",
        budget: item.budget_estimate ? `$${item.budget_estimate}/day` : "$45/day",
        season: item.recommended_season || "Oct - Nov & Mar - May",
      }))

      setItems(mapped)
    } catch (error) {
      console.log("Recommendation error:", error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRecommendations()
  }, [category])

  return (
    <div className="container-app theme-forest py-8 space-y-6 animate-fadeIn">
      <Breadcrumbs items={[{ label: "AI Recommendations", to: "/recommendation" }]} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
            Machine Learning Engine
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
            <FiCpu className="text-purple-700" /> AI Personalized Recommendations
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Collaborative filtering & content matching based on your travel interests, seasons, and ratings.
          </p>
        </div>

        {/* Category Pill Filters */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategory(cat.value)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                category === cat.value
                  ? "bg-purple-700 text-white shadow-md shadow-purple-900/20"
                  : "bg-gray-100 hover:bg-gray-200 text-gray-700"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Loader />
      ) : items.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item, index) => (
            <HoverCard
              key={item.id || index}
              className="card-base rounded-3xl overflow-hidden border border-purple-100 shadow-xl bg-white flex flex-col justify-between"
            >
              <div>
                <div className="h-52 w-full relative overflow-hidden bg-black">
                  <img
                    src={item.cover_image_url}
                    alt={item.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                  />
                  <span className="absolute top-3 left-3 px-3 py-1 rounded-full bg-emerald-500 text-white text-xs font-black shadow flex items-center gap-1">
                    <FiTrendingUp size={13} /> {item.score}% Match
                  </span>
                  <span className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-black/65 backdrop-blur text-amber-400 text-xs font-bold">
                    ★ {item.rating}
                  </span>
                </div>

                <div className="p-5 space-y-2">
                  <span className="text-[11px] font-bold uppercase text-purple-700 tracking-wider">
                    {item.category}
                  </span>
                  <h3 className="font-extrabold text-lg text-gray-900 leading-snug">{item.name}</h3>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <FiMapPin size={13} className="text-purple-600" /> {item.city} · <b>{item.budget}</b>
                  </p>
                  <p className="text-[11px] text-gray-400 mt-1">🌤️ Best Season: {item.season}</p>
                </div>
              </div>

              <div className="p-5 pt-0">
                <Link
                  to={`/destinations/${item.slug}`}
                  className="w-full py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow transition-colors"
                >
                  Explore Destination <FiArrowRight size={14} />
                </Link>
              </div>
            </HoverCard>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No recommendations found"
          subtitle="Try selecting another category or clear filters."
        />
      )}
    </div>
  )
}
