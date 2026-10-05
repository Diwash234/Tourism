import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiMapPin, FiStar, FiClock, FiSearch, FiFilter, FiAlertCircle, FiX } from 'react-icons/fi'
import workforceApi from '../api/workforceApi'
import useAuth from '../hooks/useAuth'
import useToast from '../hooks/useToast'

/**
 * Guide directory.
 *
 * This page used to be completely inert: it fetched `/api/v1/guides/`, which
 * does not exist (the real route is /workforce/guides/), so `guides` always
 * stayed empty, and its "Book Guide" button had no handler at all. It now uses
 * the shared workforceApi client, filters server-side, and posts a real
 * booking request through POST /workforce/guide-bookings/.
 */

const asList = (value) => {
  if (Array.isArray(value)) return value.map((v) => String(v))
  if (typeof value === 'string' && value.trim()) return value.split(',').map((v) => v.trim()).filter(Boolean)
  return []
}

const GuideDirectory = () => {
  const [guides, setGuides] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [search, setSearch] = useState('')
  const [languageFilter, setLanguageFilter] = useState('')
  const [regionFilter, setRegionFilter] = useState('')
  const [sortBy, setSortBy] = useState('rating')
  const [booking, setBooking] = useState(null)
  const [form, setForm] = useState({ start_date: '', end_date: '', group_size: 2, message: '' })
  const [busy, setBusy] = useState(false)

  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const load = useCallback(() => {
    setLoading(true)
    setLoadError('')
    workforceApi.guides({
      q: search.trim() || undefined,
      language: languageFilter || undefined,
      region: regionFilter || undefined,
    })
      .then(({ data }) => setGuides(Array.isArray(data?.results) ? data.results : []))
      .catch(() => {
        setGuides([])
        setLoadError('Guide listings could not be loaded right now.')
      })
      .finally(() => setLoading(false))
  }, [search, languageFilter, regionFilter])

  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [load])

  const sortedGuides = [...guides].sort((a, b) => {
    if (sortBy === 'rating') return (b.rating_avg || 0) - (a.rating_avg || 0)
    if (sortBy === 'experience') return (b.years_experience || 0) - (a.years_experience || 0)
    if (sortBy === 'price') return (Number(a.daily_rate_npr) || Infinity) - (Number(b.daily_rate_npr) || Infinity)
    return 0
  })

  const openBooking = (guide) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/guide-directory' } })
      return
    }
    setBooking(guide)
  }

  const submitBooking = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await workforceApi.createBooking({
        guide_id: booking.id,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        group_size: Number(form.group_size) || 1,
        message: form.message,
      })
      showToast('Booking request sent to the guide', 'success')
      setBooking(null)
      setForm({ start_date: '', end_date: '', group_size: 2, message: '' })
    } catch (error) {
      showToast(error?.response?.data?.detail || 'Could not send your request', 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Guide Directory</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search guides..."
            aria-label="Search guides"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <select
          aria-label="Filter by language"
          value={languageFilter}
          onChange={(e) => setLanguageFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Languages</option>
          <option value="English">English</option>
          <option value="Nepali">Nepali</option>
          <option value="Hindi">Hindi</option>
          <option value="Japanese">Japanese</option>
          <option value="Chinese">Chinese</option>
          <option value="French">French</option>
          <option value="German">German</option>
        </select>
        <select
          aria-label="Filter by region"
          value={regionFilter}
          onChange={(e) => setRegionFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Regions</option>
          <option value="Koshi">Koshi</option>
          <option value="Madhesh">Madhesh</option>
          <option value="Bagmati">Bagmati</option>
          <option value="Gandaki">Gandaki</option>
          <option value="Lumbini">Lumbini</option>
          <option value="Karnali">Karnali</option>
          <option value="Sudurpashchim">Sudurpashchim</option>
        </select>
        <select
          aria-label="Sort guides"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="rating">Sort by Rating</option>
          <option value="experience">Sort by Experience</option>
          <option value="price">Sort by Price</option>
        </select>
      </div>

      {loadError && (
        <div role="alert" className="mb-6 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <FiAlertCircle />
          <span>{loadError}</span>
          <button type="button" onClick={load} className="ml-auto font-semibold underline">Try again</button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
        </div>
      ) : sortedGuides.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiFilter className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No guides found matching your criteria</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedGuides.map(guide => (
            <div key={guide.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="h-48 bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center">
                <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center text-white text-2xl font-bold">
                  {(guide.name || guide.headline || 'G').charAt(0)}
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-lg">{guide.headline || guide.name || 'Tour Guide'}</h3>
                <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
                  <FiMapPin className="w-4 h-4" />
                  <span>{guide.base_city || 'Nepal'}</span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                  <FiClock className="w-4 h-4" />
                  <span>{guide.years_experience || 0} years experience</span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                  <FiStar className="w-4 h-4 text-yellow-500" />
                  <span>
                    {guide.rating_avg
                      ? `${guide.rating_avg} (${guide.review_count} review${guide.review_count === 1 ? '' : 's'})`
                      : 'No reviews yet'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {asList(guide.languages).slice(0, 3).map(lang => (
                    <span key={lang} className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded-full">
                      {lang}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-lg font-bold text-emerald-600">
                    {guide.daily_rate_npr ? `NPR ${Number(guide.daily_rate_npr).toLocaleString('en-NP')}/day` : 'Rate on request'}
                  </span>
                  <button
                    type="button"
                    onClick={() => openBooking(guide)}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                  >
                    Book Guide
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {booking && (
        <div className="fixed inset-0 z-[80] bg-black/70 grid place-items-center p-4">
          <form onSubmit={submitBooking} className="w-full max-w-lg bg-white dark:bg-gray-900 rounded-2xl p-6 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold">Request {booking.headline || booking.name}</h3>
                <p className="text-sm text-gray-500">{booking.base_city || 'Nepal'}</p>
              </div>
              <button type="button" onClick={() => setBooking(null)} aria-label="Close" className="text-gray-400 hover:text-gray-700">
                <FiX />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm">
                Start date
                <input
                  type="date"
                  required
                  value={form.start_date}
                  onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </label>
              <label className="text-sm">
                End date
                <input
                  type="date"
                  required
                  value={form.end_date}
                  onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </label>
            </div>
            <label className="block text-sm">
              Group size
              <input
                type="number"
                min={1}
                max={40}
                value={form.group_size}
                onChange={(e) => setForm({ ...form, group_size: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </label>
            <label className="block text-sm">
              Message to the guide
              <textarea
                rows={3}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                placeholder="Treks we are planning, dates, languages needed…"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </label>
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" onClick={() => setBooking(null)} className="px-4 py-2 border rounded-lg text-sm font-medium">Cancel</button>
              <button type="submit" disabled={busy} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50">
                {busy ? 'Sending…' : 'Send request'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default GuideDirectory