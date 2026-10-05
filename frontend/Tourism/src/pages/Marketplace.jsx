import { useCallback, useEffect, useState } from 'react'
import { FiMapPin, FiClock, FiStar, FiShoppingCart, FiAlertCircle, FiX } from 'react-icons/fi'
import userApi from '../api/userApi'
import useToast from '../hooks/useToast'

/**
 * Public marketplace.
 *
 * The "Book Now" button had no handler at all — it rendered on every card and
 * did nothing. It now opens a request form and posts a real basket to
 * POST /marketplace/checkout/ (request-to-book; no card data is ever sent,
 * which the backend also enforces).
 */

const Marketplace = () => {
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [priceFilter, setPriceFilter] = useState('')
  const [sortBy, setSortBy] = useState('popular')
  const [checkout, setCheckout] = useState(null)
  const [guest, setGuest] = useState({ guest_name: '', guest_email: '', guest_phone: '', travelers: 1, start_date: '', notes: '' })
  const [busy, setBusy] = useState(false)
  const [checkoutError, setCheckoutError] = useState('')
  const [reference, setReference] = useState('')
  const { showToast } = useToast()

  const fetchListings = useCallback(() => {
    setLoading(true)
    setLoadError('')
    userApi.getMarketplaceListings({ status: 'published' })
      .then(({ data }) => setListings(Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []))
      .catch(() => {
        setListings([])
        setLoadError('Marketplace listings could not be loaded right now.')
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const t = setTimeout(fetchListings, 0)
    return () => clearTimeout(t)
  }, [fetchListings])

  const filteredListings = listings
    .filter(l => {
      if (typeFilter && l.kind !== typeFilter) return false
      if (priceFilter) {
        const price = l.price_npr || 0
        if (priceFilter === 'budget' && price > 10000) return false
        if (priceFilter === 'mid' && (price < 10000 || price > 50000)) return false
        if (priceFilter === 'premium' && price < 50000) return false
      }
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'price_low') return (a.price_npr || 0) - (b.price_npr || 0)
      if (sortBy === 'price_high') return (b.price_npr || 0) - (a.price_npr || 0)
      if (sortBy === 'rating') return (b.average_rating || 0) - (a.average_rating || 0)
      return 0
    })

  const openCheckout = (listing) => {
    setCheckout(listing)
    setCheckoutError('')
    setReference('')
    setGuest({ guest_name: '', guest_email: '', guest_phone: '', travelers: 1, start_date: '', notes: '' })
  }

  const submitCheckout = async (e) => {
    e.preventDefault()
    setBusy(true)
    setCheckoutError('')
    try {
      const { data } = await userApi.checkoutMarketplace({
        guest_name: guest.guest_name.trim(),
        guest_email: guest.guest_email.trim(),
        guest_phone: guest.guest_phone.trim(),
        travelers: Number(guest.travelers) || 1,
        start_date: guest.start_date || null,
        notes: guest.notes.trim(),
        payment_method: 'request',
        items: [{ listing_id: checkout.id, quantity: 1, travel_date: guest.start_date || null }],
      })
      setReference(data?.reference || data?.order?.reference || '')
      showToast('Booking request sent', 'success')
    } catch (error) {
      setCheckoutError(error?.response?.data?.detail || 'We could not send your request. Please try again.')
    } finally {
      setBusy(false)
    }
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
      <h1 className="text-2xl font-bold mb-6">Marketplace</h1>

      {loadError && (
        <div role="alert" className="mb-6 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <FiAlertCircle />
          <span>{loadError}</span>
          <button type="button" onClick={fetchListings} className="ml-auto font-semibold underline">Try again</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Types</option>
          <option value="package">Travel Packages</option>
          <option value="tour">Tours</option>
          <option value="activity">Activities</option>
          <option value="transfer">Transfers</option>
          <option value="hotel">Hotels</option>
        </select>
        <select
          value={priceFilter}
          onChange={(e) => setPriceFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Any Price</option>
          <option value="budget">Budget (under NPR 10,000)</option>
          <option value="mid">Mid-range (NPR 10,000-50,000)</option>
          <option value="premium">Premium (NPR 50,000+)</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="popular">Most Popular</option>
          <option value="price_low">Price: Low to High</option>
          <option value="price_high">Price: High to Low</option>
          <option value="rating">Highest Rated</option>
        </select>
      </div>

      {/* Listings */}
      {filteredListings.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiShoppingCart className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No listings found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredListings.map(listing => (
            <div key={listing.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="h-48 bg-gradient-to-br from-purple-400 to-indigo-600 flex items-center justify-center">
                <FiMapPin className="w-12 h-12 text-white/50" />
              </div>
              <div className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full capitalize">
                    {listing.kind}
                  </span>
                  {listing.is_featured && (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                      Featured
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-lg">{listing.title}</h3>
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{listing.summary}</p>
                <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <FiClock className="w-4 h-4" />
                    <span>{listing.duration_days} days</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <FiStar className="w-4 h-4 text-yellow-500" />
                    <span>{listing.average_rating || 'New'}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-lg font-bold text-emerald-600">
                    NPR {listing.price_npr?.toLocaleString()}
                  </span>
                  <button type="button" onClick={() => openCheckout(listing)} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 flex items-center gap-2">
                    <FiShoppingCart className="w-4 h-4" />
                    Book Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {checkout && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            {reference ? (
              <div className="text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiShoppingCart className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-emerald-600">Request received</h3>
                {reference && (
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Your reference is <span className="font-mono font-semibold">{reference}</span>. The partner will
                    confirm by email — nothing has been charged.
                  </p>
                )}
                <button
                  type="button"
                  onClick={() => setCheckout(null)}
                  className="mt-6 px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={submitCheckout}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-semibold">Request this offer</h3>
                    <p className="text-sm text-gray-500">{checkout.title}</p>
                  </div>
                  <button type="button" onClick={() => setCheckout(null)} aria-label="Close" className="text-gray-400 hover:text-gray-700">
                    <FiX />
                  </button>
                </div>
                <div className="space-y-3 mt-4">
                  <label className="block text-sm">
                    Your name
                    <input
                      type="text"
                      required
                      value={guest.guest_name}
                      onChange={(e) => setGuest({ ...guest, guest_name: e.target.value })}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                    />
                  </label>
                  <label className="block text-sm">
                    Email
                    <input
                      type="email"
                      required
                      value={guest.guest_email}
                      onChange={(e) => setGuest({ ...guest, guest_email: e.target.value })}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                    />
                  </label>
                  <label className="block text-sm">
                    Phone (optional)
                    <input
                      type="tel"
                      value={guest.guest_phone}
                      onChange={(e) => setGuest({ ...guest, guest_phone: e.target.value })}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                    />
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="block text-sm">
                      Start date
                      <input
                        type="date"
                        value={guest.start_date}
                        onChange={(e) => setGuest({ ...guest, start_date: e.target.value })}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                      />
                    </label>
                    <label className="block text-sm">
                      Travelers
                      <input
                        type="number"
                        min={1}
                        max={20}
                        value={guest.travelers}
                        onChange={(e) => setGuest({ ...guest, travelers: e.target.value })}
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                      />
                    </label>
                  </div>
                  <label className="block text-sm">
                    Notes for the partner
                    <textarea
                      rows={3}
                      value={guest.notes}
                      onChange={(e) => setGuest({ ...guest, notes: e.target.value })}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-800 dark:text-gray-100"
                    />
                  </label>
                  <p className="text-xs text-gray-500">Request-to-book only — we never ask for card details here.</p>
                </div>
                {checkoutError && (
                  <div role="alert" className="mt-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                    <FiAlertCircle className="mt-0.5 shrink-0" />
                    <span>{checkoutError}</span>
                  </div>
                )}
                <div className="flex gap-3 mt-6">
                  <button type="button" onClick={() => setCheckout(null)} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg">
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={busy || !guest.guest_name.trim() || !guest.guest_email.trim()}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {busy ? 'Sending…' : 'Send request'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Marketplace
