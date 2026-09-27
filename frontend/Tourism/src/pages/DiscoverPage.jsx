import { useEffect, useMemo, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { FiFilter, FiMapPin, FiAlertTriangle, FiInfo, FiCrosshair } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import PlaceholderImage from "../components/common/PlaceholderImage"
import { FactChips, SeasonBadge, SourceLink } from "../components/explore/FactBits"
import exploreApi from "../api/exploreApi"
import { getDestinationImageUrl } from "../utils/imageUtils"
import CMSPageIntro from "../components/cms/CMSPageIntro"

// Traveller filters over every public destination. Filter state lives in the
// URL so results are shareable. Filters on a fact a place lacks (for example
// elevation) exclude that place; the coverage note says how many have it.

const MULTI = ["activity", "difficulty", "cost", "accessibility", "reach"]
const SINGLE = ["q", "month", "season_fit", "origin", "min_elevation", "max_elevation", "sort", "origin_lat", "origin_lng"]
const PAGE_SIZE = 24

const Chip = ({ active, onClick, children }) => (
  <button type="button" onClick={onClick} aria-pressed={active}
    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${active
      ? "border-[var(--ny-green)] bg-[var(--ny-green)] text-white"
      : "border-slate-200 bg-white text-slate-700 hover:border-[var(--ny-green)]"}`}>
    {children}
  </button>
)

const Group = ({ title, note, children }) => (
  <fieldset className="space-y-2">
    <legend className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">{title}</legend>
    <div className="flex flex-wrap gap-1.5">{children}</div>
    {note && <p className="text-[11px] leading-4 text-[var(--ny-text-muted)]">{note}</p>}
  </fieldset>
)

const ResultCard = ({ result }) => {
  const d = result.destination
  return (
    <article className="card-base flex h-full flex-col overflow-hidden border border-slate-200 bg-white">
      <div className="relative h-40 bg-[#EAF1EE]">
        <PlaceholderImage src={d.cover_image_url || getDestinationImageUrl(d)} title={d.name} alt={d.name} className="h-full w-full" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h3 className="text-base font-bold leading-snug">{d.name}</h3>
        {(d.district || d.category_name) && (
          <p className="flex items-center gap-1 text-xs text-[var(--ny-text-secondary)]">
            <FiMapPin size={12} aria-hidden="true" />{[d.category_name, d.district].filter(Boolean).join(" · ")}
          </p>
        )}
        {result.facts?.season && <SeasonBadge season={result.facts.season} />}
        <FactChips facts={result.facts} />
        {result.why?.length > 0 && (
          <ul className="space-y-1 text-xs text-[var(--ny-text-secondary)]">
            {result.why.slice(0, 3).map((w) => <li key={w} className="line-clamp-2">• {w}</li>)}
          </ul>
        )}
        <div className="mt-auto pt-2">
          <Link to={`/destinations/${d.slug}`} className="ny-btn ny-btn-secondary w-full justify-center text-sm">View details</Link>
        </div>
      </div>
    </article>
  )
}

export default function DiscoverPage() {
  const [params, setParams] = useSearchParams()
  const [options, setOptions] = useState(null)
  const [state, setState] = useState({ status: "loading", items: [], data: null, error: "" })
  const [page, setPage] = useState(1)
  const [locating, setLocating] = useState(false)
  const controllerRef = useRef(null)

  // SEO comes from the CMS page record (fallback: ROUTE_SEO) via useRouteSeo.

  const filters = useMemo(() => {
    const f = {}
    MULTI.forEach((k) => { const v = params.get(k); if (v) f[k] = v })
    SINGLE.forEach((k) => { const v = params.get(k); if (v) f[k] = v })
    return f
  }, [params])
  const filterKey = JSON.stringify(filters)

  useEffect(() => {
    exploreApi.discoverOptions().then(({ data }) => setOptions(data)).catch(() => setOptions(null))
  }, [])

  // Reset to page 1 whenever the filters change.
  useEffect(() => { const t = setTimeout(() => setPage(1), 0); return () => clearTimeout(t) }, [filterKey])

  useEffect(() => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    const start = setTimeout(() => setState((s) => ({ ...s, status: page === 1 ? "loading" : "more", error: "" })), 0)
    exploreApi.discover({ ...JSON.parse(filterKey), page, page_size: PAGE_SIZE }, { signal: controller.signal })
      .then(({ data }) => setState((s) => ({
        status: "done", data, error: "", items: page === 1 ? data.results : [...s.items, ...data.results],
      })))
      .catch((err) => {
        if (controller.signal.aborted || err?.code === "ERR_CANCELED") return
        setState((s) => ({ ...s, status: "error", error: "Could not load places. Please try again." }))
      })
    return () => { clearTimeout(start); controller.abort() }
  }, [filterKey, page])

  const setParam = (key, value) => {
    const next = new URLSearchParams(params)
    if (value === "" || value == null) next.delete(key)
    else next.set(key, value)
    if (key === "month" && !value) next.delete("season_fit")
    if (key === "origin") { next.delete("origin_lat"); next.delete("origin_lng") }
    setParams(next, { replace: true })
  }
  const toggle = (key, value) => {
    const current = new Set((params.get(key) || "").split(",").filter(Boolean))
    if (current.has(value)) current.delete(value)
    else current.add(value)
    setParam(key, [...current].join(","))
  }
  const has = (key, value) => (params.get(key) || "").split(",").includes(value)
  const hasOrigin = Boolean(params.get("origin") || params.get("origin_lat"))

  const useMyLocation = () => {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const next = new URLSearchParams(params)
        next.delete("origin")
        next.set("origin_lat", pos.coords.latitude.toFixed(4))
        next.set("origin_lng", pos.coords.longitude.toFixed(4))
        setParams(next, { replace: true })
        setLocating(false)
      },
      () => setLocating(false),
      { timeout: 10000, maximumAge: 300000 },
    )
  }

  const data = state.data
  const activeCount = Object.keys(filters).filter((k) => k !== "sort").length

  return (
    <div className="container-app py-8">
      <PageHeader eyebrow="Discover" title="Find places by what you want to do"
        subtitle="Filter by activity, effort, altitude, season, official fees, accessibility and distance from where you start." />
      <CMSPageIntro pageKey="discover" />

      <div className="mt-6 grid gap-6 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <aside aria-label="Filters" className="card-base h-fit space-y-5 border border-slate-200 bg-white p-4 lg:sticky lg:top-24">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-bold"><FiFilter aria-hidden="true" /> Filters</h2>
            {activeCount > 0 && <button type="button" onClick={() => setParams({}, { replace: true })} className="text-xs font-semibold text-[var(--ny-green)] underline">Clear all</button>}
          </div>

          <div>
            <label htmlFor="discover-q" className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">Name or district</label>
            <input id="discover-q" className="input-field mt-1" defaultValue={params.get("q") || ""} maxLength={120}
              placeholder="e.g. Mustang" onKeyDown={(e) => { if (e.key === "Enter") setParam("q", e.currentTarget.value.trim()) }}
              onBlur={(e) => setParam("q", e.currentTarget.value.trim())} />
          </div>

          <Group title="Activity">
            {(options?.activities || []).map((a) => <Chip key={a.key} active={has("activity", a.key)} onClick={() => toggle("activity", a.key)}>{a.label}</Chip>)}
          </Group>

          <div className="space-y-2">
            <label htmlFor="discover-month" className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">When are you going?</label>
            <select id="discover-month" className="input-field" value={params.get("month") || ""} onChange={(e) => setParam("month", e.target.value)}>
              <option value="">Any month</option>
              {(options?.months || []).map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
            {params.get("month") && (
              <div className="flex flex-wrap gap-1.5">
                {(options?.season_fit || []).map((s) => <Chip key={s.key} active={params.get("season_fit") === s.key} onClick={() => setParam("season_fit", params.get("season_fit") === s.key ? "" : s.key)}>{s.label} or better</Chip>)}
              </div>
            )}
            <SourceLink source={options?.season_source} />
          </div>

          <Group title="Effort" note={options?.difficulty_note}>
            {(options?.difficulties || []).map((d) => <Chip key={d.key} active={has("difficulty", d.key)} onClick={() => toggle("difficulty", d.key)}>{d.label}</Chip>)}
          </Group>

          <fieldset className="space-y-2">
            <legend className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">Altitude (m)</legend>
            <div className="flex items-center gap-2">
              <input type="number" min="0" max="9000" step="100" aria-label="Minimum altitude in metres" className="input-field" placeholder="Min"
                defaultValue={params.get("min_elevation") || ""} onBlur={(e) => setParam("min_elevation", e.currentTarget.value)} />
              <span aria-hidden="true">–</span>
              <input type="number" min="0" max="9000" step="100" aria-label="Maximum altitude in metres" className="input-field" placeholder="Max"
                defaultValue={params.get("max_elevation") || ""} onBlur={(e) => setParam("max_elevation", e.currentTarget.value)} />
            </div>
          </fieldset>

          <Group title="Official fees">
            {(options?.costs || []).map((c) => <Chip key={c.key} active={has("cost", c.key)} onClick={() => toggle("cost", c.key)}>{c.label}</Chip>)}
          </Group>

          <Group title="Accessibility" note={options?.accessibility_note}>
            {(options?.accessibility || []).map((a) => <Chip key={a.key} active={has("accessibility", a.key)} onClick={() => toggle("accessibility", a.key)}>{a.label}</Chip>)}
          </Group>

          <div className="space-y-2">
            <label htmlFor="discover-origin" className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">Starting from</label>
            <select id="discover-origin" className="input-field" value={params.get("origin") || (params.get("origin_lat") ? "__gps" : "")}
              onChange={(e) => { if (e.target.value === "__gps") return; setParam("origin", e.target.value) }}>
              <option value="">Not set</option>
              {params.get("origin_lat") && <option value="__gps">My location</option>}
              {(options?.origins || []).map((o) => <option key={o.slug} value={o.slug}>{o.label}</option>)}
            </select>
            <button type="button" onClick={useMyLocation} className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--ny-green)] underline" disabled={locating}>
              <FiCrosshair aria-hidden="true" /> {locating ? "Locating…" : "Use my location"}
            </button>
            {hasOrigin && (
              <div className="flex flex-wrap gap-1.5">
                {(options?.reach || []).map((r) => <Chip key={r.key} active={has("reach", r.key)} onClick={() => toggle("reach", r.key)}>{r.label}</Chip>)}
              </div>
            )}
          </div>
        </aside>

        <section aria-labelledby="discover-results-h" aria-busy={state.status === "loading"}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="discover-results-h" className="text-lg font-bold">
              {state.status === "loading" ? "Finding places…" : `${(data?.count || 0).toLocaleString()} place${data?.count === 1 ? "" : "s"}`}
            </h2>
            <label className="flex items-center gap-2 text-sm">
              <span className="text-[var(--ny-text-secondary)]">Sort</span>
              <select className="input-field w-auto py-1.5" value={params.get("sort") || "recommended"} onChange={(e) => setParam("sort", e.target.value === "recommended" ? "" : e.target.value)}>
                <option value="recommended">Recommended</option>
                <option value="distance" disabled={!hasOrigin}>Nearest first</option>
                <option value="elevation_asc">Lowest altitude</option>
                <option value="elevation_desc">Highest altitude</option>
                <option value="name">Name</option>
              </select>
            </label>
          </div>

          {data?.warnings?.map((w) => (
            <p key={w} className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"><FiAlertTriangle className="mt-0.5 shrink-0" aria-hidden="true" />{w}</p>
          ))}
          {data?.coverage?.note && (
            <p className="mt-3 flex items-start gap-2 text-xs text-[var(--ny-text-muted)]"><FiInfo className="mt-0.5 shrink-0" aria-hidden="true" />{data.coverage.note}</p>
          )}
          {state.status === "error" && <p className="mt-6 text-sm text-rose-700">{state.error}</p>}
          {state.status === "done" && data?.count === 0 && (
            <div className="card-base mt-6 border border-slate-200 bg-white p-6 text-sm">
              <p className="font-semibold">No places match all of these filters.</p>
              <p className="mt-1 text-[var(--ny-text-secondary)]">Remove a filter. Altitude and effort filters only include places with a measured elevation.</p>
            </div>
          )}
          <div className="mt-5 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {state.items.map((r) => <ResultCard key={r.destination.id} result={r} />)}
          </div>
          {data?.has_next && (
            <div className="mt-6 flex justify-center">
              <button type="button" className="ny-btn ny-btn-secondary" disabled={state.status === "more"} onClick={() => setPage((p) => p + 1)}>
                {state.status === "more" ? "Loading…" : "Show more"}
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
