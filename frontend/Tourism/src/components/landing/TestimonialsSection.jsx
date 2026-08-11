import { motion } from "framer-motion"
import { FiStar, FiCheckCircle } from "react-icons/fi"
import { SlideUp, HoverCard } from "../common/MotionSystem"

const TESTIMONIALS = [
  {
    name: "Elena Rostova",
    country: "Germany",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
    dest: "Annapurna Base Camp",
    review: "The turn-by-turn navigation HUD and real-time altitude sickness guides gave us complete peace of mind. We saved nearly $200 by following the ML budget estimations!",
    rating: 5,
  },
  {
    name: "Aarav Sharma",
    country: "India",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
    dest: "Pashupatinath & Janakpur",
    review: "Having the multi-dialect Nepali & Maithili phrasebook with audio pronunciation made interacting with local temple priests and artisans so rewarding.",
    rating: 5,
  },
  {
    name: "Liam O'Connor",
    country: "Canada",
    avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop&q=80",
    dest: "Everest & Gokyo Lakes",
    review: "When weather dropped unexpectedly, the live hazard alerts and direct police helpline (1144) were immediate. Best all-in-one portal for Nepal travel.",
    rating: 5,
  },
]

export default function TestimonialsSection() {
  return (
    <section className="container-app py-20 bg-gradient-to-b from-transparent via-purple-50/40 to-transparent">
      <SlideUp>
        <div className="text-center max-w-2xl mx-auto mb-14">
          <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
            Verified Community Feedback
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
            Loved by Himalayan Explorers Worldwide
          </h2>
          <p className="text-gray-500 text-sm mt-2">
            Real feedback from backpackers, mountaineers, and cultural travelers.
          </p>
        </div>
      </SlideUp>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {TESTIMONIALS.map((t, idx) => (
          <HoverCard key={idx} className="card-base p-7 rounded-3xl border border-purple-100/80 shadow-xl bg-white flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center gap-1 text-amber-500">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <FiStar key={i} size={16} className="fill-amber-400 text-amber-400" />
                ))}
              </div>
              <p className="text-gray-700 text-xs sm:text-sm leading-relaxed italic">
                "{t.review}"
              </p>
            </div>

            <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
              <img src={t.avatar} alt={t.name} className="w-11 h-11 rounded-full object-cover border-2 border-purple-200" />
              <div>
                <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1">
                  {t.name} <FiCheckCircle className="text-emerald-500" size={13} />
                </h4>
                <p className="text-[11px] text-gray-400">{t.country} · Visited <b>{t.dest}</b></p>
              </div>
            </div>
          </HoverCard>
        ))}
      </div>
    </section>
  )
}
