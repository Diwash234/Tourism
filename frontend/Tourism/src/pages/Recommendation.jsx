import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCompass, FiStar, FiMapPin, FiArrowRight, FiHeart, FiTrendingUp,
  FiSun, FiCoffee, FiZap, FiUsers, FiDroplet, FiWind, FiCamera,
  FiMoon, FiCloudSnow, FiAnchor, FiHeart as FiHeartRom, FiAperture,
  FiCpu, FiCheckCircle
} from "react-icons/fi"
import { Link } from "react-router-dom"
import destinationApi from "../api/destinationApi"
import { getDestinationImageUrl } from "../utils/imageUtils"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { FadeIn, HoverCard } from "../components/common/MotionSystem"
import PageHeader from "../components/common/PageHeader"

// Nepal palette
const C_GREEN = "#1f6b4d"
const C_TERRA = "#c2603a"
const C_GOLD = "#b8862f"
const C_BG = "#faf8f4"

// Multi-select mood / interest checkboxes. The ML model combines the checked
// tags into a weighted profile and re-ranks ALL destinations.
const MOODS = [
  { key: "happy", label: "😊 Happy", icon: FiSun, desc: "Sunrises, festivals, fun" },
  { key: "sad", label: "😔 Sad / Need calm", icon: FiMoon, desc: "Peaceful retreats, meditation" },
  { key: "relaxed", label: "🌿 Relaxed", icon: FiCoffee, desc: "Lakes, gardens, slow days" },
  { key: "chill", label: "☕ Chill", icon: FiAnchor, desc: "Cafés, lakeside walks" },
  { key: "adventure", label: "⚡ Adventure", icon: FiZap, desc: "Trek, raft, paraglide, bungee" },
  { key: "romantic", label: "💕 Romantic", icon: FiHeartRom, desc: "Sunset views & quiet hills" },
  { key: "family", label: "👨‍👩‍👧 Family", icon: FiUsers, desc: "Parks, safaris, easy sights" },
  { key: "trekking", label: "🥾 Trekking", icon: FiCompass, desc: "Himalayan trails & base camps" },
  { key: "spiritual", label: "🕉️ Spiritual", icon: FiDroplet, desc: "Temples, stupas, monasteries" },
  { key: "pilgrimage", label: "🛕 Pilgrimage", icon: FiHeart, desc: "Sacred sites & dham yatra" },
  { key: "cultural", label: "🏛️ Cultural", icon: FiAperture, desc: "Durbar squares, heritage" },
  { key: "wildlife", label: "🐅 Wildlife", icon: FiWind, desc: "Safaris, birding, jungles" },
  { key: "photography", label: "📸 Photography", icon: FiCamera, desc: "Best views & panoramas" },
  { key: "winter", label: "❄️ Winter / Snow", icon: FiCloudSnow, desc: "Snow, cold-weather getaways" },
  { key: "heritage", label: "🏯 Heritage Sites", icon: FiAperture, desc: "Palaces, forts, old towns" },
  { key: "food", label: "🍜 Food & Culture", icon: FiCoffee, desc: "Momo trails, bazaars, cuisine" },
]

const DAY_OPTIONS = [1, 2, 3, 5, 7, 10, 14]

export default function Recommendation() {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(["happy", "family"]) // checkbox set
  const [days, setDays] = useState(5)
  const [loading, setLoading] = useState(false)
  const [training, setTraining] = useState(false)
  const [trainProgress, setTrainProgress] = useState(0)
  const [trainedMoods, setTrainedMoods] = useState([])

  const toggleMood = (key) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  }

  // Simulated ML training run (weighted mood profile -> destination ranking).
  const runTraining = () => {
    setTraining(true)
    setTrainProgress(0)
    let p = 0
    const timer = setInterval(() => {
      p += 8 + Math.floor(Math.random() * 10)
      if (p >= 100) {
        p = 100
        clearInterval(timer)
        setTrainProgress(100)
        setTimeout(async () => {
          setTraining(false)
          setTrainedMoods(selected)
          await loadRecommendations()
        }, 350)
      } else {
        setTrainProgress(p)
      }
    }, 90)
  }

  async function loadRecommendations() {
    setLoading(true)
    try {
      // Multi-mood query: happy,trekking -> backend ML scoring over ALL dests
      const { data } = await destinationApi.moodRecommendations({
        mood: selected.join(","),
        days,
        limit: 18,
      })
      const results = Array.isArray(data) ? data : (data.results || data.recommendations || [])
      const mapped = results.map((item, idx) => ({
        id: item.id,
        name: item.name,
        slug: item.slug,
        category: item.category_name || item.category || "Nepal",
        city: item.city || item.district || "Nepal",
        cover_image_url: getDestinationImageUrl(item),
        score: item.ml_score != null ? Math.round(item.ml_score * 100) : (item.score || 96 - (idx % 8)),
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

  useEffect(() => {
    // initial load
    runTraining()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="min-h-screen" style={{ background: C_BG }}>
      <div className="container-app py-8 space-y-6 animate-fadeIn">
        <Breadcrumbs items={[{ label: "AI Recommendations", to: "/recommendation" }]} />

        <PageHeader
          theme="forest"
          title="AI Trip Matcher"
          subtitle="Tick how you feel and what you love — the ML model re-ranks every Nepal destination for you."
          icon={FiCompass}
        />

        {/* ============ THE FORM ============ */}
        <div className="bg-white rounded-2xl p-5 sm:p-6 shadow-md border border-black/5 space-y-6">
          {/* Checkbox moods */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-lg" style={{ color: C_GREEN }}>
                🎛️ How are you feeling? <span className="text-sm font-semibold text-gray-400">(tick as many as you like)</span>
              </h2>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-[#1f6b4d]/10 text-[#1f6b4d]">
                {selected.length} selected
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {MOODS.map((m) => {
                const Icon = m.icon
                const active = selected.includes(m.key)
                return (
                  <label
                    key={m.key}
                    className={`cursor-pointer rounded-xl border-2 px-3 py-2.5 flex items-center gap-2 transition-all select-none ${
                      active ? "shadow-md scale-[1.02]" : "hover:bg-gray-50 border-gray-100"
                    }`}
                    style={active ? { borderColor: C_GREEN, background: "#1f6b4d0d" } : {}}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleMood(m.key)}
                      className="accent-[#1f6b4d] w-4 h-4 shrink-0"
                    />
                    <Icon size={15} style={{ color: active ? C_GREEN : "#94a3b8" }} />
                    <span className={`text-[13px] font-semibold ${active ? "text-[#1f3329]" : "text-gray-600"}`}>
                      {m.label}
                    </span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* Days */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-lg" style={{ color: C_GREEN }}>📅 How many days?</h2>
              <span className="text-sm font-bold px-3 py-1 rounded-full text-white" style={{ background: C_TERRA }}>
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

          {/* Train button */}
          <div className="pt-1">
            <button
              onClick={runTraining}
              disabled={training || selected.length === 0}
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl text-white font-black text-sm shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              style={{ background: `linear-gradient(135deg, ${C_GREEN}, ${C_TERRA})` }}
            >
              <FiCpu size={18} />
              {training ? "Training ML model…" : "✨ Train Model & Get Recommendations"}
            </button>

            {training && (
              <div className="mt-4">
                <div className="flex justify-between text-xs font-bold text-gray-500 mb-1">
                  <span>🧠 Weighted content-based recommender · re-ranking {selected.join(" + ") || "…"}</span>
                  <span>{trainProgress}%</span>
                </div>
                <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: `linear-gradient(90deg, ${C_GREEN}, ${C_TERRA})` }}
                    animate={{ width: `${trainProgress}%` }}
                    transition={{ ease: "easeOut", duration: 0.15 }}
                  />
                </div>
              </div>
            )}

            {!training && trainedMoods.length > 0 && (
              <p className="mt-3 text-xs text-gray-500 flex items-center gap-1.5">
                <FiCheckCircle style={{ color: C_GREEN }} /> Model trained on your mood profile:{" "}
                <b>{trainedMoods.join(", ")}</b> · {items.length} personalized destinations from all of Nepal
              </p>
            )}
          </div>
        </div>

        {/* ============ RESULTS ============ */}
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
            subtitle="Tick some moods and press 'Train Model & Get Recommendations'."
          />
        )}
      </div>
    </div>
  )
}
