import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { FiCheckCircle, FiHelpCircle, FiMinusCircle, FiPlus, FiX, FiSearch } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import { SeasonBadge, SourceLink } from "../components/explore/FactBits"
import exploreApi from "../api/exploreApi"
import { NATIONALITY_OPTIONS } from "../utils/currency"
import CMSPageIntro from "../components/cms/CMSPageIntro"

// "Which should I choose?" Side-by-side facts for 2-4 places with a verdict
// per criterion. A criterion is only judged when every place has a value;
// otherwise it says "can't judge" and why. No scores are invented.

const MAX = 4

const PlacePicker = ({ onPick, exclude }) => {
  const [q, setQ] = useState("")
  const [items, setItems] = useState([])
  const ref = useRef(null)
  useEffect(() => {
    ref.current?.abort()
    if (q.trim().length < 2) { const t = setTimeout(() => setItems([]), 0); return () => clearTimeout(t) }
    const controller = new AbortController()
    ref.current = controller
    const t = setTimeout(() => {
      exploreApi.search(q.trim(), { signal: controller.signal })
        .then(({ data }) => setItems((data.groups.find((g) => g.type === "destinations")?.items || []).filter((i) => !exclude.includes(String(i.id)))))
        .catch(() => {})
    }, 250)
    return () => { clearTimeout(t); controller.abort() }
  }, [q, exclude])
  return (
    <div className="relative">
      <label htmlFor="decide-add" className="sr-only">Add a place to compare</label>
      <FiSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" />
      <input id="decide-add" className="input-field pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Add a place, e.g. Namche" autoComplete="off" />
      {items.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-lg">
          {items.map((i) => (
            <li key={i.id}>
              <button type="button" className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-emerald-50"
                onClick={() => { onPick(i); setQ(""); setItems([]) }}>
                <FiPlus aria-hidden="true" className="shrink-0" />
                <span className="min-w-0"><span className="block truncate font-semibold">{i.title}</span><span className="block truncate text-xs text-[var(--ny-text-secondary)]">{i.subtitle}</span></span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

const VerdictIcon = ({ v }) => {
  if (!v.judged) return <FiHelpCircle className="shrink-0 text-slate-400" aria-label="Can't judge" />
  if (v.tie) return <FiMinusCircle className="shrink-0 text-slate-500" aria-label="No difference" />
  return <FiCheckCircle className="shrink-0 text-emerald-600" aria-label="Judged" />
}

const npr = (v) => (v == null ? "None on record" : `NPR ${Number(v).toLocaleString()}`)

export default function DecidePage() {
  const [params, setParams] = useSearchParams()
  const ids = (params.get("ids") || "").split(",").filter(Boolean).slice(0, MAX)
  const idKey = ids.join(",")
  const [origins, setOrigins] = useState([])
  const [state, setState] = useState({ status: "idle", data: null, error: "" })

  // SEO comes from the CMS page record (fallback: ROUTE_SEO) via useRouteSeo.

  useEffect(() => {
    exploreApi.discoverOptions().then(({ data }) => setOrigins(data.origins || [])).catch(() => setOrigins([]))
  }, [])

  const query = { ids: idKey, month: params.get("month") || "", origin: params.get("origin") || "", days: params.get("days") || "", nationality: params.get("nationality") || "foreign" }
  const queryKey = JSON.stringify(query)

  useEffect(() => {
    const q = JSON.parse(queryKey)
    if (q.ids.split(",").filter(Boolean).length < 2) { const t = setTimeout(() => setState({ status: "idle", data: null, error: "" }), 0); return () => clearTimeout(t) }
    const controller = new AbortController()
    const start = setTimeout(() => setState((s) => ({ ...s, status: "loading", error: "" })), 0)
    exploreApi.decide(Object.fromEntries(Object.entries(q).filter(([, v]) => v)), { signal: controller.signal })
      .then(({ data }) => setState({ status: "done", data, error: "" }))
      .catch((err) => {
        if (controller.signal.aborted) return
        setState({ status: "error", data: null, error: err?.response?.data?.detail || "Could not compare these places." })
      })
    return () => { clearTimeout(start); controller.abort() }
  }, [queryKey])

  const setParam = (k, v) => { const n = new URLSearchParams(params); if (v) n.set(k, v); else n.delete(k); setParams(n, { replace: true }) }
  const addId = (item) => setParam("ids", [...ids, String(item.id)].slice(0, MAX).join(","))
  const removeId = (id) => setParam("ids", ids.filter((x) => x !== String(id)).join(","))

  const data = state.data
  const places = data?.places || []

  return (
    <div className="container-app py-8">
      <PageHeader eyebrow="Decide" title="Which place should I choose?"
        subtitle="Compare 2–4 places on the facts that matter. Each verdict says why, and anything we can't judge is marked as such." />
      <CMSPageIntro pageKey="decide" />

      <section aria-label="Comparison settings" className="card-base mt-6 grid gap-4 border border-slate-200 bg-white p-4 md:grid-cols-2 xl:grid-cols-5">
        <div className="md:col-span-2">
          {ids.length < MAX ? <PlacePicker onPick={addId} exclude={ids} /> : <p className="text-sm text-[var(--ny-text-secondary)]">Up to {MAX} places.</p>}
        </div>
        <label className="text-sm"><span className="sr-only">Month</span>
          <select className="input-field" value={params.get("month") || ""} onChange={(e) => setParam("month", e.target.value)} aria-label="Travel month">
            <option value="">This month</option>
            {["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </label>
        <select className="input-field" value={params.get("origin") || ""} onChange={(e) => setParam("origin", e.target.value)} aria-label="Starting district">
          <option value="">Starting from (not set)</option>
          {origins.map((o) => <option key={o.slug} value={o.slug}>{o.label}</option>)}
        </select>
        <select className="input-field" value={params.get("nationality") || "foreign"} onChange={(e) => setParam("nationality", e.target.value)} aria-label="Nationality for fees">
          {NATIONALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </section>

      {ids.length < 2 && (
        <p className="mt-6 text-sm text-[var(--ny-text-secondary)]">Add at least two places to compare. You can also start from <Link to="/discover" className="underline">Discover</Link>.</p>
      )}
      {state.status === "loading" && <p className="mt-6 text-sm" role="status">Comparing…</p>}
      {state.status === "error" && <p className="mt-6 text-sm text-rose-700">{state.error}</p>}

      {state.status === "done" && data && (
        <>
          <section aria-labelledby="verdicts-h" className="mt-6">
            <h2 id="verdicts-h" className="text-lg font-bold">Verdicts for {data.month_name}{data.origin ? `, from ${data.origin.label}` : ""}</h2>
            <ul className="mt-3 grid gap-3 md:grid-cols-2">
              {data.verdicts.map((v) => (
                <li key={v.key} className="card-base flex gap-3 border border-slate-200 bg-white p-4">
                  <VerdictIcon v={v} />
                  <div className="min-w-0 text-sm">
                    <p className="font-semibold">{v.title}{v.judged && !v.tie && v.winner_names?.length ? `: ${v.winner_names.join(", ")}` : ""}{v.judged && v.tie ? ": no difference" : ""}</p>
                    <p className="mt-1 text-[var(--ny-text-secondary)]">{v.explanation}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="facts-h" className="mt-8">
            <h2 id="facts-h" className="text-lg font-bold">The facts behind them</h2>
            <div className="mt-3 grid gap-4" style={{ gridTemplateColumns: `repeat(auto-fit, minmax(15rem, 1fr))` }}>
              {places.map((p) => (
                <article key={p.id} className="card-base space-y-3 border border-slate-200 bg-white p-4 text-sm">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <h3 className="font-bold leading-snug"><Link to={`/destinations/${p.slug}`} className="hover:underline">{p.name}</Link></h3>
                      <p className="text-xs text-[var(--ny-text-secondary)]">{[p.card?.district, p.card?.province].filter(Boolean).join(", ")}</p>
                    </div>
                    <button type="button" onClick={() => removeId(p.id)} aria-label={`Remove ${p.name}`} className="rounded p-1 text-[var(--ny-text-muted)] hover:bg-slate-100"><FiX aria-hidden="true" /></button>
                  </div>
                  <SeasonBadge season={p.facts?.season} withReason />
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
                    <dt className="text-[var(--ny-text-secondary)]">Altitude</dt>
                    <dd>{p.facts?.elevation?.meters != null ? `${p.facts.elevation.meters.toLocaleString()} m` : "Not on record"}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Effort</dt>
                    <dd title={p.facts?.difficulty?.basis}>{p.facts?.difficulty?.label}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Distance</dt>
                    <dd>{p.facts?.distance_from_origin_km != null ? `${p.facts.distance_from_origin_km} km straight line` : "Set a starting district"}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Acclimatise</dt>
                    <dd>{p.facts?.acclimatization ? `At least ${p.facts.acclimatization.minimum_days} day(s) ascending` : p.facts?.elevation?.meters != null ? "Not needed below 2,500 m" : "Unknown"}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Fixed fees</dt>
                    <dd>{npr(p.requirements?.fixed_fees_npr_per_person)}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Hospital</dt>
                    <dd>{p.facts?.nearest_hospital ? `${p.facts.nearest_hospital.km} km, ${p.facts.nearest_hospital.name}${p.facts.nearest_hospital.verified ? "" : " (unverified listing)"}` : "None on record"}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Stays</dt>
                    <dd>{p.hotels ? `${p.hotels.verified} verified, ${p.hotels.unverified} unverified nearby` : "—"}</dd>
                    <dt className="text-[var(--ny-text-secondary)]">Reviews</dt>
                    <dd>{p.sentiment?.overall ? `${p.sentiment.review_count}, mostly ${p.sentiment.overall.label}` : p.sentiment?.message || "None yet"}</dd>
                  </dl>
                  {p.requirements?.fees?.length > 0 && (
                    <ul className="space-y-1 border-t border-slate-100 pt-2 text-xs text-[var(--ny-text-secondary)]">
                      {p.requirements.fees.map((f) => <li key={f.label}>{f.label}: {f.amount_per_person != null ? `${f.currency} ${Number(f.amount_per_person).toLocaleString()}` : "price set by agency"}</li>)}
                    </ul>
                  )}
                  {p.facts?.cost?.source && <SourceLink source={p.facts.cost.source} />}
                </article>
              ))}
            </div>
            <p className="mt-4 text-xs text-[var(--ny-text-muted)]">
              Distances are straight lines between recorded coordinates; roads are longer. Hospital positions come from imported listings and may be approximate.
              Effort is derived from altitude, not an official grading. Fees are fixed official fees matched by name and district. Check <Link to="/before-you-travel" className="underline">Before you travel</Link>.
            </p>
          </section>
        </>
      )}
    </div>
  )
}
