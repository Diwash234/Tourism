import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { FiCompass, FiArrowRight, FiStar, FiMapPin, FiChevronLeft, FiChevronRight } from "react-icons/fi"

const HERO_TEMPLATES = [
  {
    id: "everest",
    title: "NEPAL",
    subtitle: "Everest Base Camp & Khumbu Peaks",
    tagline: "Journey into the heart of the Himalayas at 8,849 meters",
    image: "/images/destinations/everest/base-camp.jpg",
    slug: "everest-base-camp",
    city: "Solukhumbu, Koshi",
    altitude: "8,849 m",
    rating: 4.9,
    sideCards: [
      { name: "Annapurna Sanctuary", rating: 4.8, img: "/images/destinations/annapurna/trek.jpg", slug: "annapurna-base-camp" },
      { name: "Upper Mustang Kingdom", rating: 4.8, img: "/images/destinations/mustang/lo-manthang.jpg", slug: "lo-manthang-mustang" }
    ]
  },
  {
    id: "annapurna",
    title: "ANNAPURNA",
    subtitle: "Alpine Sanctuary & Rhododendron Trails",
    tagline: "Explore 4,130m glacier amphitheatres and Gurung heritage villages",
    image: "/images/destinations/annapurna/trek.jpg",
    slug: "annapurna-base-camp",
    city: "Kaski, Gandaki",
    altitude: "4,130 m",
    rating: 4.8,
    sideCards: [
      { name: "Upper Mustang Kingdom", rating: 4.8, img: "/images/destinations/mustang/lo-manthang.jpg", slug: "lo-manthang-mustang" },
      { name: "Chitwan Wildlife Safari", rating: 4.7, img: "/images/destinations/chitwan/safari.jpg", slug: "chitwan-national-park" }
    ]
  },
  {
    id: "mustang",
    title: "MUSTANG",
    subtitle: "Lo Manthang Walled Kingdom",
    tagline: "Rain-shadow desert canyons, ancient cliff caves, and Tibetan culture",
    image: "/images/destinations/mustang/lo-manthang.jpg",
    slug: "lo-manthang-mustang",
    city: "Mustang, Gandaki",
    altitude: "3,840 m",
    rating: 4.8,
    sideCards: [
      { name: "Rara Alpine Lake", rating: 4.9, img: "/images/destinations/rara/alpine-lake.jpg", slug: "rara-lake" },
      { name: "Kathmandu Durbar Square", rating: 4.7, img: "/images/destinations/kathmandu/durbar-square.jpg", slug: "kathmandu-durbar-square" }
    ]
  },
  {
    id: "chitwan",
    title: "CHITWAN",
    subtitle: "Subtropical Jungle & One-Horned Rhinos",
    tagline: "Wilderness elephant safaris, Tharu culture, and tiger reserves",
    image: "/images/destinations/chitwan/safari.jpg",
    slug: "chitwan-national-park",
    city: "Chitwan, Bagmati",
    altitude: "415 m",
    rating: 4.7,
    sideCards: [
      { name: "Rara Alpine Lake", rating: 4.9, img: "/images/destinations/rara/alpine-lake.jpg", slug: "rara-lake" },
      { name: "Everest Base Camp", rating: 4.9, img: "/images/destinations/everest/base-camp.jpg", slug: "everest-base-camp" }
    ]
  },
  {
    id: "rara",
    title: "RARA LAKE",
    subtitle: "Queen of Lakes in Wild West Nepal",
    tagline: "Crystal alpine waters surrounded by pine forests at 2,990 meters",
    image: "/images/destinations/rara/alpine-lake.jpg",
    slug: "rara-lake",
    city: "Mugu, Karnali",
    altitude: "2,990 m",
    rating: 4.9,
    sideCards: [
      { name: "Everest Base Camp", rating: 4.9, img: "/images/destinations/everest/base-camp.jpg", slug: "everest-base-camp" },
      { name: "Annapurna Sanctuary", rating: 4.8, img: "/images/destinations/annapurna/trek.jpg", slug: "annapurna-base-camp" }
    ]
  }
]

export default function HeroTemplateCarousel() {
  const [activeIdx, setActiveIdx] = useState(0)
  const navigate = useNavigate()
  const activeTemplate = HERO_TEMPLATES[activeIdx]

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % HERO_TEMPLATES.length)
    }, 6000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full min-h-[85vh] sm:min-h-[90vh] bg-[#102A2E] text-white flex flex-col justify-between p-6 sm:p-10 lg:p-12 overflow-hidden group">
      {/* Background Active Template Image */}
      <img
        src={activeTemplate.image}
        alt={activeTemplate.subtitle}
        className="absolute inset-0 w-full h-full object-cover object-center transform group-hover:scale-105 transition-transform duration-1000 ease-out"
      />

      {/* Accessible Dual-Axis Dark Gradient Protection Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/65 to-[#102A2E]/30 opacity-95" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#102A2E]/90 via-[#102A2E]/40 to-transparent" />

      {/* Top Template Navigation Bar */}
      <div className="relative z-10 flex items-center justify-between pt-2">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#D9C7A3] text-[#102A2E] text-xs font-black uppercase tracking-widest shadow-lg">
          🇳🇵 {activeTemplate.city} · Altitude {activeTemplate.altitude}
        </div>

        {/* Carousel Arrow Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveIdx((prev) => (prev - 1 + HERO_TEMPLATES.length) % HERO_TEMPLATES.length)}
            className="p-2.5 rounded-full bg-white/15 hover:bg-white/30 text-white backdrop-blur border border-white/20 transition-all"
            aria-label="Previous template"
          >
            <FiChevronLeft size={18} />
          </button>
          <span className="text-xs font-mono text-[#D9C7A3] px-2 font-bold">
            0{activeIdx + 1} / 0{HERO_TEMPLATES.length}
          </span>
          <button
            onClick={() => setActiveIdx((prev) => (prev + 1) % HERO_TEMPLATES.length)}
            className="p-2.5 rounded-full bg-white/15 hover:bg-white/30 text-white backdrop-blur border border-white/20 transition-all"
            aria-label="Next template"
          >
            <FiChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Middle Layout: Hero Title + Right Floating Side Cards (Dribbble/99designs Template Style) */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-end my-auto py-8">
        {/* Left Side: Bold Big Title & Abstract */}
        <div className="lg:col-span-7 space-y-4">
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-black text-white tracking-tighter drop-shadow-lg leading-none">
            {activeTemplate.title}
          </h1>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#D9C7A3] tracking-tight">
            {activeTemplate.subtitle}
          </h2>
          <p className="text-sm sm:text-base text-stone-200/90 max-w-xl font-medium leading-relaxed drop-shadow">
            {activeTemplate.tagline}
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-3">
            <button
              onClick={() => navigate(`/destinations/${activeTemplate.slug}`)}
              className="px-8 py-3.5 rounded-2xl bg-[#D99048] hover:bg-amber-600 text-slate-950 font-black text-sm shadow-xl shadow-amber-500/20 transition-all hover:scale-105 flex items-center gap-2"
            >
              <FiCompass size={18} /> Explore {activeTemplate.title} <FiArrowRight size={16} />
            </button>
            <button
              onClick={() => navigate(`/navigation?dest=${encodeURIComponent(activeTemplate.subtitle)}`)}
              className="px-6 py-3.5 rounded-2xl bg-white/15 hover:bg-white/25 text-white font-bold text-sm border border-white/20 backdrop-blur shadow-lg transition-all"
            >
              Get Road Route
            </button>
          </div>
        </div>

        {/* Right Side: Floating Card Carousel Previews (Matching Dribbble Reference) */}
        <div className="lg:col-span-5 hidden sm:flex items-center gap-4 overflow-x-auto pb-2">
          {activeTemplate.sideCards.map((sc, i) => (
            <div
              key={i}
              onClick={() => navigate(`/destinations/${sc.slug}`)}
              className="relative w-48 h-64 rounded-3xl overflow-hidden border border-white/20 shadow-2xl shrink-0 cursor-pointer group/card"
            >
              <img
                src={sc.img}
                alt={sc.name}
                className="w-full h-full object-cover group-hover/card:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-transparent to-transparent opacity-90" />
              <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-black/60 text-amber-300 text-[10px] font-bold flex items-center gap-1 backdrop-blur">
                <FiStar size={10} className="fill-amber-300" /> {sc.rating}
              </div>
              <div className="absolute bottom-3 left-3 right-3 space-y-1 text-white">
                <p className="text-xs font-black line-clamp-1 group-hover/card:text-[#D9C7A3] transition-colors">{sc.name}</p>
                <span className="text-[10px] text-amber-300 font-bold flex items-center gap-0.5">
                  Explore <FiArrowRight size={10} />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Template Switcher Tabs (Dribbble Glassmorphism Style) */}
      <div className="relative z-10 bg-white/10 backdrop-blur-xl p-2 sm:p-3 rounded-3xl border border-white/20 flex items-center justify-between overflow-x-auto gap-2">
        <div className="flex items-center gap-2">
          {HERO_TEMPLATES.map((tmpl, idx) => (
            <button
              key={tmpl.id}
              onClick={() => setActiveIdx(idx)}
              className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all whitespace-nowrap ${
                activeIdx === idx
                  ? "bg-[#D9C7A3] text-[#102A2E] shadow-lg font-black"
                  : "text-white/80 hover:bg-white/10 hover:text-white"
              }`}
            >
              {tmpl.title}
            </button>
          ))}
        </div>

        <button
          onClick={() => navigate("/destinations")}
          className="hidden md:flex items-center gap-1.5 px-4 py-2 rounded-2xl bg-[#D99048] text-slate-950 font-black text-xs shrink-0 hover:bg-amber-500 transition-colors"
        >
          All Destinations <FiArrowRight size={12} />
        </button>
      </div>
    </div>
  )
}
