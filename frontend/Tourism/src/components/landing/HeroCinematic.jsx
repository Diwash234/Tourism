import React, { useState, useEffect, useMemo, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiArrowRight, FiChevronLeft, FiChevronRight, FiCompass, FiMapPin,
  FiStar, FiTrendingUp, FiImage, FiShield,
} from "react-icons/fi"
import usePublicConfig from "../../hooks/usePublicConfig"

// Bundled Himalayan fallbacks so the hero is never empty (no uploads / offline).
const FALLBACK_SLIDES = [
  { id: "fb-everest", title: "EVEREST", kicker: "Solukhumbu · 8,849 m", subtitle: "Everest Base Camp & Khumbu Peaks", tagline: "Journey into the heart of the Himalayas at the roof of the world.", link_slug: "everest-base-camp", image: "/images/destinations/everest/base-camp.jpg", overlay: 62, focal_point: "top", duration: 7 },
  { id: "fb-annapurna", title: "ANNAPURNA", kicker: "Kaski · 4,130 m", subtitle: "Alpine Sanctuary & Rhododendron Trails", tagline: "Glacier amphitheatres and Gurung heritage villages.", link_slug: "annapurna-base-camp", image: "/images/destinations/annapurna/trek.jpg", overlay: 60, focal_point: "center", duration: 7 },
  { id: "fb-mustang", title: "MUSTANG", kicker: "Mustang · 3,840 m", subtitle: "Lo Manthang Walled Kingdom", tagline: "Rain-shadow desert canyons and ancient cliff caves.", link_slug: "lo-manthang", image: "/images/destinations/mustang/lo-manthang.jpg", overlay: 60, focal_point: "center", duration: 7 },
]

const FOCAL = { top: "center 25%", center: "center center", bottom: "center 75%" }

// Guarantees legible text over any photograph: a bottom + left navy scrim whose
// alpha is driven by the admin-configured overlay strength, plus a vignette.
const scrimStyle = (alpha) => ({
  background: [
    `linear-gradient(to top, rgba(7,12,32,${Math.min(0.97, alpha + 0.28)}) 0%, rgba(7,12,32,${alpha}) 42%, rgba(7,12,32,${alpha * 0.45}) 78%, rgba(7,12,32,0.12) 100%)`,
    `linear-gradient(to right, rgba(7,12,32,${Math.min(0.94, alpha + 0.18)}) 0%, rgba(7,12,32,${alpha * 0.5}) 55%, rgba(7,12,32,0.08) 100%)`,
    `radial-gradient(120% 90% at 50% 10%, rgba(7,12,32,0) 55%, rgba(7,12,32,0.5) 100%)`,
  ].join(", "),
})

export default function HeroCinematic() {
  const navigate = useNavigate()
  const { hero_slides, catalog } = usePublicConfig()
  const slides = useMemo(() => (hero_slides?.length ? hero_slides : FALLBACK_SLIDES), [hero_slides])
  const [idx, setIdx] = useState(0)
  const [paused, setPaused] = useState(false)
  const reduced = useRef(false)

  useEffect(() => {
    reduced.current = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false
  }, [])

  const active = slides[Math.min(idx, slides.length - 1)]
  const alpha = ((active?.overlay ?? 60) || 60) / 100

  // Autoplay, honouring reduced-motion + hover pause.
  useEffect(() => {
    if (paused || reduced.current || slides.length < 2) return
    const t = setInterval(() => setIdx((p) => (p + 1) % slides.length), (active?.duration || 7) * 1000)
    return () => clearInterval(t)
  }, [paused, slides.length, active?.duration, idx])

  const go = (n) => setIdx((n + slides.length) % slides.length)

  const destCount = catalog?.destination_count
  const TICKER = [
    { icon: FiMapPin, label: `${(destCount ?? 8500).toLocaleString()}+ recorded destinations`, tint: "text-[#8BB2FC]" },
    { icon: FiStar, label: "77 districts · 7 provinces", tint: "text-[#70B1AB]" },
    { icon: FiTrendingUp, label: "8,849 m — Everest, roof of the world", tint: "text-[#D9C7A3]" },
    { icon: FiImage, label: "20,000+ verified real photographs", tint: "text-[#8BB2FC]" },
    { icon: FiShield, label: "Live safety, emergency & SOS network", tint: "text-[#70B1AB]" },
    { icon: FiCompass, label: "AI itineraries, budgets & road routes", tint: "text-[#D9C7A3]" },
  ]

  return (
    <section
      className="relative w-full min-h-[88vh] sm:min-h-[92vh] bg-[#070c20] text-white overflow-hidden"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-roledescription="carousel"
      aria-label="Featured Himalayan destinations"
    >
      {/* Layered photographic backdrop (crossfade + Ken Burns on active) */}
      {slides.map((s, i) => (
        <img
          key={s.id || i}
          src={s.image}
          alt={s.subtitle || s.title}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-[1200ms] ease-out ${i === idx ? "opacity-100 kenburns" : "opacity-0"}`}
          style={{ objectPosition: FOCAL[s.focal_point] || FOCAL.center }}
          loading={i === 0 ? "eager" : "lazy"}
          onError={(e) => { e.currentTarget.style.visibility = "hidden" }}
        />
      ))}

      {/* Legibility scrim driven by admin overlay strength */}
      <div className="absolute inset-0" style={scrimStyle(alpha)} aria-hidden="true" />

      {/* Top meta bar */}
      <div className="relative z-10 flex items-center justify-between px-6 sm:px-10 lg:px-14 pt-6">
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur border border-white/20 text-[11px] font-black uppercase tracking-[0.18em] text-[#8BB2FC]">
          🇳 Digital Nepal Tourism · Himalayan Index
        </span>
        <div className="flex items-center gap-2">
          <button onClick={() => go(idx - 1)} aria-label="Previous destination" className="p-2.5 rounded-full bg-white/10 hover:bg-white/25 backdrop-blur border border-white/20 transition-all"><FiChevronLeft size={18} /></button>
          <span className="px-2 text-xs font-mono font-bold text-[#D9C7A3]">0{idx + 1} / 0{slides.length}</span>
          <button onClick={() => go(idx + 1)} aria-label="Next destination" className="p-2.5 rounded-full bg-white/10 hover:bg-white/25 backdrop-blur border border-white/20 transition-all"><FiChevronRight size={18} /></button>
        </div>
      </div>

      {/* Headline + side index cards */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-10 items-end px-6 sm:px-10 lg:px-14 pt-10 pb-8 my-auto max-w-7xl mx-auto min-h-[58vh]">
        <div className="lg:col-span-7 space-y-5">
          <AnimatePresence mode="wait">
            <motion.div
              key={active?.id ?? idx}
              initial={{ opacity: 0, y: 26 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -18 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
              className="space-y-5"
            >
              {active?.kicker && (
                <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#D9C7A3] text-[#0d1330] text-xs font-black uppercase tracking-widest shadow-lg" style={{ textShadow: "none" }}>
                  {active.kicker}
                </span>
              )}
              <h1 className="font-ubuntu text-5xl sm:text-7xl lg:text-8xl font-bold tracking-tighter leading-none" style={{ textShadow: "0 2px 24px rgba(7,12,32,0.65)" }}>
                {active?.title}
              </h1>
              <h2 className="font-ubuntu text-2xl sm:text-3xl font-bold text-[#8BB2FC] tracking-tight" style={{ textShadow: "0 1px 14px rgba(7,12,32,0.7)" }}>
                {active?.subtitle}
              </h2>
              <p className="max-w-xl text-sm sm:text-base text-stone-100/90 font-medium leading-relaxed" style={{ textShadow: "0 1px 10px rgba(7,12,32,0.8)" }}>
                {active?.tagline}
              </p>
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={() => navigate(`/destinations/${active?.link_slug || ""}`)}
                  className="px-8 py-3.5 rounded-2xl bg-[#D99048] hover:bg-amber-500 text-slate-950 font-black text-sm shadow-xl shadow-amber-500/25 transition-all hover:scale-[1.04] flex items-center gap-2"
                >
                  <FiCompass size={18} /> Explore {active?.title} <FiArrowRight size={16} />
                </button>
                <button
                  onClick={() => navigate("/destinations")}
                  className="px-6 py-3.5 rounded-2xl bg-white/10 hover:bg-white/25 text-white font-bold text-sm border border-white/25 backdrop-blur shadow-lg transition-all"
                >
                  Browse all destinations
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Side index cards: jump to the other slides */}
        <div className="lg:col-span-5 hidden md:flex items-center gap-4 overflow-x-auto pb-2 lg:justify-end">
          {slides.filter((_, i) => i !== idx).slice(0, 2).map((s) => (
            <button
              key={s.id || s.title}
              onClick={() => setIdx(slides.indexOf(s))}
              className="relative w-44 h-60 rounded-3xl overflow-hidden border border-white/20 shadow-2xl shrink-0 text-left group"
            >
              <img src={s.image} alt={s.title} loading="lazy" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" onError={(e) => { e.currentTarget.style.visibility = "hidden" }} />
              <div className="absolute inset-0 bg-gradient-to-t from-[#070c20] via-[#070c20]/30 to-transparent" aria-hidden="true" />
              <div className="absolute bottom-3 left-3 right-3">
                <p className="text-sm font-black text-white drop-shadow">{s.title}</p>
                <p className="text-[10px] text-[#8BB2FC] font-bold flex items-center gap-1">Explore <FiArrowRight size={10} /></p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Bottom: slide dots + data ticker */}
      <div className="relative z-10 px-6 sm:px-10 lg:px-14 pb-6 space-y-4">
        <div className="flex items-center gap-2">
          {slides.map((s, i) => (
            <button
              key={s.id || i}
              onClick={() => go(i)}
              aria-label={`Go to slide ${i + 1}: ${s.title}`}
              className={`h-1.5 rounded-full transition-all ${i === idx ? "w-10 bg-[#D9C7A3]" : "w-4 bg-white/30 hover:bg-white/50"}`}
            />
          ))}
        </div>
        <div
          className="w-full overflow-hidden border-t border-white/10"
          style={{ maskImage: "linear-gradient(to right, transparent, black 4%, black 96%, transparent)", WebkitMaskImage: "linear-gradient(to right, transparent, black 4%, black 96%, transparent)" }}
        >
          <div className="ticker-track gap-10 py-3">
            {[...TICKER, ...TICKER].map((t, i) => (
              <span key={i} className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-stone-200/80 shrink-0">
                <t.icon size={13} className={t.tint} /> {t.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
