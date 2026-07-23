import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiMapPin, FiShield, FiDollarSign, FiNavigation } from "react-icons/fi"
import SearchBar from "../components/common/SearchBar"
import DestinationCard from "../components/cards/DestinationCard"
import Loader from "../components/common/Loader"
import destinationApi from "../api/destinationApi"
import nepalDestinations from "../data/nepalDestinations"

const features = [
  { icon: FiMapPin, title: "Discover Destinations", desc: "Explore curated local tourist spots with photos, videos and reviews.", accent: "primary" },
  { icon: FiDollarSign, title: "Smart Budget Estimator", desc: "Plan your trip costs accurately before you travel.", accent: "secondary" },
  { icon: FiShield, title: "Real-time Risk Alerts", desc: "Stay informed with safety alerts for every destination.", accent: "marigold" },
  { icon: FiNavigation, title: "Live Navigation", desc: "Get routes, nearby hospitals, police stations and attractions.", accent: "primary" },
]

const ACCENT_CLASSES = {
  primary: "bg-primary-50 text-primary-500",
  secondary: "bg-secondary-50 text-secondary-500",
  marigold: "bg-marigold-50 text-marigold-500",
}

const STATS = [
  { value: "12+", label: "Curated destinations" },
  { value: "16", label: "Local languages supported" },
  { value: "24/7", label: "Risk alert monitoring" },
]

const Landing = () => {
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    destinationApi
      .getAll({ limit: 6, featured: true })
      .then(({ data }) => {
        const items = data.items || data || []
        setDestinations(items.length ? items : nepalDestinations.slice(0, 6))
      })
      .catch(() => setDestinations(nepalDestinations.slice(0, 6)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <section className="relative bg-dusk-gradient text-white overflow-hidden">
        <div className="container-app py-24 md:py-32 relative z-10">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-block text-xs font-semibold tracking-wide uppercase bg-white/10 text-marigold-300 px-3 py-1 rounded-full mb-4"
          >
            Nepal, up close
          </motion.span>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="text-4xl md:text-6xl font-display font-semibold max-w-2xl leading-tight"
          >
            Explore Local Wonders, <span className="text-marigold-300">Travel Smart</span> & Safe
          </motion.h1>
          <p className="mt-4 text-lg text-white/85 max-w-xl">
            Your all-in-one tourism companion — destinations, budgets, safety alerts, and navigation in one place.
          </p>
          <div className="mt-8 bg-white rounded-xl2 p-2 max-w-xl shadow-hover">
            <SearchBar placeholder="Search destinations, cities, attractions..." className="w-full" />
          </div>
          <div className="mt-6 flex gap-3">
            <Link to="/destinations" className="bg-marigold-500 hover:bg-marigold-600 text-white font-semibold px-6 py-3 rounded-xl transition">
              Browse Destinations
            </Link>
            <Link to="/register" className="border border-white/40 font-semibold px-6 py-3 rounded-xl hover:bg-white/10 transition">
              Get Started
            </Link>
          </div>

          <div className="mt-14 grid grid-cols-3 gap-6 max-w-lg">
            {STATS.map((stat) => (
              <div key={stat.label}>
                <p className="text-2xl md:text-3xl font-display font-semibold text-marigold-300">{stat.value}</p>
                <p className="text-xs text-white/70 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Mountain-ridge silhouette anchoring the hero */}
        <svg
          className="absolute bottom-0 left-0 w-full h-24 md:h-32 opacity-25"
          viewBox="0 0 1200 200"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <path
            d="M0,200 L0,110 L150,50 L280,130 L420,30 L580,120 L700,20 L840,115 L980,55 L1100,135 L1200,110 L1200,200 Z"
            fill="white"
          />
        </svg>
        <div className="lungta-strip relative z-10" />
      </section>

      <section className="container-app py-16">
        <h2 className="section-title text-center">Why Travel With Us</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map(({ icon: Icon, title, desc, accent }) => (
            <motion.div
              key={title}
              whileHover={{ y: -4 }}
              className="card-base p-6 text-center"
            >
              <div className={`inline-flex p-3 rounded-full mb-4 ${ACCENT_CLASSES[accent]}`}>
                <Icon size={24} />
              </div>
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="container-app py-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title mb-0">Popular Destinations</h2>
          <Link to="/destinations" className="text-primary-600 font-semibold text-sm hover:underline">
            View all
          </Link>
        </div>
        {loading ? (
          <Loader />
        ) : destinations.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard key={d.id} destination={d} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-10">Destinations will appear here once the backend is connected.</p>
        )}
      </section>

      <section className="container-app pb-20">
        <div className="rounded-xl2 bg-sunrise-gradient text-white p-10 md:p-14 text-center overflow-hidden relative">
          <h2 className="text-2xl md:text-3xl font-display font-semibold mb-2">Ready to plan your Nepal trip?</h2>
          <p className="text-white/90 max-w-lg mx-auto mb-6">
            Build a full itinerary with budget, travel mode, and companions in the Trip Planner.
          </p>
          <Link to="/trip-planner" className="inline-block bg-white text-primary-600 font-semibold px-6 py-3 rounded-xl hover:bg-gray-100 transition">
            Start Planning
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Landing