import { useState } from "react"
import { FiStar, FiThumbsUp, FiMessageCircle } from "react-icons/fi"
import StarRating from "../common/StarRating"
import Avatar from "../common/Avatar"
import Badge from "../common/Badge"

/**
 * Destination reviews section with rating summary,
 * review list, and write review functionality.
 */
export default function DestinationReviews({ destination, reviews = [], onSubmitReview }) {
  const [showForm, setShowForm] = useState(false)
  const [newReview, setNewReview] = useState({ rating: 0, comment: "" })

  const ratingDistribution = [5, 4, 3, 2, 1].map(star => ({
    star,
    count: reviews.filter(r => Math.round(r.rating) === star).length,
    percentage: reviews.length > 0
      ? (reviews.filter(r => Math.round(r.rating) === star).length / reviews.length) * 100
      : 0,
  }))

  const averageRating = reviews.length > 0
    ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
    : 0

  const handleSubmit = (e) => {
    e.preventDefault()
    if (newReview.rating === 0 || !newReview.comment.trim()) return
    onSubmitReview?.(newReview)
    setNewReview({ rating: 0, comment: "" })
    setShowForm(false)
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white">Reviews</h3>
        <button
          type="button"
          onClick={() => setShowForm(v => !v)}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
        >
          Write Review
        </button>
      </div>

      {/* Rating Summary */}
      <div className="flex flex-col sm:flex-row gap-6 mb-6 pb-6 border-b border-[var(--ny-border)]">
        <div className="text-center sm:text-left">
          <p className="text-4xl font-bold text-gray-900 dark:text-white">{averageRating.toFixed(1)}</p>
          <StarRating value={averageRating} size="sm" className="mt-1" />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{reviews.length} reviews</p>
        </div>
        <div className="flex-1 space-y-1.5">
          {ratingDistribution.map(({ star, count, percentage }) => (
            <div key={star} className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400 w-3">{star}</span>
              <FiStar size={12} className="text-amber-400 fill-amber-400" />
              <div className="flex-1 h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-400 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-6 text-right">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Write Review Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)]">
          <div className="mb-3">
            <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 block mb-1.5">Your Rating</label>
            <StarRating value={newReview.rating} onChange={(r) => setNewReview(prev => ({ ...prev, rating: r }))} size="lg" />
          </div>
          <div className="mb-3">
            <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 block mb-1.5">Your Review</label>
            <textarea
              value={newReview.comment}
              onChange={(e) => setNewReview(prev => ({ ...prev, comment: e.target.value }))}
              placeholder="Share your experience..."
              rows={3}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors">
              Submit Review
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-xs font-semibold rounded-lg border border-gray-300 dark:border-slate-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Review List */}
      {reviews.length === 0 ? (
        <div className="text-center py-8">
          <FiMessageCircle size={32} className="mx-auto text-gray-300 dark:text-gray-600 mb-2" />
          <p className="text-sm text-gray-500 dark:text-gray-400">No reviews yet. Be the first to review!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review, i) => (
            <div key={i} className="pb-4 border-b border-[var(--ny-border)] last:border-0 last:pb-0">
              <div className="flex items-center gap-3 mb-2">
                <Avatar name={review.user_name || review.user} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{review.user_name || review.user}</p>
                  <div className="flex items-center gap-2">
                    <StarRating value={review.rating} size="sm" />
                    <span className="text-[10px] text-gray-400">{review.date || review.created_at}</span>
                  </div>
                </div>
                {review.verified && <Badge variant="success" size="sm">Verified</Badge>}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{review.comment || review.text}</p>
              {review.helpful > 0 && (
                <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-400">
                  <FiThumbsUp size={12} />
                  <span>{review.helpful} people found this helpful</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
