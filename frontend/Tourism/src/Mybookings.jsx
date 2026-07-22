import { useEffect, useState } from "react"
import { FiCalendar, FiHome, FiStar } from "react-icons/fi"
import bookingApi from "../api/bookingApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"

const STATUS_COLORS = {
  pending: "text-yellow-600",
  confirmed: "text-green-600",
  cancelled: "text-red-500",
  completed: "text-gray-500",
}

const MyBookings = () => {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewFormFor, setReviewFormFor] = useState(null)
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState("")
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    bookingApi
      .getMyBookings()
      .then(({ data }) => setBookings(data.results || data || []))
      .catch(() => setBookings([]))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCancel = async (id) => {
    try {
      await bookingApi.cancelBooking(id)
      showToast("Booking cancelled", "info")
      load()
    } catch {
      showToast("Could not cancel booking", "error")
    }
  }

  const handleSubmitReview = async (hotelId) => {
    try {
      await bookingApi.addHotelReview(hotelId, rating, comment)
      showToast("Review submitted", "success")
      setReviewFormFor(null)
      setComment("")
    } catch (err) {
      showToast(err.response?.data?.hotel?.[0] || "Could not submit review", "error")
    }
  }

  if (loading) return <Loader />

  return (
    <div className="container-app py-10">
      <h1 className="section-title mb-6">My Bookings</h1>

      {bookings.length ? (
        <div className="space-y-4">
          {bookings.map((b) => (
            <div key={b.id} className="card-base p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold">
                  <FiHome className="text-primary-500" />
                  {b.hotel_name}
                </div>
                <span className={`text-sm font-semibold ${STATUS_COLORS[b.status] || ""}`}>
                  {b.status.toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-gray-500 flex items-center gap-1 mt-2">
                <FiCalendar size={14} /> {b.check_in} → {b.check_out} · {b.guests} guest(s)
              </p>
              <p className="text-sm mt-1">
                Total: <strong>{b.total_price} {b.currency}</strong>
              </p>

              <div className="flex gap-3 mt-3">
                {["pending", "confirmed"].includes(b.status) && (
                  <button onClick={() => handleCancel(b.id)} className="text-red-500 text-sm hover:underline">
                    Cancel booking
                  </button>
                )}
                {b.status === "completed" && (
                  <button
                    onClick={() => setReviewFormFor(reviewFormFor === b.id ? null : b.id)}
                    className="text-primary-500 text-sm hover:underline flex items-center gap-1"
                  >
                    <FiStar size={14} /> Leave a review
                  </button>
                )}
              </div>

              {reviewFormFor === b.id && (
                <div className="mt-3 border-t pt-3 space-y-2">
                  <select className="input-field" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
                    {[5, 4, 3, 2, 1].map((n) => (
                      <option key={n} value={n}>{n} star{n > 1 ? "s" : ""}</option>
                    ))}
                  </select>
                  <textarea
                    className="input-field"
                    placeholder="How was your stay?"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <button onClick={() => handleSubmitReview(b.hotel)} className="btn-primary">
                    Submit Review
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No bookings yet" subtitle="Book a hotel from a destination page to see it here." />
      )}
    </div>
  )
}

export default MyBookings