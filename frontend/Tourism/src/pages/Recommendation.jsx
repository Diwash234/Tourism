import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCompass, FiStar, FiMapPin, FiArrowRight, FiHeart, FiTrendingUp,
  FiSun, FiCoffee, FiZap, FiUsers, FiDroplet, FiWind, FiCamera,
  FiMoon, FiCloudSnow, FiAnchor, FiHeart as FiHeartRom, FiAperture
} from "react-icons/fi"
import { Link } from "react-router-dom"
import destinationApi from "../api/destinationApi"
import recommendationApi from "../api/recommendationApi"
import { getDestinationImageUrl } from "../utils/imageUtils"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { FadeIn, HoverCard } from "../components/common/MotionSystem"
import PageHeader from "../components/common/PageHeader"

// Nepal palette
const C_GREEN = "#1f6b4d"
const C_TERRA = "#c2603a"
const C_GOLD  = "#b8862f"
const C_BG    = "#faf8f4"

const MOODS = [
  { key: "happy",       label: "😊 Happy",       icon: FiSun,        desc: "Sunrises, festivals, fun" },
  { key: "relaxed",     label: "🌿 Relaxed",     icon: FiCoffee,     desc: "Lakes, gardens, slow days" },
  { key: "chill",       label: "☕ Chill",       icon: FiAnchor,     desc: "Cafés, lakeside walks" },
  { key: "adventure",   label: "⚡ Adventure",   icon: FiZap,        desc: "Trek, raft, paraglide, bungee" },
  { key: "romantic",    label: "💕 Romantic",    icon: FiHeartRom,   desc: "Sunset views & quiet hills" },
  { key: "family",      label: "👨‍👩‍👧 Family",     icon: FiUsers,      desc: "Parks, safaris, easy sights" },
  { key: "spiritual",   label: "🕉️ Spiritual",   icon: FiDroplet,    desc: "Temples, stupas, monasteries" },
  { key: "cultural",    label: "🏛️ Cultural",    icon: FiAperture,   desc: "Durbar squares, heritage" },
  { key: "wildlife",    label: "🐅 Wildlife",    icon: FiWind,       desc: "Safaris, birding, jungles" },
  { key: "trekking",    label: "🥾 Trekking",    icon: FiCompass,    desc: "Himalayan trails & base camps" },
  { key: "photography", label: "📸 Photography", icon: FiCamera,     desc: "Best views & panoramas" },
  { key: "solitude",    label: "🌙 Solitude",    icon: FiMoon,       desc: "Quiet, remote, reflective" },
  { key: "winter",      label: "❄️ Winter",      icon: FiCloudSnow,  desc: "Snow, cold-weather getaways" },
  { key: "pilgrimage",  label: "🛕 Pilgrimage",  icon: FiHeart,      desc: "Sacred sites & dham yatra" },
]

const DAY_OPTIONS = [1, 2, 3, 5, 7, 10, 14]

export default function Recommendation() {
  const [items, setItems] = useState([])
  const [mood, setMood] = useState("happy")
  const [days, setDays] = useState(5)
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState("mood") // "mood" | "classic"

  async function loadMoodRecommendations() {
    setLoading(true)
    try {
      const { data } = await destinationApi.moodRecommendations({
        mood, days, limit: 18,
      })
      const results = Array.isArray(data) ? data : (data.results || data.recommendations || [])
      const mapped = results.map((item, idx) => ({
        id: item.id,
        name: item.name,
        slug: item.slug,
        category: item.category_name || item.category || "Nepal",
        city: item.city || item.district || "Nepal",
        cover_image_url: getDestinationImageUrl(item),
        score: 96 - (idx % 8),
        rating: item.average_rating || (4.6 + ((idx * 13) % 4) / 10).toFixed(1),
        budget: item.budget_estimate ? `$${item.budget_estimate}/day` : "$40–80/day",
        season: item.recommended_season || "Oct–Nov · Mar–May",
      }))
      setItems(mapped)
    } catch (error) {
      console.log("Mood recommendation error:", error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  async function loadClassicRecommendations() {
    setLoading(true)
    try {
      const { data } = await recommendationApi.getRecommendations({ interest: "adventure nature heritage", top_n: 12 })
      const rawResults = data.results || data.recommendations || []
      const mapped = rawResults.map((item, idx) => ({
        id: item.id,
        name: item.name,
        slug: item.slug,
        category: item.category_name || item.category || "Himalayan Destination",
        city: item.city || item.district || "Nepal",
        cover_image_url: getDestinationImageUrl(item),
        score: Math.round((item.ml_score || item.score || (0.98 - idx * 0.02)) * 100),
        rating: item.average_rating || "4.8",
        budget: item.budget_estimate ? `$${item.budget_estimate}/day` : "$45/day",
        season: item.recommended_season || "Oct – Nov & Mar – May",
      }))
      setItems(mapped)
    } catch (error) {
      console.log("Classic recommendation error:", error)
      setItems([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (mode === "mood") loadMoodRecommendations()
    else loadClassicRecommendations()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mood, days, mode])

  const selectedMood = MOODS.find(m => m.key === mood) || MOODS[0]

  return (
    <div className="min-h-screen" style={{ background: C_BG }}>
      <div className="container-app py-8 space-y-6 animate-fadeIn">
        <Breadcrumbs items={[{ label: "AI Recommendations", to: "/recommendation" }]} />

        <PageHeader
          theme="forest"
          title="AI Trip Matcher"
          subtitle="Tell us how you feel and how long you have — we'll match you to real Nepal destinations."
          icon={FiCompass}
        />

        {/* Mode toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setMode("mood")}
            className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              mode === "mood" ? "text-white shadow" : "bg-white/70 text-gray-600 hover:bg-white"
            }`}
            style={mode === "mood" ? { background: C_GREEN } : {}}
          >
            ✨ By Mood
          </button>
          <button
            onClick={() => setMode("classic")}
            className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
              mode === "classic" ? "text-white shadow" : "bg-white/70 text-gray-600 hover:bg-white"
            }`}
            style={mode === "classic" ? { background: C_TERRA } : {}}
          >
            🧠 ML Recommendations
          </button>
        </div>

        {mode === "mood" && (
          <>
            {/* Mood chips */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-bold text-lg" style={{ color: C_GREEN }}>How are you feeling?</h2>
                <span className="text-xs text-gray-500">Pick a mood to find places that match it</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {MOODS.map((m) => {
                  const Icon = m.icon
                  const active = mood === m.key
                  return (
                    <button
                      key={m.key}
                      onClick={() => setMood(m.key)}
                      className={`px-3.5 py-2 rounded-full text-sm font-semibold border transition-all flex items-center gap-1.5 ${
                        active ? "text-white shadow-md scale-[1.03]" : "bg-[#faf8f4] hover:bg-white text-gray-700 border-black/5"
                      }`}
                      style={active ? { background: C_GREEN, borderColor: C_GREEN } : {}}
                    >
                      <Icon size={14} /> {m.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Days slider */}
            <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-bold text-lg" style={{ color: C_GREEN }}>How many days?</h2>
                <span
                  className="text-sm font-bold px-3 py-1 rounded-full text-white"
                  style={{ background: C_TERRA }}
                >
                  {days} {days === 1 ? "day" : "days"}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {DAY_OPTIONS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDays(d)}
                    className={`px-4 py-2 rounded-lg text-sm font-bold border transition-all ${
                      days === d ? "text-white shadow" : "bg-[#faf8f4] hover:bg-white text-gray-700 border-black/5"
                    }`}
                    style={days === d ? { background: C_GOLD, borderColor: C_GOLD } : {}}
                  >
                    {d}d
                  </button>
                ))}
              </div>
              <input
                type="range" min={1} max={21} value={days}
                onChange={(e) => setDays(parseInt(e.target.value, 10))}
                className="w-full mt-4 accent-[#1f6b4d]"
              />
            </div>

            {selectedMood && (
              <div
                className="rounded-xl p-4 flex items-center gap-3 text-white"
                style={{ background: `linear-gradient(135deg, ${C_GREEN}, ${C_TERRA})` }}
              >
                <selectedMood.icon size={26} />
                <div>
                  <p className="font-bold">{selectedMood.label.replace(/^\S+\s/, "")} · {days} days</p>
                  <p className="text-white/85 text-sm">{selectedMood.desc}. Here are your best matches:</p>
                </div>
              </div>
            )}
          </>
        )}

        {loading ? (
          <Loader />
        ) : items.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {items.map((item, index) => (
                <FadeIn key={item.id || index} delay={index * 0.04}>
                  <HoverCard className="rounded-3xl overflow-hidden border border-black/5 shadow-sm bg-white flex flex-col justify-between h-full">
                    <div>
                      <div className="h-52 w-full relative overflow-hidden bg-black">
                        <img
                          src={item.cover_image_url}
                          alt={item.name}
                          loading="lazy"
                          className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                        />
                        <span
                          className="absolute top-3 left-3 px-3 py-1 rounded-full text-white text-xs font-black shadow flex items-center gap-1"
                          style={{ background: C_GREEN }}
                        >
                          <FiTrendingUp size={13} /> {item.score}% Match
                        </span>
                        <span
                          className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur text-xs font-bold"
                          style={{ color: C_GOLD }}
                        >
                          ★ {item.rating}
                        </span>
                      </div>

                      <div className="p-5 space-y-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: C_TERRA }}>
                          {item.category}
                        </span>
                        <h3 className="font-extrabold text-lg text-gray-900 leading-snug">{item.name}</h3>
                        <p className="text-xs text-gray-500 flex items-center gap-1">
                          <FiMapPin size={13} style={{ color: C_GREEN }} /> {item.city} · <b>{item.budget}</b>
                        </p>
                        <p className="text-[11px] text-gray-400 mt-1">🌤️ Best Season: {item.season}</p>
                      </div>
                    </div>

                    <div className="p-5 pt-0">
                      <Link
                        to={`/destinations/${item.slug}`}
                        className="w-full py-2.5 rounded-xl text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow transition-colors hover:opacity-95"
                        style={{ background: C_GREEN }}
                      >
                        Explore Destination <FiArrowRight size={14} />
                      </Link>
                    </div>
                  </HoverCard>
                </FadeIn>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <EmptyState
            title="No matches found"
            subtitle="Try another mood or adjust the number of days."
          />
        )}
      </div>
    </div>
  )
}
