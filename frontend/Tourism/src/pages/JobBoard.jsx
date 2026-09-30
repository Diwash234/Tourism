import { useState, useEffect } from 'react'
import { FiMapPin, FiClock, FiDollarSign, FiBriefcase, FiSearch } from 'react-icons/fi'

const JobBoard = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [applyModal, setApplyModal] = useState(null)
  const [applied, setApplied] = useState(false)

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/v1/jobs/?status=open')
      if (response.ok) {
        const data = await response.json()
        setJobs(data.results || [])
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredJobs = jobs.filter(j => {
    if (search && !j.title?.toLowerCase().includes(search.toLowerCase())) return false
    if (roleFilter && j.role_type !== roleFilter) return false
    if (typeFilter && j.employment_type !== typeFilter) return false
    return true
  })

  const handleApply = async (jobId) => {
    try {
      const response = await fetch('/api/v1/jobs/apply/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ job: jobId, cover_letter: 'I am interested in this position.' })
      })
      if (response.ok) {
        setApplied(true)
        setTimeout(() => {
          setApplied(false)
          setApplyModal(null)
        }, 2000)
      }
    } catch (err) {
      console.error('Failed to apply:', err)
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
      <h1 className="text-2xl font-bold mb-6">Job Board</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px]">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Roles</option>
          <option value="guide">Tour Guide</option>
          <option value="trek_assistant">Trek Assistant</option>
          <option value="photographer">Photographer</option>
          <option value="translator">Translator</option>
          <option value="content_creator">Content Creator</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Types</option>
          <option value="full_time">Full Time</option>
          <option value="part_time">Part Time</option>
          <option value="seasonal">Seasonal</option>
          <option value="contract">Contract</option>
        </select>
      </div>

      {/* Job Listings */}
      {filteredJobs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiBriefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No jobs found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredJobs.map(job => (
            <div key={job.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{job.title}</h3>
                    <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded-full capitalize">
                      {job.role_type}
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-3">{job.description}</p>
                  <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <FiMapPin className="w-4 h-4" />
                      <span>{job.city || 'Nepal'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FiClock className="w-4 h-4" />
                      <span className="capitalize">{job.employment_type}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FiDollarSign className="w-4 h-4" />
                      <span>{job.compensation || 'Competitive'}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setApplyModal(job)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                >
                  Apply Now
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Apply Modal */}
      {applyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4">
            {applied ? (
              <div className="text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiBriefcase className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-emerald-600">Application Submitted!</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  We will notify you when the employer responds.
                </p>
              </div>
            ) : (
              <>
                <h3 className="text-lg font-semibold mb-4">Apply for {applyModal.title}</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cover Letter</label>
                    <textarea
                      rows={4}
                      placeholder="Tell us why you are a good fit..."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CV/Resume URL</label>
                    <input
                      type="url"
                      placeholder="https://..."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setApplyModal(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleApply(applyModal.id)}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
                  >
                    Submit Application
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default JobBoard
