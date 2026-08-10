import { useState } from "react"
import { motion } from "framer-motion"
import { FiCompass, FiStar, FiMapPin, FiArrowRight } from "react-icons/fi"
import { Link } from "react-router-dom"

const AI_RECOMMENDED = [
  { name: "Phewa Lake & Sarangkot", city: "Pokhara", match: "98% Match", reason: "Based on scenic lake boating & mountain views", slug: "phewa-lake-tal-barahi" },
  { name: "Pashupatinath Temple", city: "Kathmandu", match: "95% Match", reason: "Matches ancient heritage & UNESCO cultural interest", slug: "pashupatinath-temple" },
  { name: "Annapurna Sanctuary", city: "Kaski", match: "94% Match", reason: "Recommended for alpine mountain amphitheater trek", slug: "annapurna-base-camp-abc-sanctuary" },
  { name: "Chitwan National Park Safari", city: "Sauraha", match: "91% Match", reason: "Wildlife safari & Rhino encounters", slug: "chitwan-national-park-safari" },
]

export default function RecommendationEngine() {
  return (
    <div className="card-base p-6 space-y-4 bg-gradient-to-br from-white to-purple-50/50 border border-purple-100 rounded-3xl shadow-xl">
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
            <FiCompass className="text-purple-600" /> AI Personalized Destination Recommendations
          </h3>
          <p className="text-xs text-gray-500">Learns from viewed, searched, and favorited destinations</p>
        </div>
        <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-[10px] font-bold">
          Collaborative Filter
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {AI_RECOMMENDED.map((rec, i) => (
          <div key={i} className="p-4 rounded-2xl bg-white border border-purple-100 hover:border-purple-300 transition-all space-y-1.5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                {rec.match}
              </span>
              <span className="text-[10px] text-gray-400">📍 {rec.city}</span>
            </div>
            <h4 className="font-bold text-gray-900 text-sm">{rec.name}</h4>
            <p className="text-[11px] text-gray-500">{rec.reason}</p>
            <Link to={`/destinations/${rec.slug}`} className="text-xs font-bold text-purple-700 hover:text-purple-900 flex items-center gap-1 pt-1">
              Explore Destination <FiArrowRight size={12} />
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}
