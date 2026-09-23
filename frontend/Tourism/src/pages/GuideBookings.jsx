import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiCalendar, FiStar, FiX } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import useToast from "../hooks/useToast"
import workforceApi from "../api/workforceApi"

const STATUS_STYLE = {
  requested: "bg-sky-100 text-sky-700",
  accepted: "bg-emerald-100 text-emerald-700",
  declined: "bg-rose-100 text-rose-700",
  completed: "bg-slate-200 text-slate-700",
  cancelled: "bg-slate-100 text-slate-400",
}

/**
 * Tourist-side guide booking tracker (workforce spec §12/§13):
 * own requests with cancel, and reviews once a trip is completed.
 */
export default function GuideBookings() {
  const { showToast } = useToast()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reviewFor, setReviewFor] = useState(null)
  const [rating, setRating] = useState(5)
  const [text, setText] = useState("")

  const load = useCallback(() => {
    setLoading(true)
    workforceApi.myBookings("tourist")
      .then(({ data: d }) => setBookings(d.results || []))
      .catch(() => setBookings([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const act = async (id, action) => {
    setBusyId(id)
    try {
      await workforceApi.bookingAction(id, action)
      showToast(`Request ${action === "cancel" ? "cancelled" : action + "ed"}`, "success")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Action failed", "error")
    } finally {
      setBusyId(null)
    }
  }

  const submitReview = async (e) => {
    e.preventDefault()
    setBusyId(reviewFor)
    try {
      await workforceApi.reviewBooking(reviewFor, { rating, review: text })
      showToast("Thanks — your review helps other travellers", "success")
      setReviewFor(null); setText(""); setRating(5)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save review", "error")
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#F7F8F5]">
      <PageHeader
        title="My Guide Requests"
        subtitle="Track booking requests to verified guides — cancel anytime before the trip, review it after."
      />
      <div className="max-w-3xl mx-auto px-4 pb-16 -mt-6 space-y-3">
        <p className="text-sm text-slate-600">
          <Link to="/guides" className="font-bold text-[#1D5146] hover:underline">← Browse verified guides</Link>
        </p>
        {bookings.map((b) => (
          <div key={b.id} className="bg-white rounded-3xl border shadow-sm p-5">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-black text-slate-900">{b.guide_name}</h3>
                  <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase ${STATUS_STYLE[b.status] || "bg-slate-100"}`}>{b.status}</span>
                </div>
                <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
                  <span className="flex items-center gap-1"><FiCalendar /> {b.start_date}{b.end_date ? ` → ${b.end_date}` : ""}</span>
                  <span>Group of {b.group_size}</span>
                </p>
                {b.message && <p className="text-xs text-slate-600 mt-1.5 italic">“{b.message}”</p>}
                {b.note && <p className="text-xs text-slate-600 mt-1 italic">Guide note: “{b.note}”</p>}
                {b.review && (
                  <p className="text-xs text-amber-600 font-bold mt-1.5">
                    You rated {b.review.rating}★{b.review.review ? ` — “${b.review.review}”` : ""}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                {["requested", "accepted"].includes(b.status) && (
                  <button onClick={() => act(b.id, "cancel")} disabled={busyId === b.id}
                    className="px-4 py-2 border border-rose-200 text-rose-600 hover:bg-rose-50 rounded-xl text-xs font-black flex items-center justify-center gap-1.5 disabled:opacity-40">
                    <FiX /> Cancel
                  </button>
                )}
                {b.status === "completed" && !b.reviewed && (
                  <button onClick={() => { setReviewFor(b.id); setRating(5); setText("") }}
                    className="px-4 py-2 bg-[#1D5146] hover:bg-[#102A2E] text-white rounded-xl text-xs font-black flex items-center justify-center gap-1.5">
                    <FiStar /> Review Trip
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {!loading && !bookings.length && (
          <div className="bg-white rounded-3xl border p-12 text-center">
            <FiCalendar className="mx-auto text-3xl text-slate-300" />
            <p className="text-slate-600 font-bold mt-2">No guide requests yet.</p>
            <p className="text-xs text-slate-400 mt-1">Find a verified guide and request a booking — guides respond within the platform.</p>
            <Link to="/guides" className="inline-block mt-4 px-5 py-2.5 bg-[#1D5146] text-white rounded-xl text-sm font-bold">Browse Guides</Link>
          </div>
        )}
      </div>

      {reviewFor && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <form onSubmit={submitReview} className="bg-white rounded-3xl p-6 w-full max-w-md space-y-3">
            <h3 className="font-black text-slate-900">Rate your trip</h3>
            <div className="flex gap-1 text-2xl" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((n) => (
                <button type="button" key={n} onClick={() => setRating(n)}
                  className={n <= rating ? "text-amber-400" : "text-slate-200"}
                  aria-label={`${n} star${n === 1 ? "" : "s"}`} aria-checked={rating === n} role="radio">★</button>
              ))}
            </div>
            <textarea rows={4} className="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"
              placeholder="What was the experience like? (optional)" value={text} onChange={(e) => setText(e.target.value)} />
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={() => setReviewFor(null)} className="flex-1 px-4 py-2.5 border rounded-xl text-sm font-bold text-slate-600">Cancel</button>
              <button disabled={busyId === reviewFor} className="flex-1 px-4 py-2.5 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-sm font-black">Submit Review</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
