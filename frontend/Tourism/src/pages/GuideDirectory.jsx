import { useState, useEffect } from 'react'
import { FiMapPin, FiStar, FiClock, FiSearch, FiFilter } from 'react-icons/fi'

const GuideDirectory = () => {
  const [guides, setGuides] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [languageFilter, setLanguageFilter] = useState('')
  const [specializationFilter, setSpecializationFilter] = useState('')
  const [sortBy, setSortBy] = useState('rating')

  useEffect(() => {
    fetchGuides()
  }, [])

  const fetchGuides = async () => {
    try {
      const response = await fetch('/api/v1/guides/')
      if (response.ok) {
        const data = await response.json()
        setGuides(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch guides:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredGuides = guides
    .filter(g => {
      if (search && !g.headline?.toLowerCase().includes(search.toLowerCase())) return false
      if (languageFilter && !g.languages?.includes(languageFilter)) return false
      if (specializationFilter && !g.specializations?.includes(specializationFilter)) return false
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'rating') return (b.average_rating || 0) - (a.average_rating || 0)
      if (sortBy === 'experience') return (b.years_experience || 0) - (a.years_experience || 0)
      if (sortBy === 'price') return (a.daily_rate_npr || 0) - (b.daily_rate_npr || 0)
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
      <h1 className="text-2xl font-bold mb-6">Guide Directory</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search guides..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <select
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
          value={specializationFilter}
          onChange={(e) => setSpecializationFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Specializations</option>
          <option value="trekking">Trekking</option>
          <option value="cultural">Cultural</option>
          <option value="wildlife">Wildlife</option>
          <option value="adventure">Adventure</option>
          <option value="photography">Photography</option>
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="rating">Sort by Rating</option>
          <option value="experience">Sort by Experience</option>
          <option value="price">Sort by Price</option>
        </select>
      </div>

      {/* Guide Cards */}
      {filteredGuides.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiFilter className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No guides found matching your criteria</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredGuides.map(guide => (
            <div key={guide.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow">
              <div className="h-48 bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center">
                <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center text-white text-2xl font-bold">
                  {guide.headline?.charAt(0) || 'G'}
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-lg">{guide.headline || 'Tour Guide'}</h3>
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
                  <span>{guide.average_rating || 'New'} rating</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {(guide.languages || []).slice(0, 3).map(lang => (
                    <span key={lang} className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded-full">
                      {lang}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-lg font-bold text-emerald-600">
                    NPR {guide.daily_rate_npr || '—'}/day
                  </span>
                  <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">
                    Book Guide
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

export default GuideDirectory
