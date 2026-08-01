import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { FiMapPin, FiChevronRight } from "react-icons/fi"
import destinationApi from "../api/destinationApi"
import DestinationCard from "../components/cards/DestinationCard"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

/**
 * ExploreNepalMap — Province → District(City) → Destination flow.
 * Honest disclaimer: the 7 zones below are a SIMPLIFIED SCHEMATIC
 * strip, not geographically accurate province boundaries — building a
 * real SVG map of Nepal's province borders would need actual GeoJSON
 * data this project doesn't have. Each zone links to a representative
 * city, same honest approach used in Footer.jsx (province isn't a
 * filterable backend field — checked tourist/filters.py).
 *
 * Once a destination is picked, this hands off to DestinationDetails.jsx
 * (/destinations/:slug), which already combines hotels, weather,
 * navigation, budget, and risk for that place in one view — no need to
 * duplicate that here.
 */
const PROVINCES = [
  { name: "Koshi", city: "Biratnagar", color: "bg-himalaya-500" },
  { name: "Madhesh", city: "Janakpur", color: "bg-forest-500" },
  { name: "Bagmati", city: "Kathmandu", color: "bg-saffron-500" },
  { name: "Gandaki", city: "Pokhara", color: "bg-nepalred-500" },
  { name: "Lumbini", city: "Butwal", color: "bg-himalaya-600" },
  { name: "Karnali", city: "Surkhet", color: "bg-forest-600" },
  { name: "Sudurpashchim", city: "Dhangadhi", color: "bg-saffron-600" },
]

const ExploreNepalMap = () => {
  const [selected, setSelected] = useState(null)
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    destinationApi
      .getAll({ city: selected.city, limit: 12 })
      .then(({ data }) => setDestinations(data.results || data || []))
      .catch(() => setDestinations([]))
      .finally(() => setLoading(false))
  }, [selected])

  return (
    <div className="container-app py-10 fade-in">
      <h1 className="section-title flex items-center gap-2">
        <FiMapPin className="text-himalaya-500" /> Explore Nepal by Province
      </h1>
      <p className="text-gray-500 text-sm mb-2 max-w-2xl">
        Pick a province to narrow down destinations, then drill into any place for hotels, weather,
        budget, and safety info all in one view.
      </p>
      <p className="text-xs text-gray-400 mb-6">
        Simplified schematic, not a precise geographic map — each zone links to that province's main city.
      </p>

      {/* Simplified schematic province strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-8">
        {PROVINCES.map((p) => (
          <button
            key={p.name}
            onClick={() => setSelected(p)}
            className={`relative rounded-xl h-20 text-white text-xs font-semibold flex flex-col items-center justify-center gap-1 transition-transform hover:-translate-y-1 ${p.color} ${
              selected?.name === p.name ? "ring-4 ring-saffron-300" : ""
            }`}
          >
            <FiMapPin size={16} />
            {p.name}
          </button>
        ))}
      </div>

      {selected && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <span className="font-semibold text-dark">{selected.name}</span>
            <FiChevronRight size={14} />
            <span>{selected.city} area</span>
          </div>

          {loading ? (
            <Loader />
          ) : destinations.length ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {destinations.map((d) => (
                <DestinationCard key={d.id} destination={d} />
              ))}
            </div>
          ) : (
            <EmptyState
              title={`No destinations found near ${selected.city}`}
              subtitle="Try another province, or check back once more destinations are added for this area."
            />
          )}
        </motion.div>
      )}
    </div>
  )
}

export default ExploreNepalMap