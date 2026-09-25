import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { FiArrowRight, FiChevronLeft, FiChevronRight, FiCompass, FiMapPin } from "react-icons/fi"
import usePublicConfig from "../../hooks/usePublicConfig"
import SearchBar from "../common/SearchBar"

const FALLBACK_SLIDES = [
  { id: "everest", title: "Everest", kicker: "Khumbu · Solukhumbu", subtitle: "A closer look at the high Himalaya", tagline: "Begin with a recorded destination, then shape the route around your own pace.", link_slug: "everest-base-camp", image: "/images/destinations/everest/base-camp.jpg" },
  { id: "annapurna", title: "Annapurna", kicker: "Gandaki · Kaski", subtitle: "Trails, lakes and mountain villages", tagline: "Explore the details that help you decide when and how to go.", link_slug: "annapurna-base-camp", image: "/images/destinations/annapurna/trek.jpg" },
  { id: "mustang", title: "Upper Mustang", kicker: "Kali Gandaki · Mustang", subtitle: "High-valley heritage and open landscapes", tagline: "A calm starting point for comparing places, routes and seasons.", link_slug: "lo-manthang", image: "/images/destinations/mustang/lo-manthang.jpg" },
]

const FALLBACK_COUNT = null

export default function HeroCinematic() {
  const navigate = useNavigate()
  const { hero_slides, catalog } = usePublicConfig()
  const slides = useMemo(() => (hero_slides?.length ? hero_slides : FALLBACK_SLIDES), [hero_slides])
  const [index, setIndex] = useState(0)
  const active = slides[Math.min(index, Math.max(0, slides.length - 1))]

  useEffect(() => {
    if (slides.length < 2 || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return undefined
    const duration = Math.max(4, Math.min(30, Number(active?.duration) || 8))
    const timer = setTimeout(() => setIndex((value) => (value + 1) % slides.length), duration * 1000)
    return () => clearTimeout(timer)
  }, [slides.length, index, active?.duration])

  const go = (value) => setIndex((value + slides.length) % slides.length)
  const count = catalog?.destination_count ?? FALLBACK_COUNT
  const overlay = Number.isFinite(Number(active?.overlay)) ? Number(active.overlay) : 0.7

  return (
    <section className="relative min-h-[520px] bg-[var(--ny-green-deepest)] text-white sm:min-h-[620px] lg:min-h-[680px]" aria-roledescription="carousel" aria-label="Featured destinations">
      <div className="absolute inset-0 overflow-hidden">
        {slides.map((slide, slideIndex) => <img key={slide.id || slideIndex} src={slide.image} alt={slide.subtitle || slide.title} style={{ objectPosition: slide.focal_point || "center" }} className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 ${slideIndex === index ? "opacity-100" : "opacity-0"}`} loading={slideIndex === 0 ? "eager" : "lazy"} />)}
        <div className="absolute inset-0" style={{ background: `linear-gradient(90deg, rgba(4,42,36,${Math.max(0.35, Math.min(0.96, overlay))}) 0%, rgba(4,42,36,${Math.max(0.18, Math.min(0.8, overlay - 0.25))}) 48%, rgba(4,42,36,${Math.max(0.08, Math.min(0.5, overlay - 0.55))}) 100%)` }} aria-hidden="true" />
      </div>
      <div className="container-app relative flex min-h-[520px] flex-col justify-between py-7 sm:min-h-[620px] sm:py-10 lg:min-h-[680px]">
        <div className="flex items-center justify-between gap-4"><span className="ny-kicker !border !border-white/20 !bg-white/10 !text-[#BDEBD9]"><FiMapPin size={13} aria-hidden="true" /> Nepal Yatra</span>{slides.length > 1 && <div className="flex items-center gap-2"><button type="button" onClick={() => go(index - 1)} className="grid h-11 w-11 place-items-center rounded-full border border-white/25 bg-white/10 transition hover:bg-white/20" aria-label="Previous featured destination"><FiChevronLeft size={18} aria-hidden="true" /></button><span className="min-w-12 text-center text-xs text-[#C7D9D2]">{index + 1} / {slides.length}</span><button type="button" onClick={() => go(index + 1)} className="grid h-11 w-11 place-items-center rounded-full border border-white/25 bg-white/10 transition hover:bg-white/20" aria-label="Next featured destination"><FiChevronRight size={18} aria-hidden="true" /></button></div>}</div>
        <div className="max-w-3xl pb-8"><p className="text-sm font-semibold text-[#BDEBD9]">{active?.kicker || "Explore Nepal"}</p><h1 className="mt-3 !text-4xl !text-white sm:!text-5xl lg:!text-6xl">{active?.title || "Explore Nepal"}</h1><p className="mt-3 text-xl font-semibold text-[#DCEBE5] sm:text-2xl">{active?.subtitle || "Discover places worth planning around"}</p><p className="mt-4 max-w-xl text-base leading-7 text-[#EAF2EF]">{active?.tagline || "Find destinations, compare practical information and build a trip with confidence."}</p><div className="mt-7 flex flex-wrap gap-3"><button type="button" onClick={() => navigate(active?.link_slug ? `/destinations/${active.link_slug}` : "/destinations")} className="ny-btn ny-btn-accent"><FiCompass size={17} aria-hidden="true" />Explore Nepal <FiArrowRight size={16} aria-hidden="true" /></button><button type="button" onClick={() => navigate("/itinerary")} className="ny-btn border border-white/30 bg-transparent text-white hover:border-white hover:bg-white/10">Plan a trip</button></div><div className="mt-5 max-w-xl"><SearchBar placeholder="Search destinations, places or districts" /></div></div>
        <div className="flex flex-wrap items-center gap-4 border-t border-white/20 pt-4 text-sm text-[#C7D9D2]"><span>Explore · Discover · Plan · Stay safe</span>{count != null && <><span className="text-white/30">·</span><span>{Number(count).toLocaleString()} recorded destinations</span></>}</div>
      </div>
    </section>
  )
}
