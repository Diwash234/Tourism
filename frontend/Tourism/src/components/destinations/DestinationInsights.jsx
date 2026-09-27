import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiCalendar, FiMessageSquare, FiThermometer } from "react-icons/fi"
import exploreApi from "../../api/exploreApi"
import destinationApi from "../../api/destinationApi"
import useAuth from "../../hooks/useAuth"
import { SourceLink, monthNow } from "../explore/FactBits"

// "When to go" (NTB climate guidance, month by month) and "What travellers
// say" (VADER sentiment over approved English reviews, shown only once there
// are enough reviews). Both panels state their method and source.

const LEVEL_BG = {
  best: "bg-emerald-600 text-white",
  good: "bg-emerald-200 text-emerald-950",
  fair: "bg-slate-200 text-slate-800",
  caution: "bg-amber-200 text-amber-950",
  poor: "bg-rose-200 text-rose-950",
}

const WhenToGo = ({ destinationKey }) => {
  const [data, setData] = useState(null)
  const [selected, setSelected] = useState(monthNow())
  useEffect(() => {
    let alive = true
    exploreApi.seasonGuide(undefined, destinationKey).then(({ data: d }) => { if (alive) setData(d) }).catch(() => { if (alive) setData(false) })
    return () => { alive = false }
  }, [destinationKey])
  if (data === false) return null
  if (!data) return <div className="card-base h-40 animate-pulse border border-slate-200 bg-white" aria-hidden="true" />
  const current = data.months[selected - 1]
  const t = data.temperatures
  return (
    <section aria-labelledby="when-to-go-h" className="card-base border border-slate-200 bg-white p-5">
      <h2 id="when-to-go-h" className="flex items-center gap-2 text-lg font-bold"><FiCalendar aria-hidden="true" /> When to go</h2>
      <div className="mt-3 grid grid-cols-6 gap-1 sm:grid-cols-12" role="group" aria-label="Choose a month">
        {data.months.map((m) => (
          <button key={m.month} type="button" onClick={() => setSelected(m.month)} aria-pressed={selected === m.month}
            title={`${m.month_name}: ${m.label}`}
            className={`rounded-md px-1 py-2 text-[11px] font-bold ${LEVEL_BG[m.level] || LEVEL_BG.fair} ${selected === m.month ? "ring-2 ring-offset-1 ring-[var(--ny-text)]" : ""}`}>
            {m.month_name.slice(0, 3)}
          </button>
        ))}
      </div>
      <p className="mt-3 text-sm"><strong>{current.month_name}: {current.label}.</strong> <span className="text-[var(--ny-text-secondary)]">{current.reason}</span></p>
      {current.notes?.map((n) => <p key={n} className="mt-1 text-xs text-amber-800">{n}</p>)}
      {t && (
        <p className="mt-2 flex items-start gap-1.5 text-xs text-[var(--ny-text-secondary)]">
          <FiThermometer className="mt-0.5 shrink-0" aria-hidden="true" />
          Around {t.winter_min_c}–{t.winter_max_c} °C in winter and {t.summer_min_c}–{t.summer_max_c} °C in summer. {t.basis}
        </p>
      )}
      {data.destination.elevation_m == null && (
        <p className="mt-2 text-xs text-[var(--ny-text-muted)]">No measured elevation for this place, so altitude-specific advice is not included.</p>
      )}
      <p className="mt-2 text-xs text-[var(--ny-text-muted)]">{data.disclaimer}</p>
      <div className="mt-2 flex flex-wrap gap-3">{data.sources.map((s) => <SourceLink key={s.url} source={s} />)}</div>
    </section>
  )
}

const pct = (x) => `${Math.round((x || 0) * 100)}%`

const TravellerSentiment = ({ destinationKey }) => {
  const [data, setData] = useState(null)
  useEffect(() => {
    let alive = true
    exploreApi.sentiment(destinationKey).then(({ data: d }) => { if (alive) setData(d) }).catch(() => { if (alive) setData(false) })
    return () => { alive = false }
  }, [destinationKey])
  if (!data) return null
  return (
    <section aria-labelledby="sentiment-h" className="card-base border border-slate-200 bg-white p-5">
      <h2 id="sentiment-h" className="flex items-center gap-2 text-lg font-bold"><FiMessageSquare aria-hidden="true" /> What travellers say</h2>
      {data.status !== "ok" ? (
        <div className="mt-2 text-sm text-[var(--ny-text-secondary)]">
          <p>{data.message}</p>
          {data.ratings?.count > 0 && <p className="mt-1">{data.ratings.count} star rating(s), average {data.ratings.average} / 5.</p>}
        </div>
      ) : (
        <div className="mt-3 space-y-3 text-sm">
          <p>
            Based on <strong>{data.analysed_count}</strong> review{data.analysed_count === 1 ? "" : "s"}, travellers are mostly <strong>{data.overall.label}</strong>.
            {data.ratings?.count > 0 && ` Star rating: ${data.ratings.average} / 5 from ${data.ratings.count}.`}
          </p>
          <div className="flex h-3 overflow-hidden rounded-full bg-slate-100" role="img"
            aria-label={`Positive ${pct(data.distribution.positive.share)}, neutral ${pct(data.distribution.neutral.share)}, negative ${pct(data.distribution.negative.share)}`}>
            <span className="bg-emerald-500" style={{ width: pct(data.distribution.positive.share) }} />
            <span className="bg-slate-300" style={{ width: pct(data.distribution.neutral.share) }} />
            <span className="bg-rose-400" style={{ width: pct(data.distribution.negative.share) }} />
          </div>
          <p className="text-xs text-[var(--ny-text-secondary)]">
            {data.distribution.positive.count} positive · {data.distribution.neutral.count} neutral · {data.distribution.negative.count} negative
          </p>
          {data.aspects?.length > 0 && (
            <ul className="flex flex-wrap gap-1.5" aria-label="What reviews mention">
              {data.aspects.map((a) => (
                <li key={a.key} className={`rounded-full border px-2 py-0.5 text-xs ${a.label_sentiment === "positive" ? "border-emerald-200 bg-emerald-50" : a.label_sentiment === "negative" ? "border-rose-200 bg-rose-50" : "border-slate-200 bg-slate-50"}`}>
                  {a.label}: {a.label_sentiment} ({a.mentions})
                </li>
              ))}
            </ul>
          )}
          {data.highlights?.positive && <blockquote className="border-l-4 border-emerald-300 pl-3 text-xs italic">“{data.highlights.positive}”</blockquote>}
          {data.highlights?.negative && <blockquote className="border-l-4 border-rose-300 pl-3 text-xs italic">“{data.highlights.negative}”</blockquote>}
        </div>
      )}
      {data.not_analysed_count > 0 && <p className="mt-2 text-xs text-[var(--ny-text-muted)]">{data.not_analysed_count} review(s) not analysed. {data.not_analysed_reason}</p>}
      {data.method && (
        <p className="mt-2 text-xs text-[var(--ny-text-muted)]">
          Method: {typeof data.method === "string" ? data.method : data.method.name}
          {data.method.scope ? `. ${data.method.scope}` : ""}
          {data.method.url && <> · <a href={data.method.url} target="_blank" rel="noreferrer" className="underline">{data.method.citation || "method paper"}</a></>}
        </p>
      )}
    </section>
  )
}


const MIN_REVIEW_CHARS = 20

const Reviews = ({ destination }) => {
  const { isAuthenticated } = useAuth() || {}
  const [items, setItems] = useState(null)
  const [text, setText] = useState("")
  const [status, setStatus] = useState({ kind: "", message: "" })
  useEffect(() => {
    let alive = true
    destinationApi.getReviews(destination.slug, destination.id)
      .then(({ data }) => { if (alive) setItems(Array.isArray(data) ? data : data?.results || []) })
      .catch(() => { if (alive) setItems([]) })
    return () => { alive = false }
  }, [destination.id, destination.slug])
  const mine = (items || []).find((r) => r.moderation_status === "pending")
  const submit = async (e) => {
    e.preventDefault()
    const comment = text.trim()
    if (comment.length < MIN_REVIEW_CHARS) { setStatus({ kind: "error", message: `Please write at least ${MIN_REVIEW_CHARS} characters.` }); return }
    setStatus({ kind: "busy", message: "" })
    try {
      const { data } = await destinationApi.addReview(destination.slug, destination.id, { comment })
      setItems((list) => [data, ...(list || [])])
      setText("")
      setStatus({ kind: "ok", message: "Thanks! Your review will appear once a moderator approves it." })
    } catch (err) {
      const d = err?.response?.data
      setStatus({ kind: "error", message: (d && (d.destination?.[0] || d.comment?.[0] || d.detail)) || "Could not send your review." })
    }
  }
  return (
    <section id="reviews" aria-labelledby="reviews-h" className="card-base scroll-mt-24 border border-slate-200 bg-white p-5 lg:col-span-2">
      <h2 id="reviews-h" className="text-lg font-bold">Traveller reviews</h2>
      {items === null ? <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">Loading reviews…</p> : (
        items.filter((r) => r.moderation_status === "approved").length === 0
          ? <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">No approved reviews yet.</p>
          : (
            <ul className="mt-3 divide-y divide-slate-100">
              {items.filter((r) => r.moderation_status === "approved").slice(0, 10).map((r) => (
                <li key={r.id} className="py-3 text-sm">
                  <p className="whitespace-pre-line">{r.comment}</p>
                  <p className="mt-1 text-xs text-[var(--ny-text-muted)]">{r.user_name || "Traveller"} · {new Date(r.created_at).toLocaleDateString()}</p>
                </li>
              ))}
            </ul>
          )
      )}
      {mine && <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-900">Your review is waiting for moderation.</p>}
      {isAuthenticated ? (!mine && (
        <form onSubmit={submit} className="mt-4 space-y-2">
          <label htmlFor="review-text" className="text-sm font-semibold">Share your experience</label>
          <textarea id="review-text" className="input-field min-h-24" maxLength={2000} value={text} onChange={(e) => setText(e.target.value)}
            placeholder="What was it like? Access, safety, crowds, value, views…" />
          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" className="ny-btn ny-btn-primary" disabled={status.kind === "busy"}>{status.kind === "busy" ? "Sending…" : "Submit review"}</button>
            <span className="text-xs text-[var(--ny-text-muted)]">Reviews are checked by a moderator before they appear.</span>
          </div>
        </form>
      )) : (
        <p className="mt-4 text-sm"><Link to="/login" className="font-semibold text-[var(--ny-green)] underline">Log in</Link> to write a review.</p>
      )}
      {status.message && <p role="status" className={`mt-2 text-sm ${status.kind === "error" ? "text-rose-700" : "text-emerald-700"}`}>{status.message}</p>}
    </section>
  )
}

export default function DestinationInsights({ destination }) {
  const key = destination?.slug || destination?.id
  if (!key) return null
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <WhenToGo destinationKey={key} />
      <TravellerSentiment destinationKey={key} />
      {destination.id ? <Reviews destination={destination} /> : null}
    </div>
  )
}
