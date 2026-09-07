import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiAward,
  FiCoffee,
  FiFeather,
  FiHome,
  FiImage,
  FiMap,
  FiSun,
  FiTriangle,
  FiCheckCircle,
  FiInfo,
  FiBookOpen,
  FiX,
  FiCalendar,
} from "react-icons/fi"

import NationalSymbols, { ALL_26_NATIONAL_SYMBOLS, EIGHT_THOUSANDERS, HIMALAYAN_RANGES, DEFAULT_FOODS, DEFAULT_FESTIVALS } from "../components/dashboard/NationalSymbols"
import destinationApi from "../api/destinationApi"
import { NOT_RECORDED, UPDATE_SOON, recordedCity, recordedText } from "../utils/placeUtils"

const DEFAULT_CULTURE = [
  {
    title: "Newari Pagoda Architecture & Durbar Squares",
    nepali: "नेवारी मल्लकालीन दरबार र वास्तुकला",
    region: "Kathmandu, Patan & Bhaktapur",
    desc: "Multi-tiered pagoda temples, 55-Window Palace, intricately carved peacock wooden windows, and golden torana arches built by Malla kings.",
    image: "/images/destinations/stupa-DJFZCRbV.jfif",
  },
  {
    title: "Sacred Pilgrimage & Spiritual Traditions",
    nepali: "धार्मिक तथा सांस्कृतिक तीर्थस्थल",
    region: "Pashupatinath, Lumbini, Muktinath & Janakpur",
    desc: "Holy Bagmati riverbank rituals, Maya Devi Temple in Buddha's birthplace, Janaki Mandir Mithila art, and sacred flame springs of Muktinath.",
    image: "/images/destinations/flag_png-DqQuUnzj.jfif",
  },
  {
    title: "Masked Lakhey & Sacred Charya Dances",
    nepali: "लाखे, मारुनी र चर्या नृत्य",
    region: "Indra Jatra, Patan & Mountain Villages",
    desc: "Fierce demon-dispelling Lakhey mask dances during Indra Jatra, Kirat Maruni folk dances, and Vajrayana Buddhist Charya dance dramas performed by priests.",
    image: "/images/destinations/images-DG4ceRrC.jfif",
  },
  {
    title: "Buddhist Thangka Painting & Bronze Statuary",
    nepali: "पौभाः, थङ्का र कास्य मूर्ति कला",
    region: "Patan Craft Workshops & Bouddha",
    desc: "Centuries-old lost-wax bronze casting, Paubha scroll paintings, and hand-woven Tibetan carpets crafted by master artisans.",
    image: "/images/destinations/emblem-Q_w8OTwe.jfif",
  },
]

const Section = ({ id, icon: Icon, title, children }) => (
  <motion.section
    id={id}
    initial={{ opacity: 0, y: 12 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    className="scroll-mt-24 py-10 border-b border-gray-100 last:border-0"
  >
    <h2 className="section-title flex items-center gap-2">
      <Icon className="text-himalaya-500" />
      {title}
    </h2>
    {children}
  </motion.section>
)

const DestChip = ({ dest }) => (
  <Link
    to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"}
    className="text-xs font-medium bg-gray-50 text-gray-700 px-3.5 py-2 rounded-full border border-gray-200 hover:border-emerald-500 hover:bg-emerald-50 transition"
  >
    {dest.name}
    {dest.altitude ? ` · ${dest.altitude}` : ""}
  </Link>
)

const DestCard = ({ dest, icon: Icon }) => (
  <Link to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"} className="card-base p-4 hover:shadow-md transition bg-white border border-slate-200">
    {dest.cover_image_url ? (
      <img src={dest.cover_image_url} alt={dest.name} className="w-full h-32 rounded-xl mb-3 object-cover bg-gray-100" />
    ) : (
      <div className="w-full h-32 rounded-xl mb-3 bg-himalaya-50 flex items-center justify-center text-himalaya-300">
        {Icon ? <Icon size={28} /> : <FiImage size={28} />}
      </div>
    )}
    <h3 className="font-bold text-sm text-slate-900 mb-1">{dest.name}</h3>
    <p className="text-xs text-gray-500">{recordedCity(dest) || dest.district || NOT_RECORDED}</p>
    <p className="text-xs text-gray-600 mt-1 line-clamp-2">{recordedText(dest.short_description || dest.description)}</p>
  </Link>
)

export default function DiscoverNepal() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showSymbolsModal, setShowSymbolsModal] = useState(false)

  useEffect(() => {
    destinationApi.discoverNepal()
      .then(({ data }) => setPayload(data))
      .catch(() => setPayload(null))
      .finally(() => setLoading(false))
  }, [])

  const wildlife = payload?.wildlife?.items || []
  const heritage = payload?.heritage?.items || []
  const mountains = payload?.mountains?.items || []
  const culture = payload?.culture?.items || []
  const cuisine = payload?.cuisine?.items?.length ? payload.cuisine.items : DEFAULT_FOODS
  const festivals = payload?.festivals?.items?.length ? payload.festivals.items : DEFAULT_FESTIVALS
  const provinces = payload?.provinces || []

  return (
    <div className="container-app py-10 fade-in space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b pb-6">
        <div>
          <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
            Himalayan Atlas & National Identity
          </span>
          <h1 className="text-3xl md:text-5xl font-black text-slate-900 mt-2 tracking-tight">
            Discover Nepal — Beyond Everest
          </h1>
          <p className="text-gray-600 text-sm mt-1 max-w-2xl">
            Explore Nepal's 26 national symbols, 8,000m Himalayan mountain ranges, UNESCO heritage, living cultural traditions, wildlife reserves, and culinary culture.
          </p>
        </div>

        <button
          onClick={() => setShowSymbolsModal(true)}
          className="px-5 py-3 rounded-2xl bg-[#0B3D91] hover:bg-blue-900 text-white font-extrabold text-xs sm:text-sm shadow-lg flex items-center gap-2 shrink-0"
        >
          <FiBookOpen size={16} /> All 26 National Symbols Showcase ➔
        </button>
      </div>

      {/* Top Banner: National Symbols Summary */}
      <NationalSymbols />

      {/* 8,000m PEAKS TABLE & HIMALAYAN RANGES */}
      <section className="card-base p-6 sm:p-8 bg-white border border-slate-200 shadow-xl space-y-6">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-black uppercase tracking-wider">
            Highest Mountains on Earth
          </span>
          <h2 className="text-2xl font-black text-slate-900 mt-2 flex items-center gap-2">
            🏔️ Nepal's 8 Mountains Above 8,000 Meters
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Nepal contains 8 of the world's 14 mountains higher than 8,000 meters.
          </p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-white uppercase font-black tracking-wider text-[11px]">
              <tr>
                <th className="p-3">Rank</th>
                <th className="p-3">Mountain Peak</th>
                <th className="p-3">Height (m)</th>
                <th className="p-3">Himalayan Section</th>
                <th className="p-3">District / Region</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {EIGHT_THOUSANDERS.map((m) => (
                <tr key={m.rank} className="hover:bg-slate-50 font-medium">
                  <td className="p-3 font-black text-amber-600">#{m.rank}</td>
                  <td className="p-3 font-bold text-slate-900 text-sm">{m.name}</td>
                  <td className="p-3 font-black text-emerald-700 font-mono text-sm">{m.height}</td>
                  <td className="p-3 text-slate-600">{m.range}</td>
                  <td className="p-3 text-slate-600">{m.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Major Himalayan Sections Grid */}
        <div className="pt-4 border-t border-slate-100 space-y-3">
          <h3 className="font-extrabold text-base text-slate-900">Major Himalayan Sections of Nepal</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {HIMALAYAN_RANGES.map((r, i) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                <p className="font-black text-blue-900 text-sm">{r.range}</p>
                <p className="text-emerald-700 font-bold">Highest: {r.highest}</p>
                <p className="text-slate-600"><b>Peaks:</b> {r.peaks}</p>
                <p className="text-slate-500 text-[11px]">📍 {r.area}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CULTURAL & LIVING HERITAGE SECTION */}
      <Section id="cultural-heritage" icon={FiFeather} title="Nepali Cultural & Living Heritage">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
          {DEFAULT_CULTURE.map((item, idx) => (
            <div key={idx} className="card-base p-4 bg-white border border-slate-200 space-y-3 flex flex-col justify-between hover:shadow-md transition">
              <div className="space-y-2">
                <img src={item.image} alt={item.title} className="w-full h-36 object-cover rounded-xl bg-slate-100 border border-slate-100" />
                <div>
                  <span className="text-[10px] font-black uppercase text-amber-700 block">{item.nepali}</span>
                  <h3 className="font-extrabold text-sm text-slate-900 mt-0.5">{item.title}</h3>
                  <p className="text-[11px] text-slate-500 font-semibold mt-0.5">📍 {item.region}</p>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* FESTIVALS */}
      <Section id="festivals" icon={FiSun} title="Vibrant Cultural Festivals">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
          {festivals.map((fest, idx) => (
            <div key={idx} className="card-base p-5 bg-white border border-slate-200 space-y-2">
              <div className="flex justify-between items-start">
                <h3 className="font-black text-base text-slate-900">{fest.title || fest.name}</h3>
                <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full font-bold">
                  {fest.date || fest.kind || "Festival"}
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{fest.body || fest.desc}</p>
              <p className="text-[11px] font-bold text-emerald-700 pt-1 border-t">
                📍 {fest.city || fest.district || "All Nepal"}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* WILDLIFE & PARKS */}
      <Section id="wildlife" icon={FiAward} title="Wildlife Reserves & National Parks">
        {wildlife.length ? (
          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            {wildlife.map((dest) => <DestCard key={dest.id} dest={dest} icon={FiAward} />)}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            {[
              { id: 1, name: "Chitwan National Park", district: "Chitwan", short_description: "UNESCO Heritage site famous for One-horned Rhinos and Bengal Tigers.", cover_image_url: "/images/destinations/chitwan/safari.jpg" },
              { id: 2, name: "Bardiya National Park", district: "Bardiya", short_description: "Untouched wilderness with Royal Bengal Tigers, wild elephants, and Gangetic dolphins.", cover_image_url: "/images/destinations/bardiya/tiger-reserve.jpg" },
            ].map((d) => <DestCard key={d.id} dest={d} icon={FiAward} />)}
          </div>
        )}
      </Section>

      {/* HERITAGE SITES */}
      <Section id="unesco" icon={FiHome} title="UNESCO Heritage & Palaces">
        {heritage.length ? (
          <div className="flex flex-wrap gap-2 mt-2">
            {heritage.map((dest) => <DestChip key={dest.id} dest={dest} />)}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2 mt-2">
            {["Pashupatinath Temple", "Boudhanath Stupa", "Swayambhunath", "Kathmandu Durbar Square", "Patan Durbar Square", "Bhaktapur Durbar Square", "Lumbini Sacred Garden", "Changu Narayan"].map((name, i) => (
              <span key={i} className="px-3.5 py-2 rounded-full bg-amber-50 text-amber-900 border border-amber-200 text-xs font-bold">
                🏛️ {name}
              </span>
            ))}
          </div>
        )}
      </Section>

      {/* LOCAL FOOD */}
      <Section id="local-food" icon={FiCoffee} title="Authentic Nepali Culinary Heritage">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-2">
          {DEFAULT_FOODS.map((food, i) => (
            <div key={i} className="card-base p-4 bg-white border border-slate-200 space-y-3">
              <img src={food.image} alt={food.name} className="w-full h-36 object-cover rounded-xl" />
              <div>
                <span className="text-[10px] font-black uppercase text-amber-700">{food.nepali}</span>
                <h3 className="font-extrabold text-base text-slate-900">{food.name}</h3>
                <p className="text-xs text-slate-500">📍 {food.region}</p>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{food.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* PROVINCE INFORMATION */}
      <Section id="provinces" icon={FiMap} title="7 Provinces of Nepal">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
          {provinces.map((province) => (
            <Link
              key={province.name}
              to={`/destinations?q=${encodeURIComponent(province.name)}`}
              className="card-base p-4 hover:shadow-md transition bg-white border border-slate-200"
            >
              <h3 className="font-extrabold text-base text-slate-900">{province.name}</h3>
              <p className="text-xs text-emerald-700 font-bold mt-1">
                {province.destination_count != null
                  ? `${province.destination_count.toLocaleString()} recorded places`
                  : "Recorded places"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {province.sample_name || NOT_RECORDED}
              </p>
            </Link>
          ))}
        </div>
      </Section>

      {/* ALL 26 NATIONAL SYMBOLS SHOWCASE MODAL */}
      <AnimatePresence>
        {showSymbolsModal && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b pb-4">
                <div>
                  <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase">
                    Official 26 National Symbols Showcase
                  </span>
                  <h3 className="text-2xl font-black text-slate-900 mt-2">Nepal National Symbols & Heritage Details</h3>
                </div>
                <button onClick={() => setShowSymbolsModal(false)} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700">
                  <FiX size={20} />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                {ALL_26_NATIONAL_SYMBOLS.map((s) => (
                  <div key={s.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1.5 flex flex-col justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        {s.image ? (
                          <img src={s.image} alt={s.title} className="w-12 h-12 rounded-full object-cover border-2 border-amber-500 shadow" />
                        ) : (
                          <span className="text-2xl">{s.icon}</span>
                        )}
                        <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">{s.nepali}</span>
                      </div>
                      <h4 className="font-extrabold text-sm text-slate-900">{s.title}</h4>
                      <p className="text-slate-600 leading-relaxed">{s.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-4 border-t">
                <button onClick={() => setShowSymbolsModal(false)} className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs">
                  Close Showcase
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
