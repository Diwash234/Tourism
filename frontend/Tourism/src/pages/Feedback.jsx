import { useRef, useState } from 'react'
import { FiStar, FiUpload, FiCheck, FiAlertCircle } from 'react-icons/fi'
import axiosClient from '../api/axiosClient'

/**
 * Public feedback form.
 *
 * This used to be a dead button: handleSubmit only flipped local state and
 * showed "Your feedback has been submitted successfully" while throwing the
 * data away. It now POSTs to PublicFeedbackCreateView (POST /feedback/), which
 * requires `subject` and `message` and stores category/rating/evidence.
 */
const CATEGORIES = [
  { value: 'general', label: 'General' },
  { value: 'recommendation', label: 'Recommendation Quality' },
  { value: 'itinerary', label: 'Itinerary Quality' },
  { value: 'budget', label: 'Budget Accuracy' },
  { value: 'route', label: 'Route Quality' },
  { value: 'bug', label: 'Bug Report' },
]

const MAX_FILES = 8

const Feedback = () => {
  const [rating, setRating] = useState(0)
  const [hoverRating, setHoverRating] = useState(0)
  const [category, setCategory] = useState('general')
  const [subject, setSubject] = useState('')
  const [feedback, setFeedback] = useState('')
  const [files, setFiles] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const fileInput = useRef(null)

  const reset = () => {
    setRating(0)
    setCategory('general')
    setSubject('')
    setFeedback('')
    setFiles([])
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      // Multipart so the optional screenshots travel with the message.
      const body = new FormData()
      body.append('subject', subject.trim() || categoryLabel(category))
      body.append('message', feedback.trim())
      body.append('category', category)
      if (rating) body.append('rating', String(rating))
      files.forEach((f) => body.append('evidence', f))
      await axiosClient.post('/feedback/', body, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSubmitted(true)
      reset()
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(
        detail ||
          (err?.response
            ? 'We could not send that just now. Please try again.'
            : 'Network problem — your feedback was not sent. Please try again.')
      )
    } finally {
      setSubmitting(false)
    }
  }

  const addFiles = (list) => {
    const incoming = Array.from(list || []).slice(0, MAX_FILES)
    setFiles((prev) => [...prev, ...incoming].slice(0, MAX_FILES))
    if (fileInput.current) fileInput.current.value = ''
  }

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiCheck className="w-8 h-8 text-emerald-600" />
          </div>
          <h3 className="text-lg font-semibold text-emerald-600">Thank You!</h3>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Your feedback has been sent to our team.</p>
          <button
            type="button"
            onClick={() => setSubmitted(false)}
            className="mt-6 px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
          >
            Send more feedback
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Share Your Feedback</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Rating */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Overall Rating <span className="text-sm font-normal text-gray-500">(optional)</span></h2>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(star => (
              <button
                key={star}
                type="button"
                aria-label={`${star} star${star > 1 ? 's' : ''}`}
                aria-pressed={rating === star}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-1"
              >
                <FiStar
                  className={`w-8 h-8 ${
                    star <= (hoverRating || rating)
                      ? 'text-yellow-400 fill-yellow-400'
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Category */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Category</h2>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map(cat => (
              <button
                key={cat.value}
                type="button"
                onClick={() => setCategory(cat.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  category === cat.value
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Subject */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Subject</h2>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            maxLength={200}
            placeholder="Short summary — e.g. Budget estimate was too low for Annapurna"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
          />
        </div>

        {/* Feedback */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Your Feedback</h2>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={5}
            placeholder="Tell us what you think..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-100"
            required
          />
        </div>

        {/* Upload */}
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Attachments (Optional)</h2>
          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
            <FiUpload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-gray-500">Screenshots help us fix things faster</p>
            <p className="text-xs text-gray-400 mt-1">Up to {MAX_FILES} images or videos</p>
            <input
              ref={fileInput}
              type="file"
              multiple
              accept="image/*,video/*"
              className="sr-only"
              id="feedback-evidence"
              onChange={(e) => addFiles(e.target.files)}
            />
            <label
              htmlFor="feedback-evidence"
              className="mt-4 inline-block px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium cursor-pointer"
            >
              Choose files
            </label>
            {files.length > 0 && (
              <ul className="mt-4 space-y-2 text-left">
                {files.map((f, i) => (
                  <li key={`${f.name}-${i}`} className="flex items-center justify-between gap-3 text-sm">
                    <span className="truncate text-gray-600 dark:text-gray-300">{f.name}</span>
                    <button
                      type="button"
                      onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                      className="text-rose-600 hover:underline shrink-0"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <FiAlertCircle className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !feedback.trim()}
          className="w-full px-6 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50"
        >
          {submitting ? 'Sending…' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  )
}

const categoryLabel = (value) =>
  (CATEGORIES.find((c) => c.value === value) || {}).label || 'General'

export default Feedback