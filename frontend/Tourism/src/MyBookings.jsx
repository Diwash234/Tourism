import { useEffect, useState } from "react"
import PageHeader from "./components/common/PageHeader"
import CMSPageIntro from "./components/cms/CMSPageIntro"
import { FiCalendar, FiHome, FiStar,
  FiBriefcase,
} from "react-icons/fi"
import bookingApi from "./api/bookingApi"
import Loader from "./components/common/Loader"
import EmptyState from "./components/common/EmptyState"
import useToast from "./hooks/useToast"

const STATUS_COLORS = {
  pending: "text-yellow-600",
  confirmed: "text-green-600",
  cancelled: "text-red-500",
  completed: "text-gray-500",
}

const MyBookings = () => {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState("")
  const [reviewFormFor, setReviewFormFor] = useState(null)
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState("")
  const { showToast } = useToast()

  const load = () => {
    setLoading(true)
    setLoadError("")
    bookingApi
      .getMyBookings()
      .then(({ data }) => setBookings(data.results || data || []))
      .catch(() => { setBookings([]); setLoadError("Bookings could not be loaded right now.") })
      .finally(() => setLoading(false))
  }

  useEffect(()=>{const t=setTimeout(load,0);return()=>clearTimeout(t)}, [])

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
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="bookings" />
      <PageHeader title="My Bookings" subtitle="Your booking requests and their current status." icon={FiBriefcase} />

      {loadError && <div role="alert" className="ny-panel border-[#E9B9B9] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)]">{loadError} <button type="button" onClick={load} className="ml-2 font-semibold underline">Try again</button></div>}
       {!loadError && bookings.length ? (
        <div className="space-y-4">
          {bookings.map((b) => (
            <div key={b.id} className="card-base p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold">
                  <FiHome className="text-primary-500" />
                  {b.hotel_name || "Booking record"}
                </div>
                <span className={`text-sm font-semibold ${STATUS_COLORS[b.status] || ""}`}>
                  {(b.status || "unknown").toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-gray-500 flex items-center gap-1 mt-2">
                <FiCalendar size={14} /> {b.check_in || "Check-in unavailable"} → {b.check_out || "Check-out unavailable"} · {b.guests != null ? `${b.guests} guest(s)` : "Guest count unavailable"}
              </p>
              <p className="text-sm mt-1">
                Total: <strong>{b.total_price != null ? `${b.total_price} ${b.currency || ""}` : "Unavailable"}</strong>
              </p>

              <div className="flex gap-3 mt-3">
                {["pending", "confirmed"].includes(b.status) && (
                  <button onClick={() => handleCancel(b.id)} className="text-red-500 text-sm hover:underline">
                    Cancel booking
                  </button>
                )}
                {b.status === "completed" && b.hotel && (
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
      ) : loadError ? null : (
        <EmptyState title="No bookings yet" subtitle="Book a hotel from a destination page to see it here." />
      )}
    </div>
  )
}

export default MyBookings