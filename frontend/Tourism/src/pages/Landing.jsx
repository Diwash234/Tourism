import { useState, useEffect, useCallback } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  FiMapPin, FiShield, FiDollarSign, FiNavigation, FiStar,
  FiCompass, FiArrowRight, FiCheckCircle, FiPhoneCall, FiSun
} from "react-icons/fi"
import { useI18n } from "../i18n"

import SearchBar from "../components/common/SearchBar"
import DestinationCard from "../components/cards/DestinationCard"
import DestinationCardSkeleton from "../components/cards/DestinationCardSkeleton"
import FAQAccordion from "../components/common/FAQAccordion"
import NepalHighlights from "../components/dashboard/NepalHighlights"
import NepalExperienceSection from "../components/dashboard/NepalExperienceSection"
import NationalSymbols from "../components/dashboard/NationalSymbols"
import HeroEffects from "../components/dashboard/HeroEffects"
import destinationApi from "../api/destinationApi"
import userApi from "../api/userApi"
import usePublicConfig from "../hooks/usePublicConfig"
import VisitorNoticeBanner from "../components/common/VisitorNoticeBanner"
import { CMSExtras } from "../components/cms/CMSBlock"
import {
  FadeIn, SlideUp, Stagger, StaggerItem, HoverCard,
  BurnGlowBadge, InteractiveHeroCanvas
} from "../components/common/MotionSystem"
import CaseStudiesSection from "../components/landing/CaseStudiesSection"
import TestimonialsSection from "../components/landing/TestimonialsSection"
import StickyCTA from "../components/common/StickyCTA"
import ProvinceMarquee from "../components/landing/ProvinceMarquee"

const PROVINCES = [
  { name: "Koshi Province", city: "Biratnagar / Ilam", code: "koshi" },
  { name: "Madhesh Province", city: "Janakpurdham", code: "madhesh" },
  { name: "Bagmati Province", city: "Kathmandu Valley", code: "bagmati" },
  { name: "Gandaki Province", city: "Pokhara / Annapurna", code: "gandaki" },
  { name: "Lumbini Province", city: "Lumbini / Butwal", code: "lumbini" },
  { name: "Karnali Province", city: "Rara / Surkhet", code: "karnali" },
  { name: "Sudurpashchim", city: "Dhangadhi / Khaptad", code: "sudurpashchim" },
]

const FEATURES = [
  {
    icon: FiMapPin,
    title: "Recorded destinations",
    desc: "Browse places stored in the Nepal catalogue. Missing city, season, or budget fields stay Not recorded until an administrator adds them.",
  },
  {
    icon: FiDollarSign,
    title: "Recorded travel costs",
    desc: "Budgets appear only when a destination or published package has a stored NPR amount. Empty costs are never invented.",
  },
  {
    icon: FiShield,
    title: "Emergency directory",
    desc: "Nearest hospitals and police from the recorded directory, plus official national numbers 1144, 100 and 102.",
  },
  {
    icon: FiNavigation,
    title: "Navigation for mapped places",
    desc: "Routes open only for destinations that have recorded Nepal coordinates. Unmapped places stay off the map.",
  },
]

const FAQ_ITEMS = [
  {
    question: "Why use this Nepal Tourism portal over generic search engines?",
    answer: "This portal lists destinations, emergency contacts, and published packages that are stored in the database. If a field is empty it shows Not recorded instead of inventing a value."
  },
  {
    question: "How accurate are the travel budget estimates?",
    answer: "Only recorded NPR amounts from destination entry fees, budget rows, or published packages are shown. Missing costs stay Not recorded until an administrator updates them."
  },
  {
    question: "What should I do during high-altitude or medical emergencies?",
    answer: "Open Emergency to see recorded nearby hospitals and police. For immediate dispatch use official national numbers: Tourist Police 1144, Police 100, Ambulance 102."
  },
  {
    question: "Can community travelers submit new hidden gems?",
    answer: "Yes. Travelers can submit a place with photos and location. Submissions stay pending until an administrator reviews and publishes them."
  },
  {
    question: "Does the navigation work for remote Himalayan trekking routes?",
    answer: "Navigation uses recorded destination coordinates. If a place has no stored latitude and longitude, the map pin is Not recorded."
  }
]

const HOME_KEYS = ["hero", "features", "featured", "case-studies", "highlights", "symbols", "culture", "provinces", "marquee", "testimonials", "faq", "cta"]

export default function Landing() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const publicConfig = usePublicConfig()
  const { showBlock, copy, extras } = publicConfig.pageCMS("home", HOME_KEYS)
  const notices = publicConfig.notices || []
  const destCount = publicConfig.catalog?.destination_count
  const destCountLabel = destCount != null ? destCount.toLocaleString() : null
  const [destinations, setDestinations] = useState([])
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const cmsHero = { title: copy("hero", "title"), subtitle: copy("hero", "subtitle", copy("hero", "body")) }

  // Search-as-you-type suggestions + did-you-mean autocorrect from the API
  const fetchSuggestions = useCallback(async (q, signal) => {
    try {
      const res = await destinationApi.autocomplete(q, { type: "attraction" })
      return res.data
    } catch {
      return []
    }
  }, [])

  useEffect(() => {
    destinationApi
      .getAll({ limit: 8, featured: true })
      .then(({ data }) => {
        setDestinations(data.results || data || [])
      })
      .catch(() => setDestinations([]))
      .finally(() => setLoading(false))
    userApi.getMarketplaceListings({ featured: true })
      .then(({ data }) => setPackages(data.results || []))
      .catch(() => setPackages([]))
  }, [])

  return (
    <div className="relative overflow-x-hidden bg-white text-gray-900">
      {showBlock("hero") && <section className="relative bg-gradient-to-br from-[#0f1f1a] via-[#163026] to-[#1f4a38] text-white overflow-hidden py-24 sm:py-32">
        <HeroEffects />
        <InteractiveHeroCanvas />

        {/* Ambient glow blobs */}
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-amber-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 -right-20 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="container-app relative z-10 max-w-5xl mx-auto text-center space-y-7">
          <FadeIn delay={0.1}>
            <BurnGlowBadge
              icon={FiSun}
              text="Explore Nepal's 7 Provinces · Live 2026 Himalayan Sentinel"
            />
          </FadeIn>

          <FadeIn delay={0.2}>
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.1] max-w-4xl mx-auto">
              {cmsHero?.title || <>{t("home.hero_title1")}{" "}<span className="bg-gradient-to-r from-amber-300 via-rose-300 to-amber-200 bg-clip-text text-transparent">{t("home.hero_title2")}</span></>}
            </h1>
          </FadeIn>

          <FadeIn delay={0.3}>
            <p className="text-base sm:text-xl text-stone-100/90 max-w-2xl mx-auto font-normal leading-relaxed">
              {cmsHero?.subtitle || cmsHero?.body || t("home.hero_subtitle") }
            </p>
          </FadeIn>

          {/* Above-the-fold Search Input with Quick Pills */}
          <FadeIn delay={0.4} className="max-w-2xl mx-auto space-y-3">
            <div className="bg-white/95 backdrop-blur-md p-2 rounded-2xl shadow-2xl border border-white/20">
              <SearchBar
                placeholder={t("nav.search")}
                className="w-full text-gray-900"
                onSearch={(val) => navigate(`/destinations?q=${encodeURIComponent(val)}`)}
                fetchSuggestions={fetchSuggestions}
              />
            </div>

            {/* Quick search pills */}
            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
              <span className="text-[11px] font-bold text-amber-200">{t("home.popular")}</span>
              {destinations.slice(0, 8).map((dest) => (
                <button
                  key={dest.slug || dest.id}
                  onClick={() => navigate(dest.slug ? `/destinations/${dest.slug}` : `/destinations?q=${encodeURIComponent(dest.name)}`)}
                  className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-white/10 hover:bg-white/25 text-white backdrop-blur transition-all border border-white/10"
                >
                  {dest.name}
                </button>
              ))}
              {!destinations.length && !loading && (
                <span className="text-[11px] text-amber-100/80">No recorded featured destinations yet.</span>
              )}
            </div>
          </FadeIn>

          {/* Primary & Secondary Above-The-Fold CTAs */}
          <FadeIn delay={0.5} className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              to="/destinations"
              className="px-8 py-3.5 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 text-gray-950 font-black text-sm hover:scale-105 shadow-xl shadow-amber-400/25 transition-all flex items-center gap-2"
            >
              <FiCompass size={18} /> {t("home.hero_cta")} <FiArrowRight size={16} />
            </Link>

            <Link
              to="/budget-estimator"
              className="px-7 py-3.5 rounded-2xl bg-primary-600 hover:bg-primary-700 text-white font-bold text-sm border border-amber-400/40 backdrop-blur shadow-lg transition-all"
            >
              {t("home.hero_budget")}
            </Link>
          </FadeIn>

          {/* Trust & Proof Indicators */}
          <FadeIn delay={0.6} className="pt-8 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-4 text-left">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center font-bold text-xs shrink-0">
                ✓
              </div>
              <span className="text-xs text-amber-200 font-medium">{destCountLabel ? `${destCountLabel} recorded places` : "Recorded places"}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center font-bold text-xs shrink-0">
                ★
              </div>
              <span className="text-xs text-amber-200 font-medium">Visitor totals not recorded</span>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-rose-500/20 text-rose-300 flex items-center justify-center font-bold text-xs shrink-0">
                🚨
              </div>
              <span className="text-xs text-amber-200 font-medium">24/7 Helpline (1144)</span>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                🏔️
              </div>
              <span className="text-xs text-amber-200 font-medium">All 7 Provinces</span>
            </div>
          </FadeIn>
        </div>
      </section>}

      {showBlock("features") && <section className="container-app py-20 relative z-10">
        <SlideUp>
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
              Engineered for Himalayan Explorers
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
              {copy("features", "title", "Why Travel with Nepal Portal")}
            </h2>
            <p className="text-gray-500 text-sm mt-2">
              {copy("features", "body", "Everything you need for an unforgettable, safe, and cost-effective expedition.")}
            </p>
          </div>
        </SlideUp>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }, idx) => (
            <HoverCard
              key={title}
              className="card-base p-7 rounded-3xl border border-emerald-100/80 shadow-xl bg-gradient-to-br from-white to-emerald-50/20 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold shadow-sm">
                  <Icon size={24} />
                </div>
                <h3 className="font-bold text-base text-gray-900 leading-snug">{title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <span className="text-[11px] font-bold text-emerald-700 flex items-center gap-1">
                  Learn more <FiArrowRight size={12} />
                </span>
              </div>
            </HoverCard>
          ))}
        </div>
      </section>}

      {notices.length > 0 && <section className="container-app pt-10"><VisitorNoticeBanner notices={notices} /></section>}

      {packages.length > 0 && <section className="container-app py-12">
        <div className="flex items-end justify-between gap-4 mb-6">
          <div>
            <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">Live catalogue</span>
            <h2 className="text-3xl font-extrabold text-gray-900 mt-2 tracking-tight">Featured packages</h2>
          </div>
          <Link to="/packages" className="text-xs font-bold text-emerald-700 hover:text-emerald-900 flex items-center gap-1">All packages <FiArrowRight size={14} /></Link>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {packages.slice(0, 3).map((offer) => (
            <Link key={offer.id} to={`/packages/${offer.slug}`} className="card-base p-5 hover:shadow-lg transition">
              <p className="text-[10px] font-black uppercase text-amber-800">{offer.kind} · {offer.duration_days} days</p>
              <h3 className="font-black text-slate-900 mt-1">{offer.title}</h3>
              <p className="text-sm text-slate-600 mt-1 line-clamp-2">{offer.summary}</p>
              <p className="mt-3 font-black">NPR {Number(offer.price_npr).toLocaleString()}</p>
            </Link>
          ))}
        </div>
      </section>}

      {showBlock("featured") && <section className="container-app py-16">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
          <div>
            <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
              Handpicked Wonders
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
              {copy("featured", "title", "Featured Nepal Destinations")}
            </h2>
          </div>
          <Link
            to="/destinations"
            className="text-xs font-bold text-emerald-700 hover:text-emerald-900 flex items-center gap-1 shrink-0"
          >
            {destCountLabel ? `View all ${destCountLabel} destinations` : "View all destinations"} <FiArrowRight size={14} />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <DestinationCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard key={d.id} destination={d} />
            ))}
          </div>
        )}
      </section>}

      {showBlock("case-studies") && <CaseStudiesSection />}
      {showBlock("highlights") && <NepalHighlights />}
      {(showBlock("symbols") || showBlock("culture")) && <section className="container-app py-10">
        {showBlock("symbols") && <NationalSymbols />}
        {showBlock("culture") && <NepalExperienceSection />}
      </section>}

      {showBlock("provinces") && <section className="container-app py-16">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Explore Destinations by Province
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Discover regional attractions from the eastern tea hills to the western wilderness.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {PROVINCES.map((prov) => (
            <Link
              key={prov.name}
              to={`/destinations?q=${encodeURIComponent(prov.city)}`}
              className="card-base p-4 text-center rounded-2xl border border-emerald-100 hover:border-emerald-300 hover:shadow-xl transition-all flex flex-col items-center justify-between"
            >
              <span className="font-bold text-xs text-gray-900">{prov.name}</span>
              <span className="text-[10px] text-emerald-700 mt-1 font-semibold">{prov.city}</span>
            </Link>
          ))}
        </div>
      </section>}

      {showBlock("marquee") && <ProvinceMarquee />}
      {showBlock("testimonials") && <TestimonialsSection />}

      {showBlock("faq") && <section className="container-app py-16">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            {copy("faq", "title", "Frequently Asked Questions")}
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            {copy("faq", "body", "Everything travelers ask before embarking on their journey in Nepal.")}
          </p>
        </div>
        <div className="max-w-3xl mx-auto">
          <FAQAccordion items={FAQ_ITEMS} />
        </div>
      </section>}

      {showBlock("cta") && <StickyCTA />}
      {extras?.length > 0 && <section className="container-app py-12"><CMSExtras sections={extras} /></section>}
    </div>
  )
}
