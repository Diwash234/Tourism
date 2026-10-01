import { useState, useEffect } from 'react'
import { FiCalendar, FiMapPin, FiUsers, FiDollarSign, FiX } from 'react-icons/fi'
import useAuth from '../hooks/useAuth'

const BookingManagement = () => {
  const { user: _user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [cancelModal, setCancelModal] = useState(null)

  const fetchBookings = async () => {
    try {
      const response = await fetch('/api/v1/bookings/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('access')}` }
      })
      if (response.ok) {
        const data = await response.json()
        setBookings(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch bookings:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Defer the initial fetch one tick so the effect doesn't setState
    // synchronously; the initial loading state still renders the skeleton.
    const t = setTimeout(() => fetchBookings(), 0)
    return () => clearTimeout(t)
  }, [])

  const cancelBooking = async (id) => {
    try {
      const response = await fetch(`/api/v1/bookings/${id}/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'cancelled' })
      })
      if (response.ok) {
        setBookings(prev => prev.map(b => b.id === id ? { ...b, status: 'cancelled' } : b))
        setCancelModal(null)
      }
    } catch (err) {
      console.error('Failed to cancel booking:', err)
    }
  }

  const filteredBookings = bookings.filter(b => {
    if (filter !== 'all' && b.status !== filter) return false
    if (search && !b.hotel?.name?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-emerald-100 text-emerald-800',
      cancelled: 'bg-red-100 text-red-800',
      completed: 'bg-blue-100 text-blue-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">My Bookings</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex gap-2">
          {['all', 'pending', 'confirmed', 'cancelled', 'completed'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search by hotel name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
      </div>

      {/* Bookings List */}
      {filteredBookings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiCalendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No bookings found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredBookings.map(booking => (
            <div key={booking.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{booking.hotel?.name || 'Hotel'}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>
                      {booking.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-2">
                      <FiCalendar className="w-4 h-4" />
                      <span>{booking.check_in} → {booking.check_out}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FiMapPin className="w-4 h-4" />
                      <span>{booking.hotel?.destination?.name || 'N/A'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FiUsers className="w-4 h-4" />
                      <span>{booking.guests} guests</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FiDollarSign className="w-4 h-4" />
                      <span>${booking.total_price}</span>
                    </div>
                  </div>
                </div>
                {booking.status === 'pending' && (
                  <button
                    onClick={() => setCancelModal(booking)}
                    className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cancel Modal */}
      {cancelModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Cancel Booking</h3>
              <button onClick={() => setCancelModal(null)} className="text-gray-400 hover:text-gray-600">
                <FiX className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to cancel your booking at {cancelModal.hotel?.name}? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setCancelModal(null)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Keep Booking
              </button>
              <button
                onClick={() => cancelBooking(cancelModal.id)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Cancel Booking
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default BookingManagement
