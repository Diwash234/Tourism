import { FiMapPin, FiTrendingUp, FiCompass } from "react-icons/fi"

const BASE_STATS = [
  { value: "7", label: "Provinces", note: "Administrative regions of Nepal", icon: FiMapPin },
  { value: "77", label: "Districts", note: "Administrative districts across Nepal", icon: FiCompass },
]

export default function NepalStats({ destinationCount = null }) {
  const stats = destinationCount == null ? BASE_STATS : [...BASE_STATS, { value: Number(destinationCount).toLocaleString(), label: "Recorded places", note: "From the current project catalogue", icon: FiTrendingUp }]
  return (
    <section className="border-y border-[var(--ny-border)] bg-white py-12 sm:py-16" aria-labelledby="nepal-stats-title">
      <div className="container-app"><div className="max-w-2xl"><p className="ny-kicker">Nepal, in numbers</p><h2 id="nepal-stats-title" className="mt-2">A country of remarkable scale</h2><p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">A few useful facts for orienting your trip, with the destination count shown only when the live catalogue provides it.</p></div><div className={`mt-8 grid grid-cols-2 gap-4 ${stats.length === 4 ? "xl:grid-cols-4" : "lg:grid-cols-3"}`}>{stats.map(({ value, label, note, icon: Icon }) => <div key={label} className="ny-card p-5"><Icon size={20} className="text-[var(--ny-green)]" aria-hidden="true" /><strong className="mt-4 block text-3xl font-bold text-[var(--ny-text)]">{value}</strong><span className="mt-1 block text-sm font-semibold">{label}</span><p className="mt-2 text-xs leading-5 text-[var(--ny-text-secondary)]">{note}</p></div>)}</div></div>
    </section>
  )
}
