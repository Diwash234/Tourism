import { useEffect, useState } from "react"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiAward,
  FiCoffee,
  FiFeather,
  FiHome,
  FiMap,
  FiSun,
  FiBookOpen,
  FiX,
  FiCompass,
} from "react-icons/fi"

import PlaceholderImage from "../components/common/PlaceholderImage"
import NationalSymbols, { ALL_26_NATIONAL_SYMBOLS, EIGHT_THOUSANDERS, HIMALAYAN_RANGES } from "../components/dashboard/NationalSymbols"
import destinationApi from "../api/destinationApi"
import { NOT_RECORDED, recordedCity, recordedText } from "../utils/placeUtils"
import EmptyState from "../components/common/EmptyState"
import SkeletonLoader from "../components/common/SkeletonLoader"

const Section = ({ id, icon: Icon, title, children }) => (
  <motion.section
    id={id}
    initial={{ opacity: 0, y: 12 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    className="scroll-mt-24 py-10 border-b border-gray-100 last:border-0"
  >
    <h2 className="section-title flex items-center gap-2">
      <Icon className="text-himalaya-500" />
      {title}
    </h2>
    {children}
  </motion.section>
)

const DestChip = ({ dest }) => (
  <Link
    to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"}
    className="text-xs font-medium bg-gray-50 text-gray-700 px-3.5 py-2 rounded-full border border-gray-200 hover:border-emerald-500 hover:bg-emerald-50 transition"
  >
    {dest.name}
    {dest.altitude ? ` · ${dest.altitude}` : ""}
  </Link>
)

const DestCard = ({ dest }) => (
  <Link to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"} className="card-base p-4 hover:shadow-md transition bg-white border border-slate-200">
    <PlaceholderImage src={dest.cover_image_url} title={dest.name} alt={dest.name} className="mb-3 h-32 w-full rounded-xl" />
    <h3 className="font-bold text-sm text-slate-900 mb-1">{dest.name}</h3>
    <p className="text-xs text-gray-500">{recordedCity(dest) || dest.district || NOT_RECORDED}</p>
    <p className="text-xs text-gray-600 mt-1 line-clamp-2">{recordedText(dest.short_description || dest.description)}</p>
  </Link>
)

export default function DiscoverNepal() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [showSymbolsModal, setShowSymbolsModal] = useState(false)

  useEffect(() => {
    const resetTimer = setTimeout(() => setError(""), 0)
    destinationApi.discoverNepal()
      .then(({ data }) => setPayload(data))
      .catch((requestError) => {
        setPayload(null)
        setError(requestError.response?.data?.detail || "We could not load the discovery records right now.")
      })
      .finally(() => setLoading(false))
    return () => clearTimeout(resetTimer)
  }, [])

  const wildlife = payload?.wildlife?.items || []
  const heritage = payload?.heritage?.items || []
  const culture = payload?.culture?.items || []
  const cuisine = payload?.cuisine?.items || []
  const festivals = payload?.festivals?.items || []
  const provinces = payload?.provinces || []

  return (
    <div className="ny-page container-app space-y-8 py-6 sm:py-8">
      <CMSPageIntro pageKey="discover-nepal" />
      {loading && <SkeletonLoader count={4} />}
       {error && <div role="alert" className="ny-panel flex flex-col gap-3 border-[#E9B9B9] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)] sm:flex-row sm:items-center sm:justify-between"><span>{error}</span><button type="button" onClick={() => window.location.reload()} className="ny-btn ny-btn-secondary min-h-11 shrink-0">Try again</button></div>}
      <header className="flex flex-col gap-4 border-b border-[var(--ny-border)] pb-6 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0"><span className="ny-kicker">Himalayan atlas & national identity</span><PageHeader title="Discover Nepal beyond Everest" subtitle="Explore recorded places, mountain context, heritage and the practical details that help you choose a route." icon={FiCompass} /><p className="mt-2 max-w-2xl text-sm text-[var(--ny-text-secondary)]">Move between the mountain record, living culture, protected places and the destinations behind them.</p></div>
        <button type="button" onClick={() => setShowSymbolsModal(true)} className="ny-btn ny-btn-secondary shrink-0"><FiBookOpen size={16} aria-hidden="true" />Explore national symbols</button>
      </header>

      {/* Top Banner: National Symbols Summary */}
      <NationalSymbols />

      {/* 8,000m PEAKS TABLE & HIMALAYAN RANGES */}
      <section className="card-base p-6 sm:p-8 bg-white border border-slate-200 shadow-xl space-y-6">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-black uppercase tracking-wider">
            Highest Mountains on Earth
          </span>
          <h2 className="text-2xl font-black text-slate-900 mt-2 flex items-center gap-2">
            Nepal's eight mountains above 8,000 metres
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Nepal contains 8 of the world's 14 mountains higher than 8,000 meters.
          </p>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-white uppercase font-black tracking-wider text-[11px]">
              <tr>
                <th className="p-3">Rank</th>
                <th className="p-3">Mountain Peak</th>
                <th className="p-3">Height (m)</th>
                <th className="p-3">Himalayan Section</th>
                <th className="p-3">District / Region</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {EIGHT_THOUSANDERS.map((m) => (
                <tr key={m.rank} className="hover:bg-slate-50 font-medium">
                  <td className="p-3 font-black text-amber-600">#{m.rank}</td>
                  <td className="p-3 font-bold text-slate-900 text-sm">{m.name}</td>
                  <td className="p-3 font-black text-emerald-700 font-mono text-sm">{m.height}</td>
                  <td className="p-3 text-slate-600">{m.range}</td>
                  <td className="p-3 text-slate-600">{m.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Major Himalayan Sections Grid */}
        <div className="pt-4 border-t border-slate-100 space-y-3">
          <h3 className="font-extrabold text-base text-slate-900">Major Himalayan Sections of Nepal</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {HIMALAYAN_RANGES.map((r, i) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                <p className="font-black text-blue-900 text-sm">{r.range}</p>
                <p className="text-emerald-700 font-bold">Highest: {r.highest}</p>
                <p className="text-slate-600"><b>Peaks:</b> {r.peaks}</p>
                <p className="text-slate-500 text-[11px]">{r.area}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CULTURAL & LIVING HERITAGE SECTION */}
      <Section id="cultural-heritage" icon={FiFeather} title="Nepali cultural & living heritage">
        {culture.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{culture.map((item, index) => <article key={item.slug || index} className="ny-card overflow-hidden"><PlaceholderImage src={item.image || item.cover_image_url} title={item.title || item.name} alt={item.title || item.name} className="h-36 w-full" /><div className="p-4">{(item.nepali || item.nepali_title) && <span className="text-xs font-semibold text-[var(--ny-green)]">{item.nepali || item.nepali_title}</span>}<h3 className="mt-1 font-bold">{item.title || item.name}</h3><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{item.desc || item.short_description || "Cultural information unavailable."}</p></div></article>)}</div> : <EmptyState title="Cultural records unavailable" subtitle="The current discovery response did not include cultural stories." action={<Link to="/destinations?q=culture" className="ny-btn ny-btn-secondary">Browse cultural places</Link>} />}
      </Section>

      {/* FESTIVALS */}
      <Section id="festivals" icon={FiSun} title="Cultural festivals">
        {festivals.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{festivals.map((festival, index) => <article key={festival.id || index} className="ny-card p-5"><div className="flex items-start justify-between gap-3"><h3 className="font-bold">{festival.title || festival.name}</h3><span className="rounded-full bg-[var(--ny-soft-gold)] px-2.5 py-1 text-xs text-[var(--ny-warning)]">{festival.date || festival.kind || "Festival"}</span></div><p className="mt-3 text-sm leading-6 text-[var(--ny-text-secondary)]">{festival.body || festival.desc || "Festival information unavailable."}</p>{(festival.city || festival.district) && <p className="mt-4 border-t border-[var(--ny-border)] pt-3 text-xs text-[var(--ny-text-secondary)]">{festival.city || festival.district}</p>}</article>)}</div> : <EmptyState title="Festival records unavailable" subtitle="The current discovery response did not include festival records." />}
      </Section>

      {/* WILDLIFE & PARKS */}
      <Section id="wildlife" icon={FiAward} title="Wildlife Reserves & National Parks">
        {wildlife.length ? (
          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            {wildlife.map((dest) => <DestCard key={dest.id} dest={dest} icon={FiAward} />)}
          </div>
        ) : <EmptyState title="Wildlife records unavailable" subtitle="The current discovery response did not include wildlife places. Browse the destination catalogue for the latest records." action={<Link to="/destinations?q=wildlife" className="ny-btn ny-btn-secondary">Browse wildlife places</Link>} />}
      </Section>

      {/* HERITAGE SITES */}
      <Section id="unesco" icon={FiHome} title="UNESCO Heritage & Palaces">
        {heritage.length ? (
          <div className="flex flex-wrap gap-2 mt-2">
            {heritage.map((dest) => <DestChip key={dest.id} dest={dest} />)}
          </div>
        ) : <EmptyState title="Heritage records unavailable" subtitle="The current discovery response did not include heritage places." action={<Link to="/destinations?q=heritage" className="ny-btn ny-btn-secondary">Browse heritage places</Link>} />}
      </Section>

      {/* LOCAL FOOD */}
      <Section id="local-food" icon={FiCoffee} title="Authentic Nepali Culinary Heritage">
        {cuisine.length ? <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{cuisine.map((food, i) => <article key={food.slug || i} className="ny-card overflow-hidden"><PlaceholderImage src={food.image || food.cover_image_url} title={food.name || food.title} alt={food.name || food.title} className="h-36 w-full" /><div className="p-4">{food.nepali && <span className="text-xs font-semibold text-[var(--ny-green)]">{food.nepali}</span>}<h3 className="mt-1 font-bold">{food.name || food.title}</h3><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{food.desc || food.short_description || "Food information unavailable."}</p></div></article>)}</div> : <EmptyState title="Food records unavailable" subtitle="The current discovery response did not include food stories." action={<Link to="/destinations?q=food" className="ny-btn ny-btn-secondary">Browse food places</Link>} />}
      </Section>

      {/* PROVINCE INFORMATION */}
      <Section id="provinces" icon={FiMap} title="7 Provinces of Nepal">
        {provinces.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {provinces.map((province) => (
            <Link
              key={province.name}
              to={`/destinations?q=${encodeURIComponent(province.name)}`}
              className="card-base p-4 hover:shadow-md transition bg-white border border-slate-200"
            >
              <h3 className="font-extrabold text-base text-slate-900">{province.name}</h3>
              <p className="text-xs text-emerald-700 font-bold mt-1">
                {province.destination_count != null
                  ? `${province.destination_count.toLocaleString()} recorded places`
                  : "Browse province places"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {province.sample_name || NOT_RECORDED}
              </p>
            </Link>
          ))}
        </div> : <EmptyState title="Province records unavailable" subtitle="The current discovery response did not include province summaries." action={<Link to="/destinations" className="ny-btn ny-btn-secondary">Browse destinations</Link>} />}
      </Section>

      {/* ALL 26 NATIONAL SYMBOLS SHOWCASE MODAL */}
      <AnimatePresence>
        {showSymbolsModal && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b pb-4">
                <div>
                  <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase">
                    Official 26 National Symbols Showcase
                  </span>
                  <h3 className="text-2xl font-black text-slate-900 mt-2">Nepal National Symbols & Heritage Details</h3>
                </div>
                <button onClick={() => setShowSymbolsModal(false)} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700">
                  <FiX size={20} />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                {ALL_26_NATIONAL_SYMBOLS.map((s) => (
                  <div key={s.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1.5 flex flex-col justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        {s.image ? (
                          <img src={s.image} alt={s.title} className="w-12 h-12 rounded-full object-cover border-2 border-amber-500 shadow" />
                        ) : (
                          <span className="text-2xl">{s.icon}</span>
                        )}
                        <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">{s.nepali}</span>
                      </div>
                      <h4 className="font-extrabold text-sm text-slate-900">{s.title}</h4>
                      <p className="text-slate-600 leading-relaxed">{s.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-4 border-t">
                <button onClick={() => setShowSymbolsModal(false)} className="px-6 py-2.5 rounded-xl bg-slate-900 text-white font-bold text-xs">
                  Close Showcase
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
