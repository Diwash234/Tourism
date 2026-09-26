import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiActivity, FiExternalLink, FiFileText, FiShield } from "react-icons/fi"
import travelApi from "../../api/travelApi"
import { NATIONALITY_OPTIONS } from "../../utils/currency"

// Destination-specific official requirements: elevation (sourced), park /
// conservation fee, restricted-area permit, TIMS + guide rule, heritage fee
// and insurance advice. Matches are labelled "likely" with their basis --
// the traveller is always pointed to the official source.

const Src = ({ source }) => source?.url ? (
  <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] underline text-slate-500">
    {source.publisher} <FiExternalLink size={10} />
  </a>
) : null

const Item = ({ title, status, basis, children, source }) => (
  <li className="rounded-xl border border-slate-200 bg-white p-3">
    <p className="text-sm font-semibold text-slate-900">{title}</p>
    {status ? <p className="text-[11px] font-medium text-amber-800">{status}</p> : null}
    <div className="mt-1 text-xs leading-5 text-slate-600">{children}</div>
    {basis ? <p className="mt-1 text-[11px] text-slate-500">Why: {basis}</p> : null}
    <Src source={source} />
  </li>
)

export default function DestinationRequirementsPanel({ destinationId }) {
  const [nationality, setNationality] = useState(() => localStorage.getItem("tourism_nationality") || "foreign")
  const [state, setState] = useState({ data: null, error: false })

  useEffect(() => {
    if (!destinationId) return undefined
    let alive = true
    travelApi.destinationRequirements(destinationId, { nationality })
      .then(({ data }) => { if (alive) setState({ data, error: false }) })
      .catch(() => { if (alive) setState({ data: null, error: true }) })
    return () => { alive = false }
  }, [destinationId, nationality])

  const { data, error } = state
  if (error) return null
  if (!data) return <div className="card-base h-24 animate-pulse rounded-3xl bg-slate-50" aria-hidden="true" />

  const alt = data.altitude
  const nothing = !data.protected_areas.length && !data.restricted_areas.length && !data.tims && !data.heritage_sites.length

  return (
    <section aria-labelledby="dest-req-h" className="card-base space-y-4 rounded-3xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/40 p-6" data-testid="destination-requirements">
      <div className="flex flex-col gap-2 border-b pb-3 sm:flex-row sm:items-end sm:justify-between">
        <h2 id="dest-req-h" className="flex items-center gap-2 text-lg font-bold text-slate-900"><FiFileText /> Permits, fees & altitude</h2>
        <label className="text-xs text-slate-600">
          <span className="sr-only">Nationality</span>
          <select className="input-field !min-h-9 !py-1 text-xs" value={nationality} onChange={(e) => { setNationality(e.target.value); localStorage.setItem("tourism_nationality", e.target.value) }}>
            {NATIONALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label.split(" (")[0]}</option>)}
          </select>
        </label>
      </div>

      <p className="flex items-start gap-2 text-sm text-slate-700">
        <FiActivity className="mt-1 shrink-0" aria-hidden="true" />
        {alt.recorded ? (
          <span>
            Elevation ≈ <strong>{alt.elevation_m.toLocaleString()} m</strong>
            <span className="block text-[11px] text-slate-500">{alt.elevation_kind === "dem" ? "Approx. terrain height (Copernicus DEM via Open-Meteo)" : alt.elevation_source}</span>
            {alt.above_threshold ? <span className="mt-1 block text-xs font-medium text-amber-800">Above 2,500 m — ascend gradually; know the AMS symptoms. <Link className="underline" to="/before-you-travel#altitude">Altitude guide</Link></span> : null}
          </span>
        ) : <span>Elevation not recorded for this place.</span>}
      </p>

      {nothing ? (
        <p className="text-sm text-slate-600">No national-park, restricted-area, TIMS or heritage-site fee is matched for this place. Local entry fees may still apply.</p>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {data.protected_areas.map((p) => (
            <Item key={p.name} title={`${p.name} entry`} status={p.status_label} basis={p.basis} source={p.source}>
              {p.fee_npr === 0 ? "Free for your nationality" : p.fee_npr != null ? <>NPR {p.fee_npr.toLocaleString()} {p.fee_basis || "per person"}</> : "Fee not listed"}
            </Item>
          ))}
          {data.restricted_areas.map((r) => (
            <Item key={r.name} title={`Restricted-area permit — ${r.name}`} status={r.status_label} basis={r.basis} source={r.source}>
              {r.fee_text}<span className="block">Issued via a registered agency; licensed guide and minimum two trekkers required.</span>
            </Item>
          ))}
          {data.tims ? (
            <Item title={`TIMS card — ${data.tims.region}`} status={data.tims.status_label} basis={data.tims.basis} source={data.tims.source}>
              {data.tims.fee_npr != null ? `NPR ${data.tims.fee_npr.toLocaleString()} per trekker. ` : ""}{data.tims.licensed_guide_required ? "Licensed trekking guide required." : ""}
            </Item>
          ) : null}
          {data.heritage_sites.map((h) => (
            <Item key={h.name} title={`${h.name} entry`} status={h.status_label} basis={h.basis} source={h.source}>
              {h.fee_npr === 0 ? "Free for your nationality" : h.fee_npr != null ? `NPR ${h.fee_npr.toLocaleString()} per person` : "Fee not listed"}{h.notes ? ` · ${h.notes}` : ""}
            </Item>
          ))}
        </ul>
      )}

      {(alt.above_threshold || data.tims || data.restricted_areas.length > 0) && data.insurance ? (
        <p className="flex items-start gap-2 rounded-xl border border-sky-200 bg-sky-50 p-3 text-xs text-sky-900">
          <FiShield className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>{data.insurance.statement} <Src source={data.insurance.source} /></span>
        </p>
      ) : null}

      <p className="text-[11px] text-slate-500">{data.matching_note} <Link className="underline" to="/before-you-travel">Visa & full requirements →</Link></p>
    </section>
  )
}
