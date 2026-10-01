import { useState, useEffect } from 'react'
import { FiMapPin, FiClock, FiStar, FiShoppingCart, FiFilter } from 'react-icons/fi'

const Marketplace = () => {
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('')
  const [priceFilter, setPriceFilter] = useState('')
  const [sortBy, setSortBy] = useState('popular')

  const fetchListings = async () => {
    try {
      const response = await fetch('/api/v1/marketplace/listings/?status=published')
      if (response.ok) {
        const data = await response.json()
        setListings(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch listings:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchListings()
  }, [])

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
                  <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 flex items-center gap-2">
                    <FiShoppingCart className="w-4 h-4" />
                    Book Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Marketplace
