import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiArrowRight, FiCompass, FiMapPin, FiShield } from "react-icons/fi"
import { useI18n } from "../i18n"
import usePublicConfig from "../hooks/usePublicConfig"
import destinationApi from "../api/destinationApi"
import adminApi from "../api/adminApi"
import userApi from "../api/userApi"
import FAQAccordion from "../components/common/FAQAccordion"
import NepalHighlights from "../components/dashboard/NepalHighlights"
import NepalExperienceSection from "../components/dashboard/NepalExperienceSection"
import NationalSymbols from "../components/dashboard/NationalSymbols"
import VisitorNoticeBanner from "../components/common/VisitorNoticeBanner"
import { CMSExtras } from "../components/cms/CMSBlock"
import CaseStudiesSection from "../components/landing/CaseStudiesSection"
import TestimonialsSection from "../components/landing/TestimonialsSection"
import NearYouSection from "../components/landing/NearYouSection"
import StickyCTA from "../components/common/StickyCTA"
import ProvinceMarquee from "../components/landing/ProvinceMarquee"
import NepalStats from "../components/landing/NepalStats"
import FeaturedEditorialGrid from "../components/landing/FeaturedEditorialGrid"
import HeroCinematic from "../components/landing/HeroCinematic"

const PROVINCES = [
  ["Koshi", "Biratnagar"], ["Madhesh", "Janakpur"], ["Bagmati", "Kathmandu"], ["Gandaki", "Pokhara"],
  ["Lumbini", "Butwal"], ["Karnali", "Surkhet"], ["Sudurpashchim", "Dhangadhi"],
]

const DEFAULT_FEATURES = [
  { icon: FiCompass, title: "Explore with context", description: "Compare recorded destinations, locations, seasons and practical details.", url: "/destinations" },
  { icon: FiMapPin, title: "Shape your route", description: "Move from a place to a plan with trip planning, distance and navigation tools.", url: "/itinerary" },
  { icon: FiShield, title: "Keep safety close", description: "Find emergency services, directory records and current alert information when available.", url: "/emergency" },
  { icon: FiArrowRight, title: "Build at your pace", description: "Save useful places, assemble an itinerary and request partner services when ready.", url: "/packages" },
]

const FAQ_ITEMS = [
  { question: "Can I plan a Nepal trip in one place?", answer: "Nepal Yatra brings destinations, route planning, budget tools, travel packages and safety information into one journey. Availability depends on the live project catalogue; missing information is marked rather than filled in." },
  { question: "Are prices and ratings real?", answer: "Prices, ratings and availability are shown only when a record is available. When a field is not recorded, the interface says so instead of guessing." },
  { question: "What should I do in an emergency?", answer: "Open Emergency services, search an approved destination or choose GPS. The directory presents the contact records returned by the current emergency response." },
  { question: "How do I add a place I discovered?", answer: "Signed-in travellers can use the submission forms. A place is published only after the platform's review process, so the public catalogue stays trustworthy." },
]

const HOME_KEYS = ["hero", "features", "featured", "case-studies", "highlights", "symbols", "culture", "provinces", "marquee", "testimonials", "faq", "cta"]

export default function Landing() {
  const { t } = useI18n()
  const publicConfig = usePublicConfig()
  const { showBlock, block: cmsBlock, copy, extras } = publicConfig.pageCMS("home", HOME_KEYS)
  const [destinations, setDestinations] = useState([])
  const [featuredCards, setFeaturedCards] = useState([])
  const [packages, setPackages] = useState([])
  const featureItems = (() => {
    const blocks = cmsBlock("features")?.blocks || []
    const grid = blocks.find((item) => (item.block_type || item.type) === "card_grid")
    const items = grid?.data?.items
    return Array.isArray(items) && items.length ? items : null
  })()

  useEffect(() => {
    let active = true
    Promise.allSettled([
      adminApi.getPublicFeaturedDestinations(),
      destinationApi.getAll({ limit: 8, featured: true }),
      userApi.getMarketplaceListings({ featured: true }),
    ]).then(([featured, places, offers]) => {
      if (!active) return
      setFeaturedCards(featured.status === "fulfilled" ? (featured.value.data.results || featured.value.data || []) : [])
      setDestinations(places.status === "fulfilled" ? (places.value.data.results || places.value.data || []) : [])
      setPackages(offers.status === "fulfilled" ? (offers.value.data.results || []) : [])
    })
    return () => { active = false }
  }, [])

  return (
    <div className="ny-page overflow-x-hidden bg-[var(--ny-bg)]">
      {showBlock("hero") && <HeroCinematic />}
      <NearYouSection destinations={destinations} />
      {publicConfig.notices?.length > 0 && <section className="container-app pt-8"><VisitorNoticeBanner notices={publicConfig.notices} /></section>}

      {showBlock("features") && <section className="container-app section-space"><div className="max-w-2xl"><p className="ny-kicker">A calmer way to travel</p><h2 className="mt-2">{copy("features", "title", "From first idea to a safer route")}</h2><p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{copy("features", "body", "Explore the country, compare the details that matter and keep the next useful action close at hand.")}</p></div><div className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">{(featureItems || DEFAULT_FEATURES).map((item) => { const Icon = typeof item.icon === "function" ? item.icon : null; const title = item.title || "Explore Nepal"; const description = item.description || item.body || "Explore the live catalogue."; const url = item.url || "/destinations"; const content = <><span className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] text-[var(--ny-green)]">{Icon ? <Icon size={20} aria-hidden="true" /> : <span aria-hidden="true">{item.emoji || "✦"}</span>}</span><h3 className="mt-5 text-lg font-bold">{title}</h3><p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{description}</p><span className="mt-auto pt-5 text-sm font-semibold text-[var(--ny-green)]">Explore <FiArrowRight size={14} className="inline" aria-hidden="true" /></span></>; return <Link key={title} to={url} className="ny-card flex h-full flex-col p-5 hover:-translate-y-0.5">{content}</Link> })}</div></section>}

      {packages.length > 0 && <section className="container-app pb-12"><div className="flex flex-col gap-3 border-b border-[var(--ny-border)] pb-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="ny-kicker">Live catalogue</p><h2 className="mt-2">Travel packages</h2></div><Link to="/packages" className="text-sm font-semibold text-[var(--ny-green)] hover:underline">View all packages <FiArrowRight size={14} className="inline" aria-hidden="true" /></Link></div><div className="mt-6 grid gap-5 md:grid-cols-3">{packages.slice(0, 3).map((offer) => <Link key={offer.id} to={`/packages/${offer.slug}`} className="ny-card flex h-full flex-col p-5"><span className="text-xs font-semibold uppercase tracking-[0.08em] text-[var(--ny-green)]">{offer.kind}</span><h3 className="mt-2 text-lg font-bold">{offer.title}</h3><p className="mt-2 line-clamp-2 text-sm text-[var(--ny-text-secondary)]">{offer.summary || offer.description || "Package information available on the detail page."}</p><span className="mt-auto pt-5 text-sm font-bold text-[var(--ny-green)]">{offer.price_npr != null ? `NPR ${Number(offer.price_npr).toLocaleString()}` : "Price unavailable"}</span></Link>)}</div></section>}

      <NepalStats destinationCount={publicConfig.catalog?.destination_count} />
      {showBlock("featured") && <FeaturedEditorialGrid destinations={destinations} featuredCards={featuredCards} />}
      {showBlock("case-studies") && <CaseStudiesSection offers={packages} destinations={destinations} />}
      {showBlock("highlights") && <NepalHighlights />}
      {(showBlock("symbols") || showBlock("culture")) && <section className="container-app section-space">{showBlock("symbols") && <NationalSymbols />}{showBlock("culture") && <NepalExperienceSection />}</section>}

      {showBlock("provinces") && <section className="container-app section-space"><div className="max-w-2xl"><p className="ny-kicker">Across the country</p><h2 className="mt-2">Explore by province</h2><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">Start with a province, then follow the places that fit your route.</p></div><div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-7">{PROVINCES.map(([province, city]) => <Link key={province} to={`/destinations?q=${encodeURIComponent(city)}`} className="ny-card flex min-h-28 flex-col justify-between p-4"><span className="font-bold">{province}</span><span className="mt-3 text-xs text-[var(--ny-text-secondary)]">{city}</span><span className="mt-3 text-xs font-semibold text-[var(--ny-green)]">Explore →</span></Link>)}</div></section>}
      {showBlock("marquee") && <ProvinceMarquee />}
      {showBlock("testimonials") && <TestimonialsSection />}
      {showBlock("faq") && <section className="container-app section-space"><div className="max-w-2xl"><p className="ny-kicker">Before you go</p><h2 className="mt-2">{copy("faq", "title", "Frequently asked questions")}</h2>{copy("faq", "body", "Everything travellers ask before beginning a journey in Nepal.") && <p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{copy("faq", "body", "Everything travellers ask before beginning a journey in Nepal.")}</p>}</div><div className="mx-auto mt-7 max-w-3xl"><FAQAccordion items={FAQ_ITEMS} /></div></section>}
      {showBlock("cta") && <StickyCTA />}
      {extras?.length > 0 && <section className="container-app section-space"><CMSExtras sections={extras} /></section>}
      <p className="sr-only">Nepal Yatra traveller information portal language: {t("language.name") || "English"}</p>
    </div>
  )
}
