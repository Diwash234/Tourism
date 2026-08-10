import { FiStar, FiUser, FiSend } from "react-icons/fi"
import { useState } from "react"

export default function ReviewSection({ reviews = [], onAddReview }) {
  const [comment, setComment] = useState("")
  const [rating, setRating] = useState(5)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!comment.trim()) return
    onAddReview?.({ comment, rating })
    setComment("")
  }

  return (
    <div className="card-base p-6 sm:p-8 space-y-6 shadow-lg border border-purple-100 rounded-3xl">
      <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
        <FiStar className="text-amber-500 fill-amber-500" /> Traveler Reviews & Ratings ({reviews.length})
      </h3>

      <form onSubmit={handleSubmit} className="p-4 rounded-2xl bg-purple-50 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-700">Rating:</span>
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              className={`p-1 ${rating >= star ? "text-amber-500 fill-amber-500" : "text-gray-300"}`}
            >
              ★
            </button>
          ))}
        </div>
        <textarea
          rows={2}
          placeholder="Share your travel experience..."
          className="input-field text-xs"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <button type="submit" className="btn-primary px-4 py-2 text-xs font-bold bg-purple-700 hover:bg-purple-800 text-white rounded-xl">
          Post Review
        </button>
      </form>

      <div className="space-y-3">
        {reviews.map((r, i) => (
          <div key={i} className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-gray-800">{r.user_name || "Traveler"}</span>
              <span className="text-amber-500">{"★".repeat(r.rating || 5)}</span>
            </div>
            <p className="text-gray-600">{r.comment}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
