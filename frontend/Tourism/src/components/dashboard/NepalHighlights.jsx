import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  FiTriangle, FiCompass, FiHome, FiFeather,
  FiWind, FiDroplet, FiMusic, FiCoffee,
} from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import { NOT_RECORDED, UPDATE_SOON } from "../../utils/placeUtils"

const THEMES = [
  { icon: FiTriangle, title: "Mountains", key: "mountains", gradient: "from-himalaya-500 to-himalaya-700" },
  { icon: FiCompass, title: "Featured places", key: "featured", gradient: "from-forest-500 to-himalaya-600" },
  { icon: FiHome, title: "Heritage", key: "heritage", gradient: "from-saffron-500 to-nepalred-500" },
  { icon: FiFeather, title: "Wildlife", key: "wildlife", gradient: "from-forest-600 to-forest-400" },
  { icon: FiWind, title: "Culture", key: "culture", gradient: "from-himalaya-600 to-saffron-500" },
  { icon: FiDroplet, title: "Local food", key: "cuisine", gradient: "from-himalaya-500 to-forest-500" },
  { icon: FiMusic, title: "Festivals", key: "festivals", gradient: "from-nepalred-500 to-saffron-500" },
  { icon: FiCoffee, title: "Provinces", key: "provinces", gradient: "from-saffron-600 to-forest-500" },
]

const NepalHighlights = ({ bare = false }) => {
  const [payload, setPayload] = useState(null)

  useEffect(() => {
    destinationApi.discoverNepal()
      .then(({ data }) => setPayload(data))
      .catch(() => setPayload(null))
  }, [])

  const tagsFor = (key) => {
    if (key === "provinces") return (payload?.provinces || []).map((row) => ({ id: row.name, name: row.name, to: `/destinations?q=${encodeURIComponent(row.name)}` }))
    if (key === "festivals") return (payload?.festivals?.items || []).map((row) => ({ id: row.id, name: row.title, to: "/discover-nepal" }))
    return (payload?.[key]?.items || []).slice(0, 3).map((dest) => ({
      id: dest.id, name: dest.name, to: dest.slug ? `/destinations/${dest.slug}` : "/destinations",
    }))
  }

  return (
    <section className={bare ? "" : "container-app py-16"}>
      <h2 className="section-title text-center mx-auto w-fit">Why Visit Nepal</h2>
      <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10 -mt-2">
        Tags come from recorded destinations and published notices. Empty themes stay {NOT_RECORDED}.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {THEMES.map(({ icon: Icon, title, key, gradient }, i) => {
          const dests = tagsFor(key)
          return (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ delay: i * 0.05 }}
            className="card-base overflow-hidden"
          >
            <div className={`h-24 bg-gradient-to-br ${gradient} flex items-center justify-center`}>
              <Icon size={32} className="text-white/90" />
            </div>
            <div className="p-4">
              <h3 className="font-bold text-dark mb-1.5">{title}</h3>
              <p className="text-sm text-gray-500 mb-3">
                {dests.length ? `${dests.length} recorded entries` : `${NOT_RECORDED} — ${UPDATE_SOON}`}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {dests.length ? dests.map((dest) => (
                  <Link key={dest.id} to={dest.to} className="text-[11px] font-medium bg-gray-50 text-gray-600 px-2 py-1 rounded-full hover:bg-emerald-50">
                    {dest.name}
                  </Link>
                )) : (
                  <span className="text-[11px] font-medium bg-amber-50 text-amber-800 px-2 py-1 rounded-full">{NOT_RECORDED}</span>
                )}
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
