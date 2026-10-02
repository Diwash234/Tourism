import { FiExternalLink, FiClock } from "react-icons/fi"

// Small, reusable pieces that show a derived fact together with its basis.
// Rule: never render a value the API did not return. Unknowns say "unknown".

const SEASON_STYLES = {
  best: "bg-emerald-100 text-emerald-900 border-emerald-300",
  good: "bg-emerald-50 text-emerald-800 border-emerald-200",
  fair: "bg-slate-50 text-slate-700 border-slate-200",
  caution: "bg-amber-50 text-amber-900 border-amber-300",
  poor: "bg-rose-50 text-rose-800 border-rose-200",
}

export const SourceLink = ({ source, className = "" }) => (source?.url ? (
  <a href={source.url} target="_blank" rel="noreferrer"
    className={`inline-flex items-center gap-1 text-xs text-[var(--ny-text-muted)] underline ${className}`}>
    Source: {source.publisher || source.title}{source.retrieved_at ? ` (retrieved ${source.retrieved_at})` : ""}
    <FiExternalLink size={11} aria-hidden="true" />
  </a>
) : null)

export const SeasonBadge = ({ season, withReason = false }) => {
  if (!season) return null
  return (
    <span className="inline-flex flex-col gap-1">
      <span title={season.reason}
        className={`inline-flex w-fit items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${SEASON_STYLES[season.level] || SEASON_STYLES.fair}`}>
        {season.label} in {season.month_name}
      </span>
      {withReason && <span className="text-xs text-[var(--ny-text-secondary)]">{season.reason}</span>}
      {withReason && (season.notes || []).map((n) => <span key={n} className="text-xs text-amber-800">{n}</span>)}
    </span>
  )
}

export const OpenNowBadge = ({ hours, compact = false }) => {
  if (!hours) return null
  const style = hours.state === "open"
    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
    : hours.state === "closed" ? "bg-slate-100 text-slate-700 border-slate-200" : "bg-white text-slate-500 border-slate-200"
  return (
    <span title={[hours.raw, hours.note].filter(Boolean).join(" · ")}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold ${style}`}>
      <FiClock size={11} aria-hidden="true" />
      {compact && hours.state === "unknown" ? "Hours unknown" : hours.label}
    </span>
  )
}

const km = (v) => `${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })} km`

/** Compact fact chips for a destination result (from facts_for_row). */
export const FactChips = ({ facts }) => {
  if (!facts) return null
  const chips = []
  const elev = facts.elevation?.meters
  chips.push({ key: "elev", text: elev != null ? `${elev.toLocaleString()} m` : "Elevation unknown",
    title: elev != null ? `Source: ${facts.elevation.source}` : "No measured elevation on record" })
  chips.push({ key: "diff", text: facts.difficulty?.level === "unknown" ? "Effort unknown" : `${facts.difficulty?.label} effort`,
    title: facts.difficulty?.basis })
  chips.push({ key: "cost", text: facts.cost?.label, title: facts.cost?.basis })
  if (facts.distance_from_origin_km != null) {
    chips.push({ key: "dist", text: `${km(facts.distance_from_origin_km)} straight line`, title: facts.reach?.basis })
  }
  if (facts.nearest_hospital) {
    chips.push({ key: "hosp", text: `Hospital ${facts.nearest_hospital.km} km`,
      title: `${facts.nearest_hospital.name}${facts.nearest_hospital.verified ? "" : " (unverified listing)"}, straight line` })
  }
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Key facts">
      {chips.filter((c) => c.text).map((c) => (
        <li key={c.key} title={c.title}
          className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-700">
          {c.text}
        </li>
      ))}
    </ul>
  )
}

export const monthNow = () => new Date().getMonth() + 1
