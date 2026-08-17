import { motion } from "framer-motion"
import { FiTrendingUp, FiCheckCircle, FiClock, FiMapPin, FiArrowRight } from "react-icons/fi"
import { Link } from "react-router-dom"
import { SlideUp, HoverCard } from "../common/MotionSystem"

const EXPEDITIONS = [
  {
    title: "12-Day Everest Base Camp Expedition",
    hiker: "Sarah & David (United Kingdom)",
    route: "Kathmandu ➔ Lukla ➔ Namche ➔ Dingboche ➔ EBC (5,364m)",
    metrics: { days: 12, maxAlt: "5,364m", totalBudget: "$680 USD", safetyStatus: "100% Verified" },
    desc: "Seamless acclimatization schedule with AI altitude sentinel monitoring, teahouse reservations in Namche Bazaar, and real-time emergency helpline connectivity.",
    image: "/images/destinations/everest/base-camp.jpg",
    slug: "everest-base-camp-ebc",
  },
  {
    title: "7-Day Annapurna Sanctuary & Ghandruk Trail",
    hiker: "Kenji Takahashi (Japan)",
    route: "Pokhara ➔ Nayapul ➔ Ghandruk ➔ Chomrong ➔ ABC (4,130m)",
    metrics: { days: 7, maxAlt: "4,130m", totalBudget: "$340 USD", safetyStatus: "Zero AMS Sickness" },
    desc: "Navigated through blooming rhododendron forests into the 360-degree Annapurna glacier amphitheater with turn-by-turn road graph waypoints.",
    image: "/images/destinations/everest/base-camp.jpg",
    slug: "annapurna-base-camp-abc-sanctuary",
  },
  {
    title: "4-Day Pokhara Adventure & Lakeside Leisure",
    hiker: "Maya & Friends (Australia)",
    route: "Kathmandu ➔ Prithvi Hwy ➔ Sarangkot ➔ Phewa Boating",
    metrics: { days: 4, maxAlt: "1,592m", totalBudget: "$195 USD", safetyStatus: "Full Comfort" },
    desc: "Paragliding over Machhapuchhre reflection, world peace pagoda sunrise hike, and local Newari feast in Bandipur old quarter.",
    image: "/images/destinations/pokhara/fewatal.jpg",
    slug: "phewa-lake-tal-barahi",
  },
]

export default function CaseStudiesSection() {
  return (
    <section className="container-app py-20 relative z-10">
      <SlideUp>
        <div className="text-center max-w-3xl mx-auto mb-14">
          <span className="px-3.5 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-black uppercase tracking-wider">
            Verified Journeys & Blueprints
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
            Real Traveler Journeys Across Nepal
          </h2>
          <p className="text-gray-500 text-sm mt-2">
            Explore verified itineraries, ground truth budget metrics, and altitude profiles from real Himalayan travelers.
          </p>
        </div>
      </SlideUp>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {EXPEDITIONS.map((exp, i) => (
          <HoverCard key={i} className="card-base overflow-hidden rounded-3xl border border-purple-100/80 shadow-xl flex flex-col justify-between bg-white">
            <div>
              <div className="h-52 w-full relative overflow-hidden bg-black">
                <img src={exp.image} alt={exp.title} className="w-full h-full object-cover hover:scale-105 transition-transform duration-700" />
                <span className="absolute top-3 left-3 px-3 py-1 rounded-full bg-black/65 backdrop-blur text-amber-300 text-xs font-bold flex items-center gap-1">
                  <FiMapPin size={12} /> {exp.metrics.maxAlt}
                </span>
              </div>

              <div className="p-6 space-y-3">
                <h3 className="font-bold text-lg text-gray-900 leading-snug">{exp.title}</h3>
                <p className="text-xs text-purple-700 font-semibold">{exp.hiker}</p>
                <p className="text-xs text-gray-600 leading-relaxed">{exp.desc}</p>

                <div className="p-3.5 rounded-2xl bg-purple-50/70 border border-purple-100 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-400 text-[10px] uppercase font-bold">Duration</span>
                    <p className="font-extrabold text-gray-800">{exp.metrics.days} Days</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-[10px] uppercase font-bold">Actual Cost</span>
                    <p className="font-extrabold text-emerald-700">{exp.metrics.totalBudget}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 pt-0">
              <Link
                to={`/destinations/${exp.slug}`}
                className="w-full py-3 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-900 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border border-purple-200"
              >
                View Expedition Blueprint <FiArrowRight size={13} />
              </Link>
            </div>
          </HoverCard>
        ))}
      </div>
    </section>
  )
}
