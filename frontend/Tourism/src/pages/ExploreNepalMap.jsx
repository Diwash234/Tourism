import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FiChevronRight, FiMapPin } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import destinationApi from "../api/destinationApi"
import DestinationCard from "../components/cards/DestinationCard"
import SkeletonLoader from "../components/common/SkeletonLoader"
import EmptyState from "../components/common/EmptyState"

const PROVINCES = [
  { name: "Koshi", city: "Biratnagar", description: "Eastern tea hills, wetlands and sunrise viewpoints." },
  { name: "Madhesh", city: "Janakpur", description: "Temple towns, Mithila culture and the southern plain." },
  { name: "Bagmati", city: "Kathmandu", description: "Heritage squares, craft traditions and the valley." },
  { name: "Gandaki", city: "Pokhara", description: "Lakes, Annapurna foothills and mountain paths." },
  { name: "Lumbini", city: "Butwal", description: "Sacred gardens, monasteries and the Terai." },
  { name: "Karnali", city: "Surkhet", description: "Remote valleys, national parks and western horizons." },
  { name: "Sudurpashchim", city: "Dhangadhi", description: "Far-western landscapes, rivers and community places." },
]

const ExploreNepalMap = () => {
  const [selected, setSelected] = useState(null)
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!selected) return undefined
    let active = true
    const timer = setTimeout(() => {
      setLoading(true)
      setError("")
      destinationApi.getAll({ province: selected.name, limit: 12 })
        .then(({ data }) => { if (active) setDestinations(data.results || data || []) })
        .catch(() => { if (active) { setDestinations([]); setError("We could not load this province's destination records right now.") } })
        .finally(() => { if (active) setLoading(false) })
    }, 0)
    return () => { active = false; clearTimeout(timer) }
  }, [selected])

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="explore-map" />
      <PageHeader title="Explore Nepal by province" subtitle="Choose a province to see recorded places, then open a destination for its own travel details." icon={FiMapPin} />
      <p className="text-sm text-[var(--ny-text-secondary)]">This is a province guide, not a precise boundary map. Destination records remain the source of truth.</p>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label="Nepal provinces">
        {PROVINCES.map((province) => {
          const active = selected?.name === province.name
          return <button key={province.name} type="button" onClick={() => setSelected(province)} className={`ny-card group flex min-h-36 flex-col items-start p-4 text-left ${active ? "border-[var(--ny-green)] bg-[var(--ny-soft-green)]" : ""}`} aria-pressed={active}><span className="grid h-10 w-10 place-items-center rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] text-[var(--ny-green)]"><FiMapPin size={18} aria-hidden="true" /></span><span className="mt-3 font-bold">{province.name}</span><span className="mt-1 text-xs text-[var(--ny-text-secondary)]">{province.description}</span><span className="mt-auto pt-3 text-xs font-semibold text-[var(--ny-green)]">Explore {province.city} <FiChevronRight size={13} className="inline transition group-hover:translate-x-0.5" aria-hidden="true" /></span></button>
        })}
      </section>

      {selected && <section aria-live="polite" className="space-y-5"><div className="flex items-center gap-2 border-b border-[var(--ny-border)] pb-4 text-sm text-[var(--ny-text-secondary)]"><span className="font-semibold text-[var(--ny-text)]">{selected.name}</span><FiChevronRight size={14} aria-hidden="true" /><span>Destinations across {selected.name}</span></div>{loading ? <SkeletonLoader count={3} /> : error ? <div role="alert" className="ny-panel p-5 text-sm text-[var(--ny-danger)]">{error} <button type="button" onClick={() => setSelected({ ...selected })} className="ml-2 font-semibold underline">Retry</button></div> : destinations.length ? <motion.div layout className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">{destinations.map((destination) => <DestinationCard key={destination.id} destination={destination} />)}</motion.div> : <EmptyState title={`No destinations found for ${selected.name}`} subtitle="There are no published records for this province view yet. Try another province or browse the full catalogue." action={<button type="button" onClick={() => setSelected(null)} className="ny-btn ny-btn-secondary">Choose another province</button>} />}</section>}
    </div>
  )
}

export default ExploreNepalMap
