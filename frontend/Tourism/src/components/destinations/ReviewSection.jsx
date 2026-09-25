import { FiStar, FiUser, FiSend, FiCheckCircle } from "react-icons/fi"
import { useState } from "react"

export default function ReviewSection({ reviews = [], onAddReview }) {
  const [comment, setComment] = useState("")
  const [rating, setRating] = useState(0)

  const activeReviews = Array.isArray(reviews) ? reviews : []

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!comment.trim() || !rating) return
    onAddReview?.({ comment, rating, user_name: "You (Traveler)" })
    setComment("")
  }

  return (
    <div className="card-base p-6 sm:p-8 space-y-6 shadow-lg border border-[#E5E0D5] rounded-3xl bg-white">
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase tracking-wider">
            Published traveller reviews
          </span>
          <h3 className="font-extrabold text-xl text-gray-900 mt-1 flex items-center gap-2">
            <FiStar className="text-amber-500 fill-amber-500" /> Traveler Reviews & Ratings ({activeReviews.length})
          </h3>
        </div>
        <span className="text-xs text-slate-500 font-bold flex items-center gap-1">
          <FiCheckCircle className="text-emerald-600" /> Published records only
        </span>
      </div>

      <form onSubmit={handleSubmit} className="p-4 rounded-2xl bg-[#F7F8F5]/60 border border-[#E5E0D5] space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-gray-700">Your Rating:</span>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              aria-label={`Rate ${star} out of 5`}
              onClick={() => setRating(star)}
              className={`p-1 text-sm ${rating >= star ? "text-amber-500 fill-amber-500 font-bold" : "text-gray-300"}`}
            >
              ★
            </button>
          ))}
          <span className="text-xs font-bold text-amber-700 ml-2">{rating ? `${rating} / 5 Stars` : "Select a rating"}</span>
        </div>
        <textarea
          aria-label="Your review"
          rows={3}
          placeholder="Share your travel experience, trail conditions, or local tips for fellow travelers..."
          className="input-field text-xs bg-white"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <div className="flex justify-end">
          <button type="submit" className="btn-primary px-5 py-2 text-xs font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow">
            Post Traveler Review
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {!activeReviews.length && <p className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">No published reviews are available for this place yet.</p>}
        {activeReviews.map((r, i) => (
          <div key={r.id || i} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs space-y-1.5 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-[#102A2E] text-white font-bold flex items-center justify-center text-xs">
                  {r.user_name ? r.user_name[0] : "T"}
                </div>
                <b className="text-slate-900 text-xs">{r.user_name || "Traveler"}</b>
              </div>
              <div className="flex items-center gap-1.5">
                {r.rating != null ? <span className="text-amber-500 font-bold">{"★".repeat(Math.max(0, Math.min(5, Number(r.rating))))}</span> : <span className="text-xs text-slate-400">Rating unavailable</span>}
                <span className="text-[10px] text-slate-400">{r.date || "Recent"}</span>
              </div>
            </div>
            <p className="text-slate-700 leading-relaxed pl-9">{r.comment || r.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
