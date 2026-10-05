import { useState, useEffect, useCallback } from "react"
import {
  FiCheck,
  FiX,
  FiStar,
  FiFilter,
  FiRefreshCw,
  FiAlertCircle,
  FiCheckCircle,
  FiClock,
  FiMapPin,
  FiUser,
} from "react-icons/fi"
import adminApi from "../api/adminApi"

/**
 * Review moderation queue for staff/admin. Lists pending reviews with
 * approve/reject actions, status filtering, and bulk operations.
 *
 * This used three routes that were never built (/reviews/moderation-queue/,
 * /reviews/<id>/moderate/, /reviews/bulk-moderate/), so every action here
 * 404'd. The real moderation surface is AdminReviewModerationView at
 * /admin/review-moderation/ (GET for the queue, PATCH for approve / flag /
 * archive / restore, and it is bulk-capable via `ids`).
 */
const ReviewModeration = () => {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState("pending")
  const [selected, setSelected] = useState(new Set())
  const [acting, setActing] = useState(false)

  const fetchReviews = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await adminApi.getReviewModeration({
        type: "all",
        status: filter,
        page_size: 50,
      })
      setReviews(data?.results || [])
    } catch (err) {
      setReviews([])
      setError(
        err?.response?.data?.detail || "Unable to load reviews. Please try again later."
      )
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchReviews(), 0)
    return () => clearTimeout(t)
  }, [fetchReviews])

  // Rows are tagged by `type` ("destination" | "hotel") because the two live
  // in different tables, and the API refuses an ambiguous id set.
  // Destination reviews and hotel reviews live in different tables, so a bare
  // id is ambiguous. Selection is keyed by "<type>:<id>".
  const keyOf = (review) => `${review.type}:${review.id}`

  const actOnReview = async (review, action) => {
    setActing(true)
    setError(null)
    try {
      await adminApi.moderateReviews({ type: review.type, ids: [review.id], action })
      setReviews((prev) => prev.filter((r) => keyOf(r) !== keyOf(review)))
      setSelected((prev) => {
        const next = new Set(prev)
        next.delete(keyOf(review))
        return next
      })
    } catch (err) {
      setError(err?.response?.data?.detail || `Failed to ${action} that review.`)
    } finally {
      setActing(false)
    }
  }

  const bulkAction = async (action) => {
    const rows = reviews.filter((r) => selected.has(keyOf(r)))
    if (rows.length === 0) return
    if (!window.confirm(`Are you sure you want to ${action} ${rows.length} review(s)?`)) return
    setActing(true)
    setError(null)
    try {
      // One call per type — the endpoint moderates a single `type` at a time.
      for (const type of ["destination", "hotel"]) {
        const ids = rows.filter((r) => r.type === type).map((r) => r.id)
        if (ids.length === 0) continue
        await adminApi.moderateReviews({ type, ids, action })
      }
      const done = new Set(rows.map(keyOf))
      setReviews((prev) => prev.filter((r) => !done.has(keyOf(r))))
      setSelected(new Set())
    } catch (err) {
      setError(err?.response?.data?.detail || `Failed to ${action} those reviews.`)
    } finally {
      setActing(false)
    }
  }

  const toggleSelect = (key) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const selectAll = () => {
    if (selected.size === reviews.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(reviews.map(keyOf)))
    }
  }

  const statusIcon = (status) => {
    if (status === "approved") return <FiCheckCircle size={14} className="text-green-600" />
    if (status === "flagged") return <FiAlertCircle size={14} className="text-amber-600" />
    if (status === "archived") return <FiX size={14} className="text-red-600" />
    return <FiClock size={14} className="text-amber-600" />
  }

  const statusBadge = (status) => {
    const colors = {
      pending: "bg-amber-100 text-amber-800",
      approved: "bg-green-100 text-green-800",
      flagged: "bg-orange-100 text-orange-800",
      archived: "bg-red-100 text-red-800",
    }
    return `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${colors[status] || "bg-gray-100 text-gray-800"}`
  }

  // The moderation API's states are pending / approved / flagged / archived.
  // It has no "rejected" state — rejecting a review is `archive`.
  const filters = [
    { key: "pending", label: "Pending", icon: FiClock },
    { key: "approved", label: "Approved", icon: FiCheckCircle },
    { key: "flagged", label: "Flagged", icon: FiAlertCircle },
    { key: "archived", label: "Archived", icon: FiX },
  ]

  return (
    <div className="ny-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-ny-text flex items-center gap-2">
          <FiStar size={18} className="text-ny-green" />
          Review Moderation
        </h3>
        <button
          onClick={fetchReviews}
          className="ny-btn ny-btn-ghost ny-btn-sm"
          type="button"
          aria-label="Refresh reviews"
        >
          <FiRefreshCw size={14} />
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <FiFilter size={14} className="text-ny-text-muted" />
        {filters.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilter(key)}
            className={`ny-btn ny-btn-sm ${filter === key ? "ny-btn-primary" : "ny-btn-secondary"}`}
          >
            <Icon size={12} /> {label}
          </button>
        ))}
      </div>

      {/* Bulk actions */}
      {filter === "pending" && reviews.length > 0 && (
        <div className="flex items-center gap-2 mb-4 p-3 rounded-xl bg-ny-soft-green border border-ny-border">
          <label className="flex items-center gap-2 text-sm text-ny-text cursor-pointer">
            <input
              type="checkbox"
              checked={selected.size === reviews.length}
              onChange={selectAll}
              className="accent-ny-green"
            />
            Select all
          </label>
          <span className="text-xs text-ny-text-muted">({selected.size} selected)</span>
          <div className="ml-auto flex gap-2">
            <button
              onClick={() => bulkAction("approve")}
              disabled={selected.size === 0 || acting}
              className="ny-btn ny-btn-primary ny-btn-sm"
              type="button"
            >
              <FiCheck size={12} /> Approve
            </button>
            <button
              onClick={() => bulkAction("archive")}
              disabled={selected.size === 0 || acting}
              className="ny-btn ny-btn-danger ny-btn-sm"
              type="button"
            >
              <FiX size={12} /> Archive
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="space-y-3" role="status" aria-label="Loading reviews">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-xl border border-ny-border">
              <div className="ny-skeleton h-4 w-1/4 mb-2" />
              <div className="ny-skeleton h-4 w-3/4 mb-1" />
              <div className="ny-skeleton h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-ny-soft-red border border-red-200" role="alert">
          <FiAlertCircle size={16} className="text-ny-danger" />
          <span className="text-sm text-ny-danger">{error}</span>
        </div>
      ) : reviews.length === 0 ? (
        <div className="ny-empty">
          <span className="ny-empty-icon"><FiCheckCircle size={24} /></span>
          <h3>All caught up!</h3>
          <p>No {filter} reviews to show.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reviews.map((review) => (
            <div
              key={keyOf(review)}
              className="p-4 rounded-xl border border-ny-border hover:border-ny-green/30 transition-colors"
            >
              <div className="flex items-start gap-3">
                {filter === "pending" && (
                  <input
                    type="checkbox"
                    checked={selected.has(keyOf(review))}
                    onChange={() => toggleSelect(keyOf(review))}
                    className="mt-1 accent-ny-green"
                    aria-label={`Select review by ${review.user || "user"}`}
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="flex items-center gap-1 text-sm font-semibold text-ny-text">
                      <FiUser size={12} /> {review.user || "Anonymous"}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-ny-soft-green text-ny-green text-[10px] uppercase">
                      {review.type}
                    </span>
                    {review.rating != null && (
                      <span className="flex items-center gap-0.5">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <FiStar
                            key={i}
                            size={12}
                            className={i < review.rating ? "text-ny-gold fill-ny-gold" : "text-gray-300"}
                          />
                        ))}
                      </span>
                    )}
                    <span className={statusBadge(review.status)}>
                      {statusIcon(review.status)} {review.status}
                    </span>
                  </div>
                  <p className="text-sm text-ny-text-secondary mb-2">{review.comment}</p>
                  <div className="flex items-center gap-3 text-xs text-ny-text-muted">
                    <span className="flex items-center gap-1">
                      <FiMapPin size={10} /> {review.subject || "—"}
                    </span>
                    <span className="flex items-center gap-1">
                      <FiClock size={10} /> {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                {filter === "pending" && (
                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => actOnReview(review, "approve")}
                      disabled={acting}
                      className="ny-btn ny-btn-primary ny-btn-sm"
                      type="button"
                      aria-label="Approve review"
                    >
                      <FiCheck size={12} />
                    </button>
                    <button
                      onClick={() => actOnReview(review, "archive")}
                      disabled={acting}
                      className="ny-btn ny-btn-danger ny-btn-sm"
                      type="button"
                      aria-label="Archive review"
                    >
                      <FiX size={12} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReviewModeration
