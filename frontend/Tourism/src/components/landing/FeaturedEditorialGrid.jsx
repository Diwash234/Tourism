import React from "react"
import { Link, useNavigate } from "react-router-dom"
import { FiArrowRight, FiStar, FiCompass } from "react-icons/fi"

export default function FeaturedEditorialGrid({ destinations = [], featuredCards = [] }) {
  const navigate = useNavigate()

  // Use provided featured destinations or fallback to landmark destinations
  const list = (featuredCards.length ? featuredCards : destinations).slice(0, 3)

  const main = list[0] || {
    destination_name: "Mount Everest Base Camp",
    destination_slug: "everest-base-camp",
    title: "Mount Everest Base Camp",
    short_description: "Trek through Khumbu valley beneath 8,849m peaks, Buddhist monasteries, and Sherpa heritage.",
    image_url: "/images/destinations/everest/base-camp.jpg",
    destination_city: "Solukhumbu, Koshi",
    destination_rating: 4.9,
    cta_label: "Explore Everest",
    cta_url: "/destinations/everest-base-camp"
  }

  const side1 = list[1] || {
    destination_name: "Annapurna Sanctuary",
    destination_slug: "annapurna-base-camp",
    title: "Annapurna Sanctuary",
    short_description: "Circling 4,130m alpine amphitheatres through rhododendron forests.",
    image_url: "/images/destinations/annapurna/trek.jpg",
    destination_city: "Kaski, Gandaki",
    destination_rating: 4.8,
    cta_label: "Explore Annapurna",
    cta_url: "/destinations/annapurna-base-camp"
  }

  const side2 = list[2] || {
    destination_name: "Upper Mustang Kingdom",
    destination_slug: "lo-manthang-mustang",
    title: "Upper Mustang Kingdom",
    short_description: "Walled medieval Buddhist city of Lo Manthang in rain-shadow desert canyons.",
    image_url: "/images/destinations/mustang/lo-manthang.jpg",
    destination_city: "Mustang, Gandaki",
    destination_rating: 4.8,
    cta_label: "Explore Mustang",
    cta_url: "/destinations/lo-manthang-mustang"
  }

  return (
    <section className="py-16 container-app max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-[#D9C7A3] text-[#102A2E] text-xs font-black uppercase tracking-widest">
            HANDPICKED WONDERS
          </span>
          <h2 className="text-3xl sm:text-4xl font-black text-[#172022] mt-2 tracking-tight">
            Featured Himalayan Destinations
          </h2>
          <p className="text-sm text-[#697675] mt-1">
            Editorial showcase of Nepal's most iconic mountain peaks, sanctuaries, and forbidden kingdoms.
          </p>
        </div>

        <Link
          to="/destinations"
          className="px-5 py-2.5 rounded-2xl bg-[#102A2E] hover:bg-[#1D5146] text-white font-bold text-xs flex items-center gap-1.5 shrink-0 shadow-md transition-all"
        >
          View All Destinations <FiArrowRight size={14} />
        </Link>
      </div>

      {/* Editorial Asymmetric Grid: 50% Main Card + 25%/25% Stacked Side Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main 50% Featured Card (col-span-6) */}
        <div
          onClick={() => navigate(main.cta_url || `/destinations/${main.destination_slug || "everest-base-camp"}`)}
          className="lg:col-span-6 relative min-h-[460px] sm:min-h-[520px] rounded-3xl overflow-hidden bg-[#102A2E] text-white p-8 flex flex-col justify-end shadow-2xl cursor-pointer group"
        >
          <img
            src={main.image_url || main.effective_image_url || main.cover_image_url || "/images/destinations/everest/base-camp.jpg"}
            alt={main.title || main.destination_name}
            className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/50 to-transparent opacity-90" />

          <div className="relative z-10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-3 py-1 rounded-full bg-[#D9C7A3] text-[#102A2E] text-[10px] font-black uppercase tracking-wider">
                📍 {main.destination_city || main.city || "Nepal"}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-black/60 text-amber-300 text-xs font-bold flex items-center gap-1 backdrop-blur">
                <FiStar size={12} className="fill-amber-300" /> {main.destination_rating || main.average_rating || 4.9}
              </span>
            </div>

            <h3 className="text-3xl sm:text-4xl font-black text-white group-hover:text-[#D9C7A3] transition-colors">
              {main.title || main.destination_name}
            </h3>

            <p className="text-xs sm:text-sm text-stone-200/90 line-clamp-2 leading-relaxed">
              {main.short_description || main.description}
            </p>

            <div className="pt-3 border-t border-white/15 flex items-center justify-between">
              <span className="text-xs font-bold text-[#D9C7A3]">Himalayan Landmark</span>
              <span className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#D99048] text-slate-950 font-black text-xs group-hover:bg-amber-500 transition-all shadow">
                {main.cta_label || "Explore Destination"} <FiArrowRight size={14} />
              </span>
            </div>
          </div>
        </div>

        {/* Right Side Stacked Cards (col-span-6: two col-span-6 child cards) */}
        <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Side Card 1 */}
          <div
            onClick={() => navigate(side1.cta_url || `/destinations/${side1.destination_slug || "annapurna-base-camp"}`)}
            className="relative min-h-[460px] sm:min-h-[520px] rounded-3xl overflow-hidden bg-[#102A2E] text-white p-6 flex flex-col justify-end shadow-xl cursor-pointer group"
          >
            <img
              src={side1.image_url || side1.effective_image_url || side1.cover_image_url || "/images/destinations/annapurna/trek.jpg"}
              alt={side1.title || side1.destination_name}
              className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/60 to-transparent opacity-90" />

            <div className="relative z-10 space-y-2">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full bg-white/20 text-stone-100 text-[10px] font-bold backdrop-blur">
                  📍 {side1.destination_city || side1.city || "Gandaki"}
                </span>
                <span className="text-xs font-bold text-amber-300 flex items-center gap-1">
                  <FiStar size={11} className="fill-amber-300" /> {side1.destination_rating || 4.8}
                </span>
              </div>

              <h4 className="text-2xl font-black text-white group-hover:text-[#D9C7A3] transition-colors">
                {side1.title || side1.destination_name}
              </h4>

              <p className="text-xs text-stone-300/90 line-clamp-2 leading-relaxed">
                {side1.short_description || side1.description}
              </p>

              <div className="pt-2 border-t border-white/15 flex items-center justify-between">
                <span className="text-[11px] font-bold text-[#D9C7A3]">Alpine Sanctuary</span>
                <span className="text-xs font-bold text-[#D99048] flex items-center gap-1">
                  Explore <FiArrowRight size={12} />
                </span>
              </div>
            </div>
          </div>

          {/* Side Card 2 */}
          <div
            onClick={() => navigate(side2.cta_url || `/destinations/${side2.destination_slug || "lo-manthang-mustang"}`)}
            className="relative min-h-[460px] sm:min-h-[520px] rounded-3xl overflow-hidden bg-[#102A2E] text-white p-6 flex flex-col justify-end shadow-xl cursor-pointer group"
          >
            <img
              src={side2.image_url || side2.effective_image_url || side2.cover_image_url || "/images/destinations/mustang/lo-manthang.jpg"}
              alt={side2.title || side2.destination_name}
              className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/60 to-transparent opacity-90" />

            <div className="relative z-10 space-y-2">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full bg-white/20 text-stone-100 text-[10px] font-bold backdrop-blur">
                  📍 {side2.destination_city || side2.city || "Mustang"}
                </span>
                <span className="text-xs font-bold text-amber-300 flex items-center gap-1">
                  <FiStar size={11} className="fill-amber-300" /> {side2.destination_rating || 4.8}
                </span>
              </div>

              <h4 className="text-2xl font-black text-white group-hover:text-[#D9C7A3] transition-colors">
                {side2.title || side2.destination_name}
              </h4>

              <p className="text-xs text-stone-300/90 line-clamp-2 leading-relaxed">
                {side2.short_description || side2.description}
              </p>

              <div className="pt-2 border-t border-white/15 flex items-center justify-between">
                <span className="text-[11px] font-bold text-[#D9C7A3]">Rain-Shadow Desert</span>
                <span className="text-xs font-bold text-[#D99048] flex items-center gap-1">
                  Explore <FiArrowRight size={12} />
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
