import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  FiTriangle, FiCompass, FiHome, FiFeather,
  FiWind, FiDroplet, FiMusic, FiCoffee, FiMapPin
} from "react-icons/fi"
import destinationApi from "../../api/destinationApi"

const THEMES = [
  { icon: FiTriangle, title: "Mountains & Peaks", key: "mountains", bgImg: "/images/destinations/everest/base-camp.jpg" },
  { icon: FiCompass, title: "Featured Places", key: "featured", bgImg: "/images/destinations/pokhara/fewatal.jpg" },
  { icon: FiHome, title: "UNESCO Heritage", key: "heritage", bgImg: "/images/destinations/kathmandu/durbar-square.jpg" },
  { icon: FiFeather, title: "Wildlife Reserves", key: "wildlife", bgImg: "/images/destinations/chitwan/safari.jpg" },
  { icon: FiWind, title: "Culture & Living Art", key: "culture", bgImg: "/images/destinations/stupa-DJFZCRbV.jfif" },
  { icon: FiDroplet, title: "Local Culinary Heritage", key: "cuisine", bgImg: "/images/destinations/food/momo.jpg" },
  { icon: FiMusic, title: "Cultural Festivals", key: "festivals", bgImg: "/images/destinations/festivals/dashain-tika.jpg" },
  { icon: FiCoffee, title: "7 Provinces of Nepal", key: "provinces", bgImg: "/images/destinations/ilam/tea-gardens.jpg" },
]

const DEFAULT_THEME_DATA = {
  mountains: [
    { id: "m1", name: "Mount Everest (8,848m)", to: "/destinations/everest-base-camp-ebc" },
    { id: "m2", name: "Annapurna I (8,091m)", to: "/destinations/annapurna-base-camp-abc-sanctuary" },
    { id: "m3", name: "Machhapuchhre (Fishtail)", to: "/destinations/pokhara-lakeside" },
  ],
  featured: [
    { id: "f1", name: "Pokhara Lakeside", to: "/destinations/pokhara-lakeside" },
    { id: "f2", name: "Kathmandu Durbar Square", to: "/destinations/kathmandu-durbar-square" },
    { id: "f3", name: "Rara Alpine Lake", to: "/destinations/rara-lake-national-park" },
  ],
  heritage: [
    { id: "h1", name: "Pashupatinath Temple", to: "/destinations/pashupatinath-temple" },
    { id: "h2", name: "Boudhanath Stupa", to: "/destinations/boudhanath-stupa" },
    { id: "h3", name: "Bhaktapur Durbar Square", to: "/destinations/bhaktapur-durbar-square" },
  ],
  wildlife: [
    { id: "w1", name: "Chitwan Rhino Safari", to: "/destinations/chitwan-national-park-safari" },
    { id: "w2", name: "Bardia Tiger Reserve", to: "/destinations/bardiya-national-park" },
    { id: "w3", name: "Koshi Tappu Wetlands", to: "/destinations/koshi-tappu-wildlife-reserve" },
  ],
  culture: [
    { id: "c1", name: "Newari Pagoda Architecture", to: "/discover-nepal" },
    { id: "c2", name: "Masked Lakhey & Charya Dance", to: "/discover-nepal" },
    { id: "c3", name: "Patan Thangka & Bronze Art", to: "/discover-nepal" },
  ],
  cuisine: [
    { id: "d1", name: "Steamed MoMo & Achar", to: "/discover-nepal" },
    { id: "d2", name: "Dal Bhat Tarkari Platter", to: "/discover-nepal" },
    { id: "d3", name: "Sel Roti & Bhaktapur Juju Dhau", to: "/discover-nepal" },
  ],
  festivals: [
    { id: "v1", name: "Bada Dashain (Sept-Oct)", to: "/discover-nepal" },
    { id: "v2", name: "Tihar Festival of Lights", to: "/discover-nepal" },
    { id: "v3", name: "Holi Festival of Colors", to: "/discover-nepal" },
  ],
  provinces: [
    { id: "p1", name: "Koshi", to: "/destinations?q=Koshi" },
    { id: "p2", name: "Madhesh", to: "/destinations?q=Madhesh" },
    { id: "p3", name: "Bagmati", to: "/destinations?q=Bagmati" },
    { id: "p4", name: "Gandaki", to: "/destinations?q=Gandaki" },
    { id: "p5", name: "Lumbini", to: "/destinations?q=Lumbini" },
    { id: "p6", name: "Karnali", to: "/destinations?q=Karnali" },
    { id: "p7", name: "Sudurpashchim", to: "/destinations?q=Sudurpashchim" },
  ],
}

const NepalHighlights = ({ bare = false }) => {
  const [payload, setPayload] = useState(null)

  useEffect(() => {
    destinationApi.discoverNepal()
      .then(({ data }) => setPayload(data))
      .catch(() => setPayload(null))
  }, [])

  const tagsFor = (key) => {
    let apiData = []
    if (key === "provinces") {
      apiData = (payload?.provinces || []).map((row) => ({ id: row.name, name: row.name, to: `/destinations?q=${encodeURIComponent(row.name)}` }))
    } else if (key === "festivals") {
      apiData = (payload?.festivals?.items || []).map((row) => ({ id: row.id, name: row.title, to: "/discover-nepal" }))
    } else if (payload?.[key]?.items?.length) {
      apiData = payload[key].items.slice(0, 3).map((dest) => ({
        id: dest.id, name: dest.name, to: dest.slug ? `/destinations/${dest.slug}` : "/destinations",
      }))
    }
    return apiData.length ? apiData : (DEFAULT_THEME_DATA[key] || [])
  }

  return (
    <section className={bare ? "" : "container-app py-12"}>
      <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
        <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
          Himalayan Highlights & Culture
        </span>
        <h2 className="section-title text-center mx-auto w-fit">Why Visit Nepal</h2>
        <p className="text-gray-600 text-sm">
          Explore iconic mountain peaks, UNESCO World Heritage, wildlife safaris, authentic local cuisine, and vibrant cultural festivals across all 7 provinces.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {THEMES.map(({ icon: Icon, title, key, bgImg }, i) => {
          const dests = tagsFor(key)
          return (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.05 }}
              className="card-base overflow-hidden bg-white border border-slate-200 shadow-md hover:shadow-xl transition-all flex flex-col justify-between"
            >
              <div>
                <div className="h-32 relative overflow-hidden bg-slate-900">
                  <img src={bgImg} alt={title} className="w-full h-full object-cover opacity-90 hover:scale-105 transition-transform duration-500" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent flex items-end p-3">
                    <span className="text-white font-extrabold text-sm flex items-center gap-2">
                      <Icon className="text-amber-400 shrink-0" size={18} />
                      {title}
                    </span>
                  </div>
                </div>

                <div className="p-4 space-y-3">
                  <p className="text-xs font-bold text-emerald-700 flex items-center gap-1">
                    <FiCheckCircle size={13} /> {dests.length} Verified Entries
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {dests.map((dest) => (
                      <Link
                        key={dest.id || dest.name}
                        to={dest.to}
                        className="text-[11px] font-bold bg-slate-100 text-slate-800 px-2.5 py-1 rounded-full hover:bg-amber-400 hover:text-slate-950 transition-all border border-slate-200"
                      >
                        {dest.name}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}

export default NepalHighlights
