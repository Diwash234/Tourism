import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { FiSearch, FiAlertCircle, FiArrowRight, FiX } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import VerificationBadge from "../components/common/VerificationBadge"
import { OpenNowBadge } from "../components/explore/FactBits"
import exploreApi from "../api/exploreApi"
import useSeo from "../hooks/useSeo"
import usePublicConfig from "../hooks/usePublicConfig"
import { ROUTE_SEO } from "../utils/seoRoutes"
import CMSPageIntro from "../components/cms/CMSPageIntro"

// One search box for the whole site: destinations, districts, hotels,
// restaurants, services, permit rules and tools. Misspellings get a
// "did you mean" from real place names; if nothing matches, results for
// the closest real name are shown and labelled as such.

const MIN_CHARS = 2
const DEBOUNCE_MS = 300

const Result = ({ item }) => {
  const body = (
    <>
      <span className="min-w-0">
        <span className="block truncate font-semibold text-[var(--ny-text)]">{item.title}</span>
        {item.subtitle && <span className="block truncate text-xs text-[var(--ny-text-secondary)]">{item.subtitle}</span>}
        <span className="mt-1 flex flex-wrap gap-1.5">
          {item.verified === false && <VerificationBadge record={{ verified: false, source: item.source }} compact />}
          {item.hours && <OpenNowBadge hours={item.hours} compact />}
        </span>
      </span>
      <FiArrowRight className="shrink-0 text-[var(--ny-text-muted)]" aria-hidden="true" />
    </>
  )
  const cls = "flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 hover:bg-emerald-50 focus:bg-emerald-50 focus:outline-none"
  return item.path ? <Link to={item.path} className={cls}>{body}</Link> : <div className={cls}>{body}</div>
}

export default function SearchPage() {
  const [params, setParams] = useSearchParams()
  const urlQuery = params.get("q") || ""
  const [text, setText] = useState(urlQuery)
  const [state, setState] = useState({ status: "idle", data: null, error: "" })
  const controllerRef = useRef(null)

  // A query search gets its own noindex title; the bare page uses the CMS
  // record's SEO fields (fallback: ROUTE_SEO) so admins can edit them.
  const { pages } = usePublicConfig()
  const cmsPage = (pages || []).find((page) => page.route === "/search")
  useSeo({
    title: urlQuery ? `Search: ${urlQuery} · Nepal Yatra` : (cmsPage?.seo_title || cmsPage?.title || ROUTE_SEO["/search"].title),
    description: urlQuery ? undefined : (cmsPage?.meta_description || ROUTE_SEO["/search"].description),
    path: "/search",
    noindex: Boolean(urlQuery) || cmsPage?.search_visible === false,
  })

  // Keep the box in sync when the URL changes (back/forward, did-you-mean links).
  useEffect(() => {
    const t = setTimeout(() => setText(urlQuery), 0)
    return () => clearTimeout(t)
  }, [urlQuery])

  // Debounced URL update while typing.
  useEffect(() => {
    const trimmed = text.trim()
    if (trimmed === urlQuery) return undefined
    const t = setTimeout(() => {
      setParams(trimmed ? { q: trimmed } : {}, { replace: true })
    }, DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [text, urlQuery, setParams])

  // Fetch whenever the URL query changes; cancel stale requests.
  useEffect(() => {
    controllerRef.current?.abort()
    if (urlQuery.trim().length < MIN_CHARS) {
      const t = setTimeout(() => setState({ status: "idle", data: null, error: "" }), 0)
      return () => clearTimeout(t)
    }
    const controller = new AbortController()
    controllerRef.current = controller
    const start = setTimeout(() => setState((s) => ({ ...s, status: "loading", error: "" })), 0)
    exploreApi.search(urlQuery, { signal: controller.signal })
      .then(({ data }) => setState({ status: "done", data, error: "" }))
      .catch((err) => {
        if (controller.signal.aborted || err?.code === "ERR_CANCELED") return
        setState({ status: "error", data: null, error: "Search is unavailable right now. Please try again." })
      })
    return () => { clearTimeout(start); controller.abort() }
  }, [urlQuery])

  const data = state.data
  return (
    <div className="container-app py-8">
      <PageHeader eyebrow="Search" title="Search Nepal Yatra"
        subtitle="Places, districts, hotels, restaurants, banks and ATMs, permits and tools, all in one place." />
      <CMSPageIntro pageKey="search" />
      <form role="search" className="mt-6" onSubmit={(e) => { e.preventDefault(); setParams(text.trim() ? { q: text.trim() } : {}) }}>
        <label htmlFor="site-search" className="sr-only">Search</label>
        <div className="relative">
          <FiSearch className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" />
          <input id="site-search" type="search" value={text} onChange={(e) => setText(e.target.value)} autoFocus
            maxLength={120} placeholder="Try “Pokhara”, “ATM Thamel”, “Sagarmatha permit”…"
            className="input-field pl-11 pr-10 py-3 text-base" autoComplete="off" />
          {text && (
            <button type="button" onClick={() => { setText(""); setParams({}) }} aria-label="Clear search"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--ny-text-muted)] hover:text-[var(--ny-text)]">
              <FiX aria-hidden="true" />
            </button>
          )}
        </div>
      </form>

      <div className="mt-6" aria-live="polite">
        {state.status === "idle" && (
          <p className="text-sm text-[var(--ny-text-secondary)]">Type at least {MIN_CHARS} characters.</p>
        )}
        {state.status === "loading" && <p className="text-sm text-[var(--ny-text-secondary)]">Searching…</p>}
        {state.status === "error" && (
          <p className="flex items-center gap-2 text-sm text-rose-700"><FiAlertCircle aria-hidden="true" /> {state.error}</p>
        )}
        {state.status === "done" && data && (
          <>
            {data.showing_results_for && (
              <p className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                No results for “{data.query}”. Showing results for <strong>{data.showing_results_for}</strong>.
              </p>
            )}
            {!data.showing_results_for && data.did_you_mean?.length > 0 && (
              <p className="mb-4 text-sm">
                Did you mean{" "}
                {data.did_you_mean.map((s, i) => (
                  <span key={s}>{i > 0 && ", "}<Link className="font-semibold text-[var(--ny-green)] underline" to={`/search?q=${encodeURIComponent(s)}`}>{s}</Link></span>
                ))}?
              </p>
            )}
            {data.total === 0 ? (
              <div className="card-base border border-slate-200 bg-white p-6 text-sm">
                <p className="font-semibold">Nothing found for “{data.query}”.</p>
                <p className="mt-1 text-[var(--ny-text-secondary)]">
                  Check the spelling, try a district name, or <Link className="underline" to="/discover">browse places by activity</Link>.
                </p>
              </div>
            ) : (
              <div className="grid gap-5 lg:grid-cols-2">
                {data.groups.map((group) => (
                  <section key={group.type} aria-labelledby={`g-${group.type}`} className="card-base border border-slate-200 bg-white p-4">
                    <div className="mb-2 flex items-baseline justify-between gap-3 px-1">
                      <h2 id={`g-${group.type}`} className="text-sm font-bold uppercase tracking-wide text-[var(--ny-green)]">{group.label}</h2>
                      {group.more_path && group.total > group.items.length && (
                        <Link to={group.more_path} className="text-xs font-semibold text-[var(--ny-green)] underline">See all {group.total}</Link>
                      )}
                    </div>
                    <ul className="divide-y divide-slate-100">
                      {group.items.map((item) => <li key={item.id}><Result item={item} /></li>)}
                    </ul>
                  </section>
                ))}
              </div>
            )}
            {data.total > 0 && data.notes?.map((n) => <p key={n} className="mt-4 text-xs text-[var(--ny-text-muted)]">{n}</p>)}
          </>
        )}
      </div>
    </div>
  )
}
