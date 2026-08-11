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

const TREK_PROFILES = [
  {
    id: "ebc",
    name: "Everest Base Camp Trek",
    maxAlt: "5,545m (Kala Patthar)",
    days: "12-14 Days",
    difficulty: "Challenging",
    route: [
      { stop: "Lukla", alt: 2800 },
      { stop: "Phakding", alt: 2610 },
      { stop: "Namche Bazaar (Acclimatize)", alt: 3440, highlight: "Sherpa Capital" },
      { stop: "Tengboche", alt: 3860, highlight: "Famous Gompa" },
      { stop: "Dingboche (Acclimatize)", alt: 4410 },
      { stop: "Lobuche", alt: 4940 },
      { stop: "Gorak Shep / EBC", alt: 5364, highlight: "Base Camp" },
      { stop: "Kala Patthar", alt: 5545, highlight: "Summit View" },
    ]
  },
  {
    id: "abc",
    name: "Annapurna Sanctuary (ABC)",
    maxAlt: "4,130m (Annapurna Base Camp)",
    days: "7-10 Days",
    difficulty: "Moderate",
    route: [
      { stop: "Nayapul", alt: 1070 },
      { stop: "Tikhedhunga", alt: 1540 },
      { stop: "Ghorepani (Poon Hill)", alt: 2860, highlight: "Sunrise View" },
      { stop: "Chhomrong", alt: 2170 },
      { stop: "Dovan", alt: 2600 },
      { stop: "Deurali", alt: 3200 },
      { stop: "Machhapuchhre BC", alt: 3700 },
      { stop: "Annapurna Base Camp", alt: 4130, highlight: "360° Amphitheater" },
    ]
  },
  {
    id: "langtang",
    name: "Langtang Valley & Kyanjin",
    maxAlt: "4,773m (Kyanjin Ri)",
    days: "6-8 Days",
    difficulty: "Moderate",
    route: [
      { stop: "Syabrubesi", alt: 1460 },
      { stop: "Lama Hotel", alt: 2470 },
      { stop: "Langtang Village", alt: 3430 },
      { stop: "Kyanjin Gompa", alt: 3870, highlight: "Yak Cheese Factory" },
      { stop: "Kyanjin Ri Summit", alt: 4773, highlight: "Glacial Vistas" },
    ]
  }
]

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
  const [activeTrek, setActiveTrek] = useState("ebc")
  const [activeTab, setActiveTab] = useState("trekking") // 'trekking' | 'cuisine'
  const selectedTrek = TREK_PROFILES.find((t) => t.id === activeTrek) || TREK_PROFILES[0]

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
            {TREK_PROFILES.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTrek(t.id)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTrek === t.id
                    ? "bg-amber-400 text-gray-950 shadow-md font-black"
                    : "bg-slate-50 text-gray-700 hover:bg-purple-50 border border-slate-200"
                }`}
              >
                {t.name}
              </button>
            ))}
          </div>

          {/* Selected Trek Elevation Bar Visualization */}
          <div className="bg-gradient-to-br from-purple-950 via-slate-900 to-purple-900 text-white p-6 rounded-3xl space-y-6 shadow-2xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-purple-800/60 pb-3">
              <div>
                <h3 className="font-extrabold text-xl text-amber-300">{selectedTrek.name}</h3>
                <p className="text-xs text-purple-200">
                  Duration: <b>{selectedTrek.days}</b> · Difficulty: <b>{selectedTrek.difficulty}</b> · Peak: <b>{selectedTrek.maxAlt}</b>
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-rose-500/30 border border-rose-400 text-rose-200 text-xs font-bold flex items-center gap-1">
                <FiShield size={12} /> High Altitude Care (&gt;3,500m)
              </span>
            </div>

            {/* Interactive Elevation Bar Chart */}
            <div className="space-y-3">
              <p className="text-[11px] font-bold text-purple-300 uppercase tracking-wider">
                Elevation Progression by Waypoint (Meters Above Sea Level)
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 pt-2">
                {selectedTrek.route.map((r, i) => {
                  const heightPct = Math.min(100, Math.max(20, (r.alt / 5600) * 100))
                  const isHighAlt = r.alt >= 3500
                  return (
                    <div key={i} className="flex flex-col items-center justify-end text-center space-y-2">
                      <span className="text-[11px] font-mono font-bold text-amber-300">
                        {r.alt.toLocaleString()}m
                      </span>

                      {/* Bar */}
                      <div className="w-full bg-purple-900/60 rounded-xl h-36 flex items-end p-1 relative group">
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: `${heightPct}%` }}
                          transition={{ duration: 0.6, delay: i * 0.05 }}
                          className={`w-full rounded-lg ${
                            isHighAlt
                              ? "bg-gradient-to-t from-amber-500 to-rose-500 shadow-md shadow-rose-500/30"
                              : "bg-gradient-to-t from-emerald-500 to-cyan-400"
                          }`}
                        />
                        {r.highlight && (
                          <span className="absolute -top-6 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded bg-black/80 text-[9px] font-bold text-amber-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                            {r.highlight}
                          </span>
                        )}
                      </div>

                      <div className="min-h-[32px]">
                        <p className="font-bold text-[11px] text-white leading-tight">{r.stop}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-between items-center text-xs text-purple-200 border-t border-purple-800/40 pt-3 gap-2">
              <p>💡 <i>Acclimatization Rule:</i> Rest every 1,000m gained above 3,000m and drink 4+ liters of water daily.</p>
              <Link
                to="/compare"
                className="px-4 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs inline-flex items-center gap-1 shadow"
              >
                Compare with Other Treks ➔
              </Link>
            </div>
          </div>
        </motion.div>
      )}

      {/* TAB 2: NEPALI CULINARY HERITAGE EXPLORER */}
      {activeTab === "cuisine" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {AUTHENTIC_FOODS.map((food, idx) => (
            <BorderBeamCard key={idx} className="bg-white">
              <div className="space-y-2.5">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[10px] font-black uppercase">
                      {food.region}
                    </span>
                    <h3 className="text-xl font-extrabold text-gray-900 mt-1 flex items-center gap-2">
                      {food.name} <span className="text-sm font-normal text-purple-700 font-devanagari font-bold">({food.nepali})</span>
                    </h3>
                  </div>
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-100">
                    {food.tagline}
                  </span>
                </div>

                <p className="text-xs text-gray-600 leading-relaxed">
                  {food.desc}
                </p>

                <div className="p-3 rounded-2xl bg-purple-50/70 border border-purple-100 text-[11px] text-purple-950 flex items-center justify-between">
                  <span>📍 <b>Where to experience:</b> {food.whereToTaste}</span>
                  <Link to="/destinations" className="text-purple-700 font-bold hover:underline shrink-0 ml-2">
                    Find Spots ➔
                  </Link>
                </div>
              </div>
            </BorderBeamCard>
          ))}
        </motion.div>
      )}
    </section>
  )
}

export default NepalExperienceSection
