import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiAlertTriangle, FiExternalLink, FiFileText, FiMap, FiShield, FiPhone, FiActivity, FiLoader } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import travelApi from "../api/travelApi"
import { NATIONALITY_OPTIONS } from "../utils/currency"

// "Before you travel" -- visa, TIMS, permits, park & heritage fees,
// altitude safety, insurance and official contacts. Every figure comes from
// /api/v1/travel-requirements/, which serves data transcribed from
// immigration.gov.np and ntb.gov.np with the source link and retrieval date.

const SourceLink = ({ source }) => source?.url ? (
  <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-[var(--ny-text-muted)] underline">
    Source: {source.publisher}{source.title ? ` — ${source.title}` : ""}{source.retrieved_at ? ` (retrieved ${source.retrieved_at})` : ""} <FiExternalLink size={11} />
  </a>
) : null

const Section = ({ id, icon: Icon, title, children, source }) => (
  <section id={id} aria-labelledby={`${id}-h`} className="card-base scroll-mt-24 border border-slate-200 bg-white p-5 sm:p-6">
    <h2 id={`${id}-h`} className="flex items-center gap-2 text-lg font-bold"><Icon aria-hidden="true" /> {title}</h2>
    <div className="mt-3 space-y-3 text-sm leading-6 text-[var(--ny-text-secondary)]">{children}</div>
    <div className="mt-3"><SourceLink source={source} /></div>
  </section>
)

const npr = (value) => (value == null ? "—" : `NPR ${Number(value).toLocaleString()}`)

const feeText = (row, nationality) => (row.fees_npr?.[nationality] === 0 ? "Free" : npr(row.fees_npr?.[nationality]))

const FeeTable = ({ rows, nationality, caption }) => (
  <>
  <ul className="divide-y divide-slate-100 sm:hidden" aria-label={caption}>
    {rows.map((row) => (
      <li key={row.name} className="py-2">
        <div className="flex items-start justify-between gap-3">
          <span className="min-w-0 font-medium text-[var(--ny-text)]">{row.name}</span>
          <span className="shrink-0 font-semibold">{feeText(row, nationality)}</span>
        </div>
        <p className="text-xs">{[row.fee_basis, row.note || row.notes, row.child_policy].filter(Boolean).join(" · ")}</p>
      </li>
    ))}
  </ul>
  <div className="hidden overflow-x-auto sm:block">
    <table className="w-full min-w-[20rem] text-left text-sm">
      <caption className="sr-only">{caption}</caption>
      <thead><tr className="border-b border-slate-200 text-xs uppercase text-gray-500"><th className="py-2 pr-3">Place</th><th className="py-2 pr-3">Your fee</th><th className="py-2">Notes</th></tr></thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.name} className="border-b border-slate-100 align-top">
            <td className="py-2 pr-3 font-medium text-[var(--ny-text)]">{row.name}</td>
            <td className="py-2 pr-3 whitespace-nowrap">{feeText(row, nationality)}</td>
            <td className="py-2 text-xs">{[row.fee_basis, row.note || row.notes, row.child_policy].filter(Boolean).join(" · ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
  </>
)

export default function BeforeYouTravel() {
  const [nationality, setNationality] = useState(() => localStorage.getItem("tourism_nationality") || "foreign")
  const [data, setData] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    let alive = true
    travelApi.requirements(nationality)
      .then(({ data: body }) => { if (alive) { setData(body); setError("") } })
      .catch(() => { if (alive) setError("Official requirements could not be loaded. Please check the linked government pages directly.") })
    return () => { alive = false }
  }, [nationality])

  const change = (value) => { setNationality(value); localStorage.setItem("tourism_nationality", value) }

  return (
    <div className="ny-page container-app py-6 sm:py-8">
      <PageHeader title="Before you travel" subtitle="Visa, trekking permits, park and heritage fees, altitude safety and insurance — from official Government of Nepal and Nepal Tourism Board sources." icon={FiFileText} />

      <div className="card-base mb-6 flex flex-col gap-3 border border-slate-200 bg-white p-4 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="byt-nationality" className="text-xs font-medium text-gray-500">Show fees for</label>
          <select id="byt-nationality" className="input-field mt-1" value={nationality} onChange={(e) => change(e.target.value)} data-testid="nationality-select">
            {NATIONALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <nav aria-label="Sections" className="flex flex-wrap gap-2 text-xs">
          {[["visa", "Visa"], ["tims", "TIMS"], ["permits", "Permits"], ["parks", "Parks"], ["heritage", "Heritage"], ["altitude", "Altitude"], ["insurance", "Insurance"], ["contacts", "Contacts"]].map(([id, label]) => (
            <a key={id} href={`#${id}`} className="ny-btn ny-btn-secondary min-h-9 px-3 text-xs">{label}</a>
          ))}
        </nav>
      </div>

      {error && <p role="alert" className="ny-panel mb-4 p-4 text-sm text-[var(--ny-danger)]">{error}</p>}
      {!data && !error && <p className="flex items-center gap-2 text-sm"><FiLoader className="animate-spin" /> Loading official requirements…</p>}

      {data && (
        <div className="grid grid-cols-1 gap-5">
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900" data-testid="requirements-disclaimer">
            <FiAlertTriangle className="mr-1 inline" aria-hidden="true" />{data.disclaimer}
          </p>

          <Section id="visa" icon={FiFileText} title="Tourist visa" source={data.visa.source}>
            {data.visa.applies === false ? <p>{data.visa.summary}</p> : (
              <>
                <p>{data.visa.summary}</p>
                {data.visa.fees_usd?.length ? (
                  <ul className="flex flex-wrap gap-2">{data.visa.fees_usd.map((f) => <li key={f.days} className="rounded-lg border border-slate-200 px-3 py-2"><strong>{f.days} days</strong>: US${f.usd}</li>)}</ul>
                ) : null}
                {data.visa.note ? <p className="text-xs">{data.visa.note}</p> : null}
                {data.visa.steps?.length ? <ol className="list-decimal space-y-1 pl-5">{data.visa.steps.map((s) => <li key={s}>{s}</li>)}</ol> : null}
                {data.visa.mission_visa_rule ? <p className="text-xs">{data.visa.mission_visa_rule}</p> : null}
                {data.visa.apply_url ? <p><a className="font-semibold underline" href={data.visa.apply_url} target="_blank" rel="noreferrer">Online tourist visa form</a></p> : null}
              </>
            )}
          </Section>

          <Section id="tims" icon={FiMap} title="TIMS card & licensed guide" source={data.tims.source}>
            <p>{data.tims.rule}</p>
            <p><strong>Fee for you:</strong> {data.tims.fees_npr?.[nationality] == null ? "Not applicable" : `${npr(data.tims.fees_npr[nationality])} ${data.tims.fee_basis || ""}`}</p>
            {data.tims.how ? <p className="text-xs">{data.tims.how}</p> : null}
            <details><summary className="cursor-pointer font-medium">Regions requiring TIMS ({data.tims.regions.length})</summary>
              <ul className="mt-2 list-disc space-y-1 pl-5">{data.tims.regions.map((r) => <li key={r.region}><strong>{r.region}</strong>{r.treks?.length ? `: ${r.treks.join(", ")}` : ""}</li>)}</ul>
            </details>
          </Section>

          <Section id="permits" icon={FiShield} title="Restricted-area permits" source={data.restricted_areas_source}>
            <p>Restricted areas require a special permit issued through a registered trekking agency, with a licensed guide and at least two trekkers.</p>
            <ul className="divide-y divide-slate-100">{data.restricted_areas.map((r) => (
              <li key={r.name} className="py-2"><p className="font-medium text-[var(--ny-text)]">{r.name}</p><p>{r.fee_text}</p>{r.covered_areas ? <p className="text-xs">Covers: {r.covered_areas}</p> : null}</li>
            ))}</ul>
            {data.restricted_area_note ? <p className="text-xs">{data.restricted_area_note}</p> : null}
          </Section>

          <Section id="parks" icon={FiMap} title="National park & conservation-area fees" source={data.protected_areas_source}>
            <FeeTable rows={data.protected_areas} nationality={nationality} caption="Protected-area entry fees" />
          </Section>

          <Section id="heritage" icon={FiMap} title="Heritage-site entry fees" source={data.heritage_source}>
            {data.heritage_note ? <p className="text-xs">{data.heritage_note}</p> : null}
            <FeeTable rows={data.heritage_sites} nationality={nationality} caption="Heritage-site entry fees" />
          </Section>

          <Section id="altitude" icon={FiActivity} title="Altitude sickness (AMS)" source={data.altitude.source}>
            <p className="font-medium text-[var(--ny-text)]">{data.altitude.headline}</p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div><h3 className="font-semibold">Prevention</h3><ul className="list-disc pl-5">{data.altitude.prevention.map((i) => <li key={i}>{i}</li>)}</ul></div>
              <div><h3 className="font-semibold">Early symptoms</h3><ul className="list-disc pl-5">{data.altitude.early_symptoms.map((i) => <li key={i}>{i}</li>)}</ul>
                <p className="mt-2 text-xs">{data.altitude.what_to_do?.join(" ")}</p></div>
              <div className="sm:col-span-2 rounded-xl border border-red-200 bg-red-50 p-3 text-red-900">
                <h3 className="font-semibold">Worsening symptoms</h3><p>{data.altitude.worsening_symptoms.join(", ")}</p><p className="mt-1 font-bold">{data.altitude.worsening_action}</p>
              </div>
            </div>
            {data.altitude.hra ? <p className="text-xs">{data.altitude.hra.name}: {data.altitude.hra.phone} · {data.altitude.hra.aid_posts}</p> : null}
          </Section>

          <Section id="insurance" icon={FiShield} title="Travel insurance checklist" source={data.insurance.source}>
            <p>{data.insurance.statement}</p>
            <ul className="grid gap-2 sm:grid-cols-2">{data.insurance.checklist.map((i) => <li key={i} className="flex gap-2"><input type="checkbox" aria-label={i} className="mt-1" /> <span>{i}</span></li>)}</ul>
            {data.insurance.checklist_note ? <p className="text-xs">{data.insurance.checklist_note}</p> : null}
          </Section>

          <Section id="contacts" icon={FiPhone} title="Official contacts & tourist police" source={data.official_contacts.source}>
            <p>{data.tourist_police.summary}</p>
            <ul className="grid gap-2 sm:grid-cols-2">{data.official_contacts.contacts.map((c) => (
              <li key={`${c.name}-${c.phone}`} className="rounded-lg border border-slate-200 p-2"><span className="block font-medium text-[var(--ny-text)]">{c.name}</span><a className="underline" href={`tel:${String(c.phone).replace(/[^0-9+]/g, "")}`}>{c.phone}</a></li>
            ))}</ul>
            <p className="text-xs">{data.official_contacts.note} <Link className="underline" to="/emergency">Emergency services near you →</Link></p>
          </Section>

          <Section id="safety" icon={FiAlertTriangle} title="Safety advice" source={data.safety_advice.source}>
            <ul className="list-disc space-y-1 pl-5">{data.safety_advice.items.map((i) => <li key={i}>{i}</li>)}</ul>
          </Section>
        </div>
      )}
    </div>
  )
}
