import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiMapPin, FiClock, FiDollarSign, FiBriefcase, FiSearch, FiAlertCircle, FiX } from 'react-icons/fi'
import workforceApi from '../api/workforceApi'
import useAuth from '../hooks/useAuth'
import useToast from '../hooks/useToast'

/**
 * Tourism job board.
 *
 * Previously inert: it read `/api/v1/jobs/` and posted to
 * `/api/v1/jobs/apply/`, neither of which exists (the real routes are
 * /workforce/jobs/ and /workforce/job-applications/), so the list never
 * loaded and applications went nowhere. On top of that the cover-letter
 * textarea and CV input were uncontrolled and their values were discarded —
 * a hardcoded sentence was posted instead.
 *
 * Both now go through workforceApi, and the form's own values are sent.
 */

const ROLE_OPTIONS = [
  ['', 'All Roles'],
  ['guide', 'Tour Guide'],
  ['trek_assistant', 'Trek Assistant'],
  ['photographer', 'Photographer'],
  ['translator', 'Translator'],
  ['content_creator', 'Content Creator'],
]

const TYPE_OPTIONS = [
  ['', 'All Types'],
  ['full_time', 'Full Time'],
  ['part_time', 'Part Time'],
  ['seasonal', 'Seasonal'],
  ['contract', 'Contract'],
]

const JobBoard = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [applyModal, setApplyModal] = useState(null)
  const [application, setApplication] = useState({ cover_letter: '', experience_summary: '', cv_url: '', portfolio_url: '', availability: '' })
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)
  const [applyError, setApplyError] = useState('')

  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const load = useCallback(() => {
    setLoading(true)
    setLoadError('')
    workforceApi.jobs({
      q: search.trim() || undefined,
      role_type: roleFilter || undefined,
      employment_type: typeFilter || undefined,
    })
      .then(({ data }) => setJobs(Array.isArray(data?.results) ? data.results : []))
      .catch(() => {
        setJobs([])
        setLoadError('Job listings could not be loaded right now.')
      })
      .finally(() => setLoading(false))
  }, [search, roleFilter, typeFilter])

  useEffect(() => {
    const t = setTimeout(load, 250)
    return () => clearTimeout(t)
  }, [load])

  const openApply = (job) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/job-board' } })
      return
    }
    setApplyError('')
    setApplied(false)
    setApplication({ cover_letter: '', experience_summary: '', cv_url: '', portfolio_url: '', availability: '' })
    setApplyModal(job)
  }

  const handleApply = async (jobId) => {
    setApplying(true)
    setApplyError('')
    try {
      await workforceApi.applyToJob({
        job: jobId,
        cover_letter: application.cover_letter.trim(),
        experience_summary: application.experience_summary.trim(),
        cv_url: application.cv_url.trim(),
        portfolio_url: application.portfolio_url.trim(),
        availability: application.availability.trim(),
      })
      setApplied(true)
      showToast('Application submitted', 'success')
    } catch (error) {
      const detail = error?.response?.data?.detail || 'We could not submit your application. Please try again.'
      setApplyError(detail)
      showToast(detail, 'error')
    } finally {
      setApplying(false)
    }
  }

  const field = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600'

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
            aria-label="Search jobs"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
        <select
          aria-label="Filter by role"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          {ROLE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select
          aria-label="Filter by employment type"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          {TYPE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
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
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FiBriefcase className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No jobs found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map(job => (
            <div key={job.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    <h3 className="text-lg font-semibold">{job.title}</h3>
                    <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded-full">
                      {job.role_type_label || job.role_type}
                    </span>
                    {job.application_deadline && (
                      <span className="text-xs text-gray-500">
                        Apply by {new Date(job.application_deadline).toLocaleDateString('en-GB')}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 whitespace-pre-line">{job.description}</p>
                  {job.requirements && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 whitespace-pre-line">
                      <span className="font-semibold">Requirements: </span>{job.requirements}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <FiMapPin className="w-4 h-4" />
                      <span>{job.city || 'Nepal'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FiClock className="w-4 h-4" />
                      <span>{job.employment_type_label || job.employment_type}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FiDollarSign className="w-4 h-4" />
                      <span>{job.compensation || 'Competitive'}</span>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => openApply(job)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 shrink-0"
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            {applied ? (
              <div className="text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiBriefcase className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-emerald-600">Application Submitted!</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  We will notify you when the employer responds.
                </p>
                <button
                  type="button"
                  onClick={() => { setApplyModal(null); setApplied(false) }}
                  className="mt-6 px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                >
                  Close
                </button>
              </div>
            ) : (
              <>
                <div className="flex items-start justify-between gap-4">
                  <h3 className="text-lg font-semibold">Apply for {applyModal.title}</h3>
                  <button type="button" onClick={() => setApplyModal(null)} aria-label="Close" className="text-gray-400 hover:text-gray-700">
                    <FiX />
                  </button>
                </div>
                <div className="space-y-4 mt-4">
                  <div>
                    <label htmlFor="jb-cover" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cover Letter</label>
                    <textarea
                      id="jb-cover"
                      rows={4}
                      required
                      value={application.cover_letter}
                      onChange={(e) => setApplication({ ...application, cover_letter: e.target.value })}
                      placeholder="Tell us why you are a good fit..."
                      className={field}
                    />
                  </div>
                  <div>
                    <label htmlFor="jb-exp" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Experience summary</label>
                    <textarea
                      id="jb-exp"
                      rows={3}
                      value={application.experience_summary}
                      onChange={(e) => setApplication({ ...application, experience_summary: e.target.value })}
                      placeholder="Relevant guiding / trekking / hospitality experience"
                      className={field}
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label htmlFor="jb-cv" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CV/Resume URL</label>
                      <input
                        id="jb-cv"
                        type="url"
                        value={application.cv_url}
                        onChange={(e) => setApplication({ ...application, cv_url: e.target.value })}
                        placeholder="https://..."
                        className={field}
                      />
                    </div>
                    <div>
                      <label htmlFor="jb-port" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Portfolio URL</label>
                      <input
                        id="jb-port"
                        type="url"
                        value={application.portfolio_url}
                        onChange={(e) => setApplication({ ...application, portfolio_url: e.target.value })}
                        placeholder="https://..."
                        className={field}
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="jb-avail" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Availability</label>
                    <input
                      id="jb-avail"
                      value={application.availability}
                      onChange={(e) => setApplication({ ...application, availability: e.target.value })}
                      placeholder="e.g. Available from March to October"
                      className={field}
                    />
                  </div>
                </div>
                {applyError && (
                  <div role="alert" className="mt-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                    <FiAlertCircle className="mt-0.5 shrink-0" />
                    <span>{applyError}</span>
                  </div>
                )}
                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setApplyModal(null)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={applying || !application.cover_letter.trim()}
                    onClick={() => handleApply(applyModal.id)}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {applying ? 'Submitting…' : 'Submit Application'}
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