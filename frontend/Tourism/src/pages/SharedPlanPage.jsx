import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { FiCalendar, FiLock, FiMapPin, FiUsers } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import exploreApi from "../api/exploreApi"
import useSeo from "../hooks/useSeo"
import CMSPageIntro from "../components/cms/CMSPageIntro"

// Public, read-only view of a travel plan its owner chose to share.
// The API strips the owner's identity and private notes; the page is
// noindex because share links are meant for the people they're sent to.

const stopName = (s) => s?.name || s?.title || s?.destination || "Stop"

export default function SharedPlanPage() {
  const { token } = useParams()
  const [state, setState] = useState({ status: "loading", plan: null })
  useSeo({ title: state.plan ? `${state.plan.title} · Shared plan` : "Shared travel plan", path: `/plans/shared/${token}`, noindex: true })

  useEffect(() => {
    let alive = true
    exploreApi.sharedPlan(token)
      .then(({ data }) => { if (alive) setState({ status: "ok", plan: data }) })
      .catch((err) => { if (alive) setState({ status: err?.response?.status === 404 ? "gone" : "error", plan: null }) })
    return () => { alive = false }
  }, [token])

  if (state.status === "loading") return <div className="container-app py-12 text-sm" role="status">Loading shared plan…</div>
  if (state.status !== "ok") {
    return (
      <div className="container-app py-12">
        <div className="card-base mx-auto max-w-lg border border-slate-200 bg-white p-6 text-center">
          <FiLock className="mx-auto text-2xl text-[var(--ny-text-muted)]" aria-hidden="true" />
          <h1 className="mt-2 text-xl font-bold">{state.status === "gone" ? "This plan isn't shared any more" : "Couldn't load this plan"}</h1>
          <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">
            {state.status === "gone" ? "The link may have been turned off by its owner, or it was mistyped." : "Please try again in a moment."}
          </p>
          <Link to="/itinerary" className="ny-btn ny-btn-primary mt-4 inline-flex">Plan your own trip</Link>
        </div>
      </div>
    )
  }

  const plan = state.plan
  const it = plan.itinerary || {}
  const days = Array.isArray(it.itinerary) ? it.itinerary : []
  return (
    <div className="container-app py-8">
      <PageHeader eyebrow="Shared travel plan" title={plan.title || "Travel plan"}
        subtitle={[it.start_city && `Starting from ${it.start_city}`, it.days && `${it.days} day${it.days === 1 ? "" : "s"}`].filter(Boolean).join(" · ")} />
      <CMSPageIntro pageKey="shared-plan" />
      <div className="mt-4 flex flex-wrap gap-3 text-sm text-[var(--ny-text-secondary)]">
        {plan.travelers ? <span className="inline-flex items-center gap-1"><FiUsers aria-hidden="true" /> {plan.travelers} traveller{plan.travelers === 1 ? "" : "s"}</span> : null}
        {plan.start_date ? <span className="inline-flex items-center gap-1"><FiCalendar aria-hidden="true" /> {plan.start_date}{plan.end_date ? ` – ${plan.end_date}` : ""}</span> : null}
        {plan.interests?.length ? <span>Interests: {plan.interests.join(", ")}</span> : null}
      </div>

      {it.why_this_itinerary?.length > 0 && (
        <section aria-labelledby="why-h" className="card-base mt-6 border border-slate-200 bg-white p-5">
          <h2 id="why-h" className="font-bold">Why this itinerary</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[var(--ny-text-secondary)]">{it.why_this_itinerary.map((w) => <li key={w}>{w}</li>)}</ul>
        </section>
      )}

      <ol className="mt-6 space-y-4">
        {days.map((day) => (
          <li key={day.day} className="card-base border border-slate-200 bg-white p-5">
            <h2 className="font-bold">Day {day.day}{day.theme ? `: ${day.theme}` : ""}</h2>
            {day.city && <p className="flex items-center gap-1 text-xs text-[var(--ny-text-secondary)]"><FiMapPin aria-hidden="true" /> {day.city}</p>}
            <ul className="mt-3 space-y-2 text-sm">
              {(day.destinations || []).map((s, i) => (
                <li key={`${stopName(s)}-${i}`} className="flex flex-wrap items-baseline gap-x-2">
                  {s.start_time && <span className="font-mono text-xs text-[var(--ny-text-muted)]">{s.start_time}</span>}
                  {s.slug ? <Link to={`/destinations/${s.slug}`} className="font-semibold hover:underline">{stopName(s)}</Link> : <span className="font-semibold">{stopName(s)}</span>}
                  {s.category && <span className="text-xs text-[var(--ny-text-secondary)]">{s.category}</span>}
                </li>
              ))}
              {(!day.destinations || day.destinations.length === 0) && <li className="text-[var(--ny-text-secondary)]">Free day. No stops planned.</li>}
            </ul>
          </li>
        ))}
        {days.length === 0 && plan.stops?.length > 0 && (
          <li className="card-base border border-slate-200 bg-white p-5">
            <ul className="space-y-1 text-sm">{plan.stops.map((s) => <li key={`${s.day}-${s.order}`}>Day {s.day}: <Link to={`/destinations/${s.slug}`} className="underline">{s.destination}</Link></li>)}</ul>
          </li>
        )}
      </ol>
      {[it.timing_note, it.data_note].filter(Boolean).map((n) => <p key={n} className="mt-3 text-xs text-[var(--ny-text-muted)]">{n}</p>)}
      <p className="mt-6 flex items-center gap-2 text-xs text-[var(--ny-text-muted)]"><FiLock aria-hidden="true" /> {plan.privacy}</p>
      <Link to="/itinerary" className="ny-btn ny-btn-primary mt-4 inline-flex">Plan your own trip</Link>
    </div>
  )
}
