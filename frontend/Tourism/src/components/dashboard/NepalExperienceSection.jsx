import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import { FiCompass, FiCalendar } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import ShimmerBadge from "../ui/ShimmerBadge"
import BorderBeamCard from "../ui/BorderBeamCard"
import PlaceholderImage from "../common/PlaceholderImage"

const AUTHENTIC_FOODS = [
  {
    id: "momo",
    name: "Himalayan Steamed MoMo",
    nepali: "मःमः",
    image: "/images/destinations/food/momo.jpg",
    tagline: "Nepal's Most Loved Dumplings",
    region: "Nationwide (Thamel, Pokhara, Dharan)",
    desc: "Handmade steamed dumplings filled with spiced minced chicken or fresh vegetables, paired with fiery sesame-tomato golbheda achaar.",
  },
  {
    id: "newari",
    name: "Newari Samay Baji & Bhoj",
    nepali: "समय् बजि",
    image: "/images/destinations/food/newari-bhoj.jpg",
    tagline: "Ceremonial Heritage Feast",
    region: "Kathmandu Valley (Patan & Bhaktapur)",
    desc: "Beaten rice (Baji) with marinated spicy smoked meat (Choila), roasted soybeans (Bhatmas), garlic, ginger, and traditional Newari Aila.",
  },
  {
    id: "sel-roti",
    name: "Traditional Sel Roti",
    nepali: "सेल रोटी",
    image: "/images/destinations/food/sel-roti.jpg",
    tagline: "Festive Ring Bread",
    region: "All Nepal (Dashain & Tihar Staple)",
    desc: "Crispy ring-shaped rice flour doughnut fried in pure ghee, subtly flavored with cardamom and cloves, eaten with spicy Achar or hot tea.",
  },
  {
    id: "juju-dhau",
    name: "Bhaktapur Juju Dhau",
    nepali: "जुजु धौ",
    image: "/images/destinations/food/juju-dhau.jpg",
    tagline: "King of Curds",
    region: "Bhaktapur Durbar Square",
    desc: "Rich, thick, creamy buffalo-milk yogurt set in traditional clay pots (Kataru), naturally sweetened and infused with cardamom.",
  },
  {
    id: "masala-chiya",
    name: "Himalayan Masala Chiya",
    nepali: "मसाला चिया",
    image: "/images/destinations/food/masala-chiya.jpg",
    tagline: "Mountain Spiced Milk Tea",
    region: "Ilam & High Mountain Teahouses",
    desc: "Fresh Ilam black tea brewed with milk, ginger, crushed cardamom, cloves, and cinnamon. The essential trail warm-up for trekkers.",
  },
]

const AUTHENTIC_FESTIVALS = [
  {
    id: "dashain",
    name: "Bada Dashain",
    nepali: "बडा दशैं",
    image: "/images/destinations/festivals/dashain-tika.jpg",
    season: "September – October (Autumn)",
    desc: "Nepal's greatest 15-day festival celebrating victory over evil. Families gather for red Tika blessings, Jamara barley shoots, flying kites, and bamboo swings.",
  },
  {
    id: "tihar",
    name: "Tihar & Deepawali",
    nepali: "तिहार र दीपावली",
    image: "/images/destinations/festivals/tihar-diya.jpg",
    season: "October – November (Autumn)",
    desc: "The 5-day festival of lights honoring crows, dogs, cows, Goddess Laxmi, and Brothers (Bhai Tika). Streets glow with oil Diyas and vibrant Rangoli patterns.",
  },
  {
    id: "holi",
    name: "Fagu Purnima (Holi)",
    nepali: "फागु पूर्णिमा (होली)",
    image: "/images/destinations/festivals/holi-kathmandu.jpg",
    season: "March (Spring)",
    desc: "The joyous spring festival of colors. Kathmandu Durbar Square and Pokhara Lakeside burst with vibrant dry powders (Gulal), water balloons, and live music.",
  },
]

export default function NepalExperienceSection({ section = null }) {
  const foods = section?.config?.foods?.length ? section.config.foods : AUTHENTIC_FOODS
  const festivals = section?.config?.festivals?.length ? section.config.festivals : AUTHENTIC_FESTIVALS
  const [recordedTreks, setRecordedTreks] = useState([])
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
  }, [])

  return (
    <section className="space-y-8">
      {/* Section Header */}
      <div className="flex flex-col gap-4 border-b border-[var(--ny-border)] pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <ShimmerBadge variant="gold" icon={FiCompass}>
            Authentic Nepal Culture & Terrain
          </ShimmerBadge>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mt-2">
            {section?.title || "Himalayan treks, culinary heritage & festivals"}
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            {section?.subtitle || "Visual elevation profiles of Nepal's legendary trekking circuits, authentic regional foods, and vibrant cultural festivals."}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-[#F7F8F5] p-1 rounded-2xl border border-[#E5E0D5] self-start sm:self-auto overflow-x-auto no-scrollbar">
          <button
            onClick={() => setActiveTab("trekking")}
            className={`min-h-11 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
              activeTab === "trekking" ? "bg-[var(--ny-green)] text-white shadow" : "text-[var(--ny-text)] hover:bg-[var(--ny-soft-green)]"
            }`}
          >
            Trek circuits
          </button>
          <button
            onClick={() => setActiveTab("cuisine")}
            className={`min-h-11 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
              activeTab === "cuisine" ? "bg-[var(--ny-green)] text-white shadow" : "text-[var(--ny-text)] hover:bg-[var(--ny-soft-green)]"
            }`}
          >
            Nepali food
          </button>
          <button
            onClick={() => setActiveTab("festivals")}
            className={`min-h-11 px-3.5 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
              activeTab === "festivals" ? "bg-[var(--ny-green)] text-white shadow" : "text-[var(--ny-text)] hover:bg-[var(--ny-soft-green)]"
            }`}
          >
            Cultural festivals
          </button>
        </div>
      </div>

      {/* TAB 1: TREK CIRCUITS */}
      {activeTab === "trekking" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="ny-panel p-6 sm:p-8 space-y-6"
        >
          {/* Trek Selector Buttons */}
          <div className="flex flex-wrap gap-2">
            {recordedTreks.map((t) => (
              <button
                key={t.slug || t.id}
                onClick={() => setActiveTrek(t.slug)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTrek === t.slug
                    ? "bg-[var(--ny-gold)] text-[var(--ny-green-deepest)] shadow-md font-black"
                    : "bg-slate-50 text-gray-700 hover:bg-[#F7F8F5] border border-slate-200"
                }`}
              >
                {t.name}
              </button>
            ))}
          </div>

          {selectedTrek && (
            <div className="rounded-[var(--ny-radius-lg)] bg-[var(--ny-green-dark)] p-6 text-white shadow-[var(--ny-shadow-elevated)] space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/15 pb-3">
                <div>
                  <h3 className="font-extrabold text-xl text-amber-300">{selectedTrek.name}</h3>
                  <p className="text-xs text-white/75">
                    Duration: <b>{selectedTrek.recommended_days ? `${selectedTrek.recommended_days} days` : "Not recorded"}</b>
                    {" · "}Difficulty: <b>{selectedTrek.difficulty || "Not recorded"}</b>
                    {" · "}Altitude: <b>{selectedTrek.altitude || "Not recorded"}</b>
                  </p>
                  <p className="text-xs text-[var(--ny-mint)] mt-1">{selectedTrek.city || selectedTrek.district || "Location not recorded"}</p>
                </div>
              </div>
              <p className="text-sm text-white/90 leading-relaxed">{selectedTrek.short_description || selectedTrek.why_recommended?.[0] || "No route description recorded."}</p>
              <div className="flex flex-col sm:flex-row justify-between items-center text-xs text-white/75 border-t border-purple-800/40 pt-3 gap-2">
                <p>Recorded route details are shown when available.</p>
                {selectedTrek.slug && (
                  <Link
                    to={`/destinations/${selectedTrek.slug}`}
                    className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs inline-flex items-center gap-1 shadow"
                  >
                    Open Destination Guide ➔
                  </Link>
                )}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* TAB 2: NEPALI CULINARY HERITAGE */}
      {activeTab === "cuisine" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {foods.map((food) => (
            <BorderBeamCard key={food.id} className="ny-card overflow-hidden flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-44 w-full relative overflow-hidden rounded-2xl bg-black">
                  <PlaceholderImage src={food.image} title={food.name} alt={food.name} className="h-full w-full transition-transform duration-500 hover:scale-105" />
                  <span className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur text-amber-300 text-[10px] font-black uppercase">
                    {food.nepali}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-black text-gray-900">{food.name}</h3>
                  <p className="text-xs font-bold text-amber-700 mt-0.5">{food.tagline}</p>
                  <p className="text-[11px] text-slate-500 font-semibold mt-1">{food.region}</p>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">
                  {food.desc}
                </p>
              </div>
            </BorderBeamCard>
          ))}
        </motion.div>
      )}

      {/* TAB 3: CULTURAL FESTIVALS */}
      {activeTab === "festivals" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {festivals.map((fest) => (
            <BorderBeamCard key={fest.id} className="ny-card overflow-hidden flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-48 w-full relative overflow-hidden rounded-2xl bg-black">
                  <PlaceholderImage src={fest.image} title={fest.name} alt={fest.name} className="h-full w-full transition-transform duration-500 hover:scale-105" />
                  <span className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur text-amber-300 text-[10px] font-black uppercase">
                    {fest.nepali}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-black text-gray-900">{fest.name}</h3>
                  <p className="text-xs font-bold text-[#102A2E] flex items-center gap-1 mt-0.5">
                    <FiCalendar size={12} /> {fest.season}
                  </p>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {fest.desc}
                </p>
              </div>
            </BorderBeamCard>
          ))}
        </motion.div>
      )}
    </section>
  )
}
