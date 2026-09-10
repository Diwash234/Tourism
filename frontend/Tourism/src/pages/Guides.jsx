import { useCallback, useEffect, useState } from "react"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { Link } from "react-router-dom"
import { FiSearch, FiMapPin, FiAward, FiStar, FiRefreshCw, FiCalendar, FiMessageSquare } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import workforceApi from "../api/workforceApi"

const LANGUAGES = ["Nepali", "English", "Hindi", "Japanese", "Chinese", "French", "German", "Spanish", "Korean"]

/**
 * Public directory of VERIFIED tourism guides (workforce spec §2/§10/§12/§13).
 * Only verified, publicly-listed profiles are ever returned by the API —
 * the listing is scoped server-side, not filtered in React.
 * Reputation: rating average + reviews per guide (only from completed bookings).
 */
export default function Guides() {
  const { isAuthenticated } = useAuth() || {}
  const { showToast } = useToast()
  const [data, setData] = useState({ count: 0, results: [] })
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState("")
  const [language, setLanguage] = useState("")
  const [region, setRegion] = useState("")
  const [reviewsFor, setReviewsFor] = useState(null) // guide id whose reviews are open
  const [reviewData, setReviewData] = useState(null)
  const [booking, setBooking] = useState(null) // guide being requested
  const [form, setForm] = useState({ start_date: "", end_date: "", group_size: 2, message: "" })
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    workforceApi.guides({ q: q || undefined, language: language || undefined, region: region || undefined })
      .then(({ data: d }) => setData(d))
      .catch(() => setData({ count: 0, results: [] }))
      .finally(() => setLoading(false))
  }, [q, language, region])

  useEffect(() => {
    const t = setTimeout(() => load(), 250)
    return () => clearTimeout(t)
  }, [load])

  const toggleReviews = (id) => {
    if (reviewsFor === id) { setReviewsFor(null); setReviewData(null); return }
    setReviewsFor(id)
    setReviewData(null)
    workforceApi.guideReviews(id).then(({ data: d }) => setReviewData(d)).catch(() => setReviewData(null))
  }

  const submitBooking = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await workforceApi.createBooking({ guide_id: booking.id, ...form, group_size: Number(form.group_size) || 1 })
      showToast("Booking request sent to the guide", "success")
      setBooking(null)
      setForm({ start_date: "", end_date: "", group_size: 2, message: "" })
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not send request", "error")
    } finally {
      setBusy(false)
    }
  }

  const stars = (avg) => (
    <span className="inline-flex items-center gap-1 text-xs font-black text-amber-600" title={`${avg} average`}>
      <FiStar className="fill-amber-400 text-amber-400" /> {avg}
    </span>
  )

  const field = "w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"

  return (
    <div className="min-h-screen bg-[#F7F8F5]">
      <CMSPageIntro pageKey="guides" />
      <PageHeader
        title="Verified Local Guides"
        subtitle="Government-licensed, platform-verified guides across Nepal — trekking, cultural, wildlife and city specialists."
      />
      <div className="max-w-6xl mx-auto px-4 pb-16 -mt-6">
        <div className="bg-white rounded-3xl border shadow-sm p-4 flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search guides by name, skill or city…"
              aria-label="Search guides"
              className="w-full pl-10 pr-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"
            />
          </div>
          <select value={language} onChange={(e) => setLanguage(e.target.value)} aria-label="Filter by language" className="px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]">
            <option value="">Any language</option>
            {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
          </select>
          <input
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            placeholder="Region / district"
            aria-label="Filter by region"
            className="px-3 py-2.5 rounded-xl border text-sm w-full md:w-44 focus:outline-none focus:border-[#1D5146]"
          />
          <button onClick={load} className="px-4 py-2.5 bg-[#1D5146] text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Search
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 mt-6 mb-3">
          <p className="text-sm text-slate-600"><b>{data.count}</b> verified guide{data.count === 1 ? "" : "s"} available</p>
          <span className="flex items-center gap-4">
            {isAuthenticated && (
              <Link to="/guide-bookings" className="text-sm font-bold text-[#1D5146] hover:underline">My Guide Requests →</Link>
            )}
            <Link to="/guide-portal" className="text-sm font-bold text-[#1D5146] hover:underline">Become a guide →</Link>
          </span>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((g) => (
            <div key={g.id} className="bg-white rounded-3xl border shadow-sm p-5 flex flex-col gap-2 hover:shadow-md transition">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-black text-slate-900">{g.name}</h3>
                  <p className="text-xs text-slate-500">{g.headline || "Tourism guide"}</p>
                </div>
                <span className="text-[10px] px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 font-black flex items-center gap-1 whitespace-nowrap">
                  <FiAward /> VERIFIED
                </span>
              </div>
              <button onClick={() => toggleReviews(g.id)} className="flex items-center gap-2 text-left w-fit group" aria-expanded={reviewsFor === g.id}>
                {g.rating_avg ? stars(g.rating_avg) : <span className="text-xs text-slate-400 font-bold">New guide</span>}
                <span className="text-[11px] text-slate-400 font-bold group-hover:text-[#1D5146]">
                  {g.review_count > 0 ? `${g.review_count} review${g.review_count === 1 ? "" : "s"}` : "No reviews yet"} · {reviewsFor === g.id ? "hide" : "view"}
                </span>
              </button>
              {reviewsFor === g.id && (
                <div className="rounded-2xl bg-slate-50 border p-3 text-xs space-y-2">
                  {!reviewData && <p className="text-slate-400">Loading reviews…</p>}
                  {reviewData && reviewData.review_count === 0 && (
                    <p className="text-slate-500">No completed trips reviewed yet. Reviews appear after a completed booking.</p>
                  )}
                  {reviewData?.results?.map((r) => (
                    <div key={r.id} className="border-b last:border-0 pb-2 last:pb-0">
                      <p className="font-black text-amber-600">{"★".repeat(r.rating)}<span className="text-slate-300">{"★".repeat(5 - r.rating)}</span></p>
                      {r.review && <p className="text-slate-600 mt-0.5">{r.review}</p>}
                      <p className="text-[10px] text-slate-400 mt-0.5">{r.author || "Traveller"} · {new Date(r.created_at).toLocaleDateString()}</p>
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs text-slate-600 line-clamp-3">{g.bio || "No bio provided yet."}</p>
              <div className="text-[11px] text-slate-500 space-y-1 mt-auto">
                {g.base_city && <p className="flex items-center gap-1"><FiMapPin /> {g.base_city}</p>}
                {g.languages?.length > 0 && <p>🗣️ {g.languages.join(", ")}</p>}
                {g.specializations?.length > 0 && <p>⭐ {g.specializations.join(", ")}</p>}
                {g.years_experience > 0 && <p>📅 {g.years_experience} years experience</p>}
              </div>
              <div className="flex items-center justify-between pt-2 border-t mt-2">
                <span className="text-sm font-black text-[#1D5146]">
                  {g.daily_rate_npr ? `NPR ${Number(g.daily_rate_npr).toLocaleString()}/day` : "Rate on request"}
                </span>
                {isAuthenticated ? (
                  <button onClick={() => setBooking(g)} className="px-3 py-1.5 bg-[#1D5146] hover:bg-[#102A2E] text-white rounded-xl text-[11px] font-black flex items-center gap-1.5">
                    <FiCalendar /> Request Booking
                  </button>
                ) : (
                  <Link to="/login" className="px-3 py-1.5 bg-[#1D5146] text-white rounded-xl text-[11px] font-black">Sign in to Book</Link>
                )}
              </div>
            </div>
          ))}
        </div>

        {!loading && !data.results.length && (
          <div className="bg-white rounded-3xl border p-12 text-center mt-4">
            <FiStar className="mx-auto text-3xl text-slate-300" />
            <p className="text-slate-600 font-bold mt-2">No verified guides match this search yet.</p>
            <p className="text-xs text-slate-400 mt-1">Try removing filters — or apply to become Nepal&apos;s next verified guide.</p>
            <Link to="/guide-portal" className="inline-block mt-4 px-5 py-2.5 bg-[#1D5146] text-white rounded-xl text-sm font-bold">
              Apply as a Guide
            </Link>
          </div>
        )}
      </div>

      {booking && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <form onSubmit={submitBooking} className="bg-white rounded-3xl p-6 w-full max-w-md space-y-3">
            <h3 className="font-black text-slate-900 flex items-center gap-2"><FiMessageSquare /> Request {booking.name}</h3>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-xs font-bold text-slate-600">Start date *
                <input type="date" required className={field + " mt-1"} value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </label>
              <label className="text-xs font-bold text-slate-600">End date
                <input type="date" className={field + " mt-1"} value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
              </label>
            </div>
            <label className="block text-xs font-bold text-slate-600">Group size
              <input type="number" min="1" max="200" className={field + " mt-1"} value={form.group_size} onChange={(e) => setForm({ ...form, group_size: e.target.value })} />
            </label>
            <textarea rows={3} className={field} placeholder="Tell the guide about your trip (route, goals, needs)…" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={() => setBooking(null)} className="flex-1 px-4 py-2.5 border rounded-xl text-sm font-bold text-slate-600">Cancel</button>
              <button disabled={busy} className="flex-1 px-4 py-2.5 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-sm font-black">{busy ? "Sending…" : "Send Request"}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
