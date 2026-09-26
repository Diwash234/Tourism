import { Link } from "react-router-dom"
import { FiActivity, FiAlertTriangle, FiCheckSquare, FiExternalLink, FiFileText, FiInfo } from "react-icons/fi"

// Trip readiness for a generated itinerary: why the plan looks the way it
// does, the altitude profile (sourced DEM elevations only), NTB-based
// acclimatization warnings, official permits/fees and a checklist.

const SEVERITY = {
  high: "border-red-200 bg-red-50 text-red-900",
  medium: "border-amber-200 bg-amber-50 text-amber-900",
  info: "border-sky-200 bg-sky-50 text-sky-900",
}

const npr = (v) => (v == null ? "—" : `NPR ${Math.round(Number(v)).toLocaleString()}`)

function AltitudeProfile({ profile }) {
  const rows = profile?.days || []
  const known = rows.filter((r) => r.max_elevation_m != null)
  if (!known.length) {
    return <p className="text-xs text-[var(--ny-text-muted)]">No sourced elevation is recorded for the stops in this plan.</p>
  }
  const top = Math.max(...known.map((r) => r.max_elevation_m), 2500)
  return (
    <div>
      <ul className="space-y-1.5" aria-label="Highest stop per day">
        {rows.map((r) => (
          <li key={r.day} className="grid grid-cols-[3.5rem_minmax(0,1fr)_5.5rem] items-center gap-2 text-xs">
            <span className="font-semibold">Day {r.day}</span>
            <span className="relative h-2.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
              {r.max_elevation_m != null && (
                <span className={`absolute inset-y-0 left-0 rounded-full ${r.max_elevation_m >= 2500 ? "bg-amber-500" : "bg-emerald-500"}`}
                  style={{ width: `${Math.max(4, (r.max_elevation_m / top) * 100)}%` }} />
              )}
            </span>
            <span className="text-right tabular-nums">{r.max_elevation_m != null ? `≈${r.max_elevation_m.toLocaleString()} m` : "not recorded"}</span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] leading-4 text-[var(--ny-text-muted)]">
        {profile.note}{profile.stops_without_elevation ? ` ${profile.stops_without_elevation} stop(s) have no recorded elevation.` : ""}
      </p>
    </div>
  )
}

export default function TripReadinessPanel({ plan }) {
  const why = plan?.why_this_itinerary || []
  const warnings = plan?.acclimatization?.warnings || []
  const permits = plan?.permits_and_fees
  const checklist = plan?.trip_readiness || []
  if (!why.length && !checklist.length && !plan?.altitude_profile) return null
  const lines = permits?.fee_totals?.lines || []

  return (
    <section aria-labelledby="readiness-h" className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2" data-testid="trip-readiness">
      <h2 id="readiness-h" className="sr-only">Trip readiness</h2>

      {why.length > 0 && (
        <div className="card-base p-5 lg:col-span-2">
          <h3 className="flex items-center gap-2 text-sm font-bold"><FiInfo aria-hidden="true" /> Why this itinerary</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--ny-text-secondary)]">{why.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      )}

      {plan?.altitude_profile && (
        <div className="card-base p-5">
          <h3 className="flex items-center gap-2 text-sm font-bold"><FiActivity aria-hidden="true" /> Altitude & acclimatization</h3>
          <div className="mt-3"><AltitudeProfile profile={plan.altitude_profile} /></div>
          {warnings.length > 0 && (
            <ul className="mt-3 space-y-2" data-testid="altitude-warnings">
              {warnings.map((w) => (
                <li key={`${w.day}-${w.type}`} className={`flex gap-2 rounded-lg border p-2 text-xs leading-5 ${SEVERITY[w.severity] || SEVERITY.info}`}>
                  <FiAlertTriangle className="mt-0.5 shrink-0" aria-hidden="true" /><span>{w.message}</span>
                </li>
              ))}
            </ul>
          )}
          {plan.acclimatization?.source?.url && (
            <a className="mt-2 inline-flex items-center gap-1 text-[11px] underline" href={plan.acclimatization.source.url} target="_blank" rel="noreferrer">
              NTB — Safety in the mountains <FiExternalLink size={10} />
            </a>
          )}
        </div>
      )}

      {permits && (
        <div className="card-base p-5">
          <h3 className="flex items-center gap-2 text-sm font-bold"><FiFileText aria-hidden="true" /> Permits & official fees</h3>
          {lines.length ? (
            <ul className="mt-2 divide-y divide-slate-100 text-sm">
              {lines.map((l) => (
                <li key={l.label} className="flex items-start justify-between gap-3 py-1.5">
                  <span className="min-w-0">{l.label}{l.basis ? <span className="block text-[11px] text-[var(--ny-text-muted)]">{l.basis}</span> : null}</span>
                  <span className="shrink-0 text-right font-semibold">{l.amount_npr_per_person != null ? npr(l.amount_npr_per_person) : <span className="text-xs font-normal">not quoted</span>}
                    {l.currency === "USD" && l.amount_per_person != null ? <span className="block text-[11px] font-normal">US${l.amount_per_person}</span> : null}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">No park, permit or TIMS requirement matched the catalogue places in this plan.</p>
          )}
          {lines.length > 0 && (
            <p className="mt-2 flex justify-between border-t border-slate-200 pt-2 text-sm font-bold"><span>Per person</span><span>{npr(permits.fee_totals.per_person_npr)}</span></p>
          )}
          <p className="mt-2 text-[11px] text-[var(--ny-text-muted)]">{permits.matching_note} Visa fees are listed in the checklist.</p>
        </div>
      )}

      {checklist.length > 0 && (
        <div className="card-base p-5 lg:col-span-2">
          <h3 className="flex items-center gap-2 text-sm font-bold"><FiCheckSquare aria-hidden="true" /> Trip readiness checklist</h3>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {checklist.map((item) => (
              <li key={item.key} className="flex gap-2 rounded-lg border border-slate-200 p-2 text-sm">
                <input type="checkbox" className="mt-1" aria-label={item.label} />
                <span className="min-w-0">
                  <span className="font-semibold">{item.label}</span>{item.required ? <span className="ml-1 text-[10px] uppercase text-red-700">required</span> : null}
                  <span className="block text-xs text-[var(--ny-text-secondary)]">{item.detail}</span>
                  {item.link ? <Link className="text-xs underline" to={item.link}>Open</Link> : null}
                  {item.source?.url ? <a className="inline-flex items-center gap-1 text-[11px] underline" href={item.source.url} target="_blank" rel="noreferrer">{item.source.publisher} <FiExternalLink size={10} /></a> : null}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs"><Link className="underline" to="/before-you-travel">Full visa, TIMS, permit & insurance guide →</Link></p>
        </div>
      )}
    </section>
  )
}
