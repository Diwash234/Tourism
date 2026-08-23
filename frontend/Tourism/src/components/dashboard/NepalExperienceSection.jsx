import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link } from "react-router-dom"
import {
  FiCompass, FiTrendingUp, FiCoffee, FiSun, FiMapPin,
  FiArrowRight, FiShield, FiCheck, FiHeart
} from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import NepalCultureCard from "../cards/NepalCultureCard"
import LocalExperienceCard from "../cards/LocalExperienceCard"
import ShimmerBadge from "../ui/ShimmerBadge"
import BorderBeamCard from "../ui/BorderBeamCard"



const AUTHENTIC_FOODS = [
  {
    name: "Dal Bhat Tarkari",
    nepali: "दाल भात",
    tagline: "24-Hour Energy Power for Trekkers",
    region: "All Nepal (National Staple)",
    desc: "Steamed fragrant rice served with slow-cooked yellow lentil soup, seasonal organic vegetables, spicy tomato golbheda achaar, and crisp papad.",
    whereToTaste: "Local teahouses along every Himalayan trail.",
  },
  {
    name: "Newari Samay Baji",
    nepali: "समय् बजि",
    tagline: "Ceremonial Heritage Feast",
    region: "Kathmandu Valley (Newar Culture)",
    desc: "Flattened beaten rice (Baji) served with marinated spicy smoked buffalo meat (Choila), black soybeans (Bhatmas), roasted garlic, ginger, and Aila.",
    whereToTaste: "Patan, Bhaktapur, and Kirtipur heritage courtyards.",
  },
  {
    name: "Thakali Khana Set",
    nepali: "थकाली खाना",
    tagline: "Mustang Gourmet Dal Bhat",
    region: "Mustang & Kali Gandaki Valley",
    desc: "Exquisite buckwheat/rice platter served with Jimbu-tempered black lentils, dried radish Gundruk, and fiery Timur pepper chutney.",
    whereToTaste: "Lakeside Pokhara and Jomsom Thakali kitchens.",
  },
  {
    name: "Himalayan Steamed Momo",
    nepali: "मःमः",
    tagline: "Nepal's Most Loved Dumplings",
    region: "Nationwide (Tibetan-Nepali Fusion)",
    desc: "Handmade steamed dumplings filled with spiced vegetables or minced chicken, paired with spicy sesame-tomato dipping sauce.",
    whereToTaste: "Local restaurants in Thamel, Pokhara Lakeside, and Dharan.",
  }
]

const NepalExperienceSection = () => {
  const [recordedTreks, setRecordedTreks] = useState([])
  const [recordedFoods, setRecordedFoods] = useState([])
  const [activeTrek, setActiveTrek] = useState(null)
  const [activeTab, setActiveTab] = useState("trekking")
  const selectedTrek = recordedTreks.find((t) => t.slug === activeTrek) || recordedTreks[0]

  useEffect(() => {
    destinationApi.moodRecommendations({ mood: "trekking", days: 10, limit: 6 })
      .then(({ data }) => {
        const rows = data.results || []
        const list = (Array.isArray(rows) ? rows : []).filter((row) => row?.name)
        if (list.length) {
          setRecordedTreks(list)
          setActiveTrek(list[0].slug)
          return
        }
        return destinationApi.getDestinations({ featured: true, page_size: 6, limit: 6 })
          .then(({ data: fallback }) => {
            const dests = fallback.results || fallback || []
            const recorded = (Array.isArray(dests) ? dests : []).filter((row) => row?.name)
            setRecordedTreks(recorded)
            if (recorded[0]?.slug) setActiveTrek(recorded[0].slug)
          })
      })
      .catch(() => setRecordedTreks([]))
    destinationApi.discoverNepal()
      .then(({ data }) => setRecordedFoods(data.cuisine?.items || []))
      .catch(() => setRecordedFoods([]))
  }, [])

  return (
    <section className="space-y-8">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-gray-100 pb-4">
        <div>
          <ShimmerBadge variant="gold" icon={FiCompass}>
            Authentic Experiences & Terrain
          </ShimmerBadge>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-2">
            🏔️ Himalayan Elevation Profiles & Culinary Heritage
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Visual elevation profiles of Nepal's legendary trekking circuits paired with authentic regional culinary traditions.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-purple-50 p-1 rounded-2xl border border-purple-100 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("trekking")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === "trekking" ? "bg-purple-700 text-white shadow" : "text-purple-900 hover:bg-purple-100/60"
            }`}
          >
            🥾 Trek Elevation Profiles
          </button>
          <button
            onClick={() => setActiveTab("cuisine")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === "cuisine" ? "bg-purple-700 text-white shadow" : "text-purple-900 hover:bg-purple-100/60"
            }`}
          >
            🍲 Nepali Food Explorer
          </button>
        </div>
      </div>

      {/* TAB 1: TREK ELEVATION PROFILES */}
      {activeTab === "trekking" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl border border-purple-100 p-6 sm:p-8 shadow-xl space-y-6"
        >
          {/* Trek Selector Buttons */}
          <div className="flex flex-wrap gap-2">
            {recordedTreks.map((t) => (
              <button
                key={t.slug || t.id}
                onClick={() => setActiveTrek(t.slug)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTrek === t.slug
                    ? "bg-amber-400 text-gray-950 shadow-md font-black"
                    : "bg-slate-50 text-gray-700 hover:bg-purple-50 border border-slate-200"
                }`}
              >
                {t.name}
              </button>
            ))}
            {!recordedTreks.length && (
              <p className="text-xs text-slate-500">No recorded trek destinations are available yet.</p>
            )}
          </div>

          {selectedTrek && (
          <div className="bg-gradient-to-br from-purple-950 via-slate-900 to-purple-900 text-white p-6 rounded-3xl space-y-6 shadow-2xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-purple-800/60 pb-3">
              <div>
                <h3 className="font-extrabold text-xl text-amber-300">{selectedTrek.name}</h3>
                <p className="text-xs text-purple-200">
                  Duration: <b>{selectedTrek.recommended_days ? `${selectedTrek.recommended_days} days` : "Not recorded"}</b>
                  {" · "}Difficulty: <b>{selectedTrek.difficulty || "Not recorded"}</b>
                  {" · "}Altitude: <b>{selectedTrek.altitude || "Not recorded"}</b>
                </p>
                <p className="text-xs text-purple-300 mt-1">{selectedTrek.city || selectedTrek.district || "City not recorded"}{selectedTrek.province ? `, ${selectedTrek.province}` : ""}</p>
              </div>
            </div>
            <p className="text-sm text-purple-100">{selectedTrek.short_description || selectedTrek.why_recommended?.[0] || "Recorded destination. Turn-by-turn elevation waypoints are not stored."}</p>
            <div className="flex flex-col sm:flex-row justify-between items-center text-xs text-purple-200 border-t border-purple-800/40 pt-3 gap-2">
              <p>Only recorded altitude and trip length are shown. Invented waypoint charts were removed.</p>
              {selectedTrek.slug && (
                <Link
                  to={`/destinations/${selectedTrek.slug}`}
                  className="px-4 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs inline-flex items-center gap-1 shadow"
                >
                  Open destination ➔
                </Link>
              )}
            </div>
          </div>
          )}
        </motion.div>
      )}

      {/* TAB 2: NEPALI CULINARY HERITAGE EXPLORER */}
      {activeTab === "cuisine" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {recordedFoods.length ? recordedFoods.map((food) => (
            <BorderBeamCard key={food.id} className="bg-white">
              <div className="space-y-2.5">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[10px] font-black uppercase">
                      {food.display_city || food.district || "Not recorded"}
                    </span>
                    <h3 className="text-xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
                      {food.name}
                    </h3>
                  </div>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {food.short_description || "Not recorded — we will update soon"}
                </p>
                <div className="p-3 rounded-2xl bg-purple-50/70 border border-purple-100 text-[11px] text-purple-950 flex items-center justify-between">
                  <span>📍 Recorded food notes for this place</span>
                  <Link to={`/destinations/${food.slug}`} className="text-purple-700 font-bold hover:underline shrink-0 ml-2">
                    Open destination ➔
                  </Link>
                </div>
              </div>
            </BorderBeamCard>
          )) : (
            <p className="text-sm text-slate-600 col-span-2">Not recorded — we will update soon. An administrator can add food notes on a destination record.</p>
          )}
        </motion.div>
      )}
    </section>
  )
}

export default NepalExperienceSection
