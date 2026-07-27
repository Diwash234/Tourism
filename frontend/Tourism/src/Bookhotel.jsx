import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { FiCalendar } from "react-icons/fi"
import bookingApi from "../api/bookingApi"
import useToast from "../hooks/useToast"

/**
 * Route this at e.g. /hotels/:hotelId/book — pass hotelId from wherever
 * the hotel is shown (destination detail page's hotel list, etc.).
 */
const BookHotel = () => {
  const { hotelId } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    try {
      await bookingApi.createBooking({
        hotel: hotelId,
        check_in: data.checkIn,
        check_out: data.checkOut,
        guests: Number(data.guests),
        special_requests: data.specialRequests,
      })
      showToast("Booking requested! Check My Bookings for status.", "success")
      navigate("/my-bookings")
    } catch (err) {
      showToast(err.response?.data?.non_field_errors?.[0] || "Could not create booking", "error")
    }
  }

  return (
    <div className="container-app py-10 max-w-lg">
      <h1 className="section-title flex items-center gap-2">
        <FiCalendar className="text-primary-500" /> Book This Hotel
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-4 mt-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500">Check-in</label>
            <input type="date" className="input-field mt-1" {...register("checkIn", { required: true })} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Check-out</label>
            <input type="date" className="input-field mt-1" {...register("checkOut", { required: true })} />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500">Guests</label>
          <input type="number" min={1} defaultValue={1} className="input-field mt-1" {...register("guests", { required: true })} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500">Special requests (optional)</label>
          <textarea className="input-field mt-1" {...register("specialRequests")} />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
          {isSubmitting ? "Booking..." : "Request Booking"}
        </button>
      </form>
    </div>
  )
}

export default BookHotel