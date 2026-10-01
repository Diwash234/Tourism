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
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"

/**
 * Review moderation queue for staff/admin. Lists pending reviews with
 * approve/reject actions, status filtering, and bulk operations.
 */
const ReviewModeration = () => {
  const showToast = useToast()
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
      const { data } = await axiosClient.get("/reviews/moderation-queue/", {
        params: { status: filter, page_size: 50 },
      })
      setReviews(data?.results || data || [])
    } catch (err) {
      setError(
        err?.response?.data?.message || "Unable to load reviews. Please try again later."
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

  const actOnReview = async (reviewId, action) => {
    setActing(true)
    try {
      await axiosClient.post(`/reviews/${reviewId}/moderate/`, { action })
      setReviews((prev) => prev.filter((r) => r.id !== reviewId))
      showToast(`Review ${action === "approve" ? "approved" : "rejected"} successfully.`, "success")
    } catch (err) {
      showToast(
        err?.response?.data?.message || `Failed to ${action} review.`,
        "error"
      )
    } finally {
      setActing(false)
    }
  }

  const bulkAction = async (action) => {
    if (selected.size === 0) return
    if (!window.confirm(`Are you sure you want to ${action} ${selected.size} review(s)?`)) return
    setActing(true)
    try {
      await axiosClient.post("/reviews/bulk-moderate/", {
        ids: Array.from(selected),
        action,
      })
      setReviews((prev) => prev.filter((r) => !selected.has(r.id)))
      setSelected(new Set())
      showToast(`${selected.size} review(s) ${action}d successfully.`, "success")
    } catch (err) {
      showToast(
        err?.response?.data?.message || `Failed to ${action} reviews.`,
        "error"
      )
    } finally {
      setActing(false)
    }
  }

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    if (selected.size === reviews.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(reviews.map((r) => r.id)))
    }
  }

  const statusIcon = (status) => {
    if (status === "approved") return <FiCheckCircle size={14} className="text-green-600" />
    if (status === "rejected") return <FiX size={14} className="text-red-600" />
    return <FiClock size={14} className="text-amber-600" />
  }

  const statusBadge = (status) => {
    const colors = {
      pending: "bg-amber-100 text-amber-800",
      approved: "bg-green-100 text-green-800",
      rejected: "bg-red-100 text-red-800",
    }
    return `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${colors[status] || "bg-gray-100 text-gray-800"}`
  }

  const filters = [
    { key: "pending", label: "Pending", icon: FiClock },
    { key: "approved", label: "Approved", icon: FiCheckCircle },
    { key: "rejected", label: "Rejected", icon: FiX },
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
              onClick={() => bulkAction("reject")}
              disabled={selected.size === 0 || acting}
              className="ny-btn ny-btn-danger ny-btn-sm"
              type="button"
            >
              <FiX size={12} /> Reject
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
              key={review.id}
              className="p-4 rounded-xl border border-ny-border hover:border-ny-green/30 transition-colors"
            >
              <div className="flex items-start gap-3">
                {filter === "pending" && (
                  <input
                    type="checkbox"
                    checked={selected.has(review.id)}
                    onChange={() => toggleSelect(review.id)}
                    className="mt-1 accent-ny-green"
                    aria-label={`Select review by ${review.author_name || "user"}`}
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="flex items-center gap-1 text-sm font-semibold text-ny-text">
                      <FiUser size={12} /> {review.author_name || "Anonymous"}
                    </span>
                    <span className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <FiStar
                          key={i}
                          size={12}
                          className={i < review.rating ? "text-ny-gold fill-ny-gold" : "text-gray-300"}
                        />
                      ))}
                    </span>
                    <span className={statusBadge(review.status)}>
                      {statusIcon(review.status)} {review.status}
                    </span>
                  </div>
                  <p className="text-sm text-ny-text-secondary mb-2">{review.comment}</p>
                  <div className="flex items-center gap-3 text-xs text-ny-text-muted">
                    <span className="flex items-center gap-1">
                      <FiMapPin size={10} /> {review.destination_name || review.destination}
                    </span>
                    <span className="flex items-center gap-1">
                      <FiClock size={10} /> {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                {filter === "pending" && (
                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => actOnReview(review.id, "approve")}
                      disabled={acting}
                      className="ny-btn ny-btn-primary ny-btn-sm"
                      type="button"
                      aria-label="Approve review"
                    >
                      <FiCheck size={12} />
                    </button>
                    <button
                      onClick={() => actOnReview(review.id, "reject")}
                      disabled={acting}
                      className="ny-btn ny-btn-danger ny-btn-sm"
                      type="button"
                      aria-label="Reject review"
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
