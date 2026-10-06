import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiPlus, FiTrash2, FiDollarSign, FiShare2, FiPrinter, FiSave, FiCopy, FiCheck, FiAlertCircle, FiX } from 'react-icons/fi'
import axiosClient from '../api/axiosClient'
import exploreApi from '../api/exploreApi'
import useAuth from '../hooks/useAuth'
import useToast from '../hooks/useToast'

/**
 * Itinerary builder.
 *
 * Previously the whole thing lived in component state and went nowhere:
 *   - "Share" opened a modal showing the literal string
 *     "https://nepalyatra.com/shared/abc123" with a Copy button that had no
 *     handler, so it copied nothing and the link pointed at nothing;
 *   - "Export PDF" had no handler at all;
 *   - there was no save, so reloading the page lost the trip.
 *
 * It now writes to TravelPlan (POST /travel-plans/), which is the same record
 * the rest of the site reads. Sharing calls the real endpoint
 * (POST /travel-plans/<id>/share/), which mints a UUID token rendered by
 * /plans/shared/<token>; revoking it with DELETE breaks every existing copy.
 * Export uses the browser's print-to-PDF, which is what the itinerary page
 * already does, so there is no fake "PDF generated" claim.
 */

const emptyDay = (n) => ({ day: n, stops: [] })

const ItineraryBuilder = () => {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [itinerary, setItinerary] = useState({
    title: 'My Nepal Trip',
    startDate: '',
    endDate: '',
    travelers: 1,
    days: [emptyDay(1)],
  })
  const [budget, setBudget] = useState({ accommodation: 0, food: 0, transport: 0, activities: 0 })
  const [planId, setPlanId] = useState(null)
  const [shareUrl, setShareUrl] = useState('')
  const [showShare, setShowShare] = useState(false)
  const [copied, setCopied] = useState(false)
  const [saving, setSaving] = useState(false)
  const [sharing, setSharing] = useState(false)
  const [error, setError] = useState('')

  const totalBudget = Object.values(budget).reduce((a, b) => a + (Number(b) || 0), 0)

  const patch = (changes) => setItinerary((prev) => ({ ...prev, ...changes }))

  const addDay = () =>
    setItinerary((prev) => ({ ...prev, days: [...prev.days, emptyDay(prev.days.length + 1)] }))

  const removeDay = (dayIndex) =>
    setItinerary((prev) =>
      prev.days.length <= 1
        ? prev
        : {
            ...prev,
            // Renumber so the visible day numbers stay contiguous after a removal.
            days: prev.days
              .filter((_, idx) => idx !== dayIndex)
              .map((d, idx) => ({ ...d, day: idx + 1 })),
          })

  const addStop = (dayIndex) =>
    setItinerary((prev) => {
      const days = prev.days.map((d, i) =>
        i === dayIndex ? { ...d, stops: [...d.stops, { key: `s${Date.now()}${d.stops.length}`, name: '', time: '', notes: '' }] } : d)
      return { ...prev, days }
    })

  const removeStop = (dayIndex, stopKey) =>
    setItinerary((prev) => ({
      ...prev,
      days: prev.days.map((d, i) =>
        i === dayIndex ? { ...d, stops: d.stops.filter((s) => s.key !== stopKey) } : d),
    }))

  const updateStop = (dayIndex, stopKey, field, value) =>
    setItinerary((prev) => ({
      ...prev,
      days: prev.days.map((d, i) =>
        i === dayIndex
          ? { ...d, stops: d.stops.map((s) => (s.key === stopKey ? { ...s, [field]: value } : s)) }
          : d),
    }))

  const requireAuth = () => {
    if (isAuthenticated) return true
    showToast('Please sign in to save and share your trip', 'warning')
    navigate('/login', { state: { from: '/itinerary-builder' } })
    return false
  }

  const save = useCallback(async () => {
    if (!requireAuth()) return
    if (itinerary.endDate && itinerary.startDate && itinerary.endDate < itinerary.startDate) {
      setError('The end date cannot be before the start date.')
      return
    }
    setSaving(true)
    setError('')
    // Stops are stored as free-form itinerary_data because TravelPlanStop
    // requires a real Destination FK; this builder accepts typed names.
    const payload = {
      title: itinerary.title.trim() || 'My Nepal Trip',
      start_date: itinerary.startDate || null,
      end_date: itinerary.endDate || null,
      travelers: Number(itinerary.travelers) || 1,
      budget_npr: totalBudget || null,
      generation_source: 'manual',
      itinerary_data: {
        budget,
        days: itinerary.days.map((d) => ({
          day: d.day,
          stops: d.stops.map((s) => ({ name: s.name, time: s.time, notes: s.notes })),
        })),
      },
    }
    try {
      const { data } = planId
        ? await axiosClient.patch(`/travel-plans/${planId}/`, payload)
        : await axiosClient.post('/travel-plans/', payload)
      setPlanId(data.id)
      // A saved plan has a new revision, so any previous link may be stale.
      if (shareUrl) setShareUrl('')
      showToast(planId ? 'Trip updated' : 'Trip saved', 'success')
    } catch (err) {
      const detail = err?.response?.data
      setError(
        (Array.isArray(detail) ? detail[0] : detail?.non_field_errors?.[0]) ||
          detail?.detail || 'We could not save your trip. Please try again.'
      )
    } finally {
      setSaving(false)
    }
  }, [itinerary, totalBudget, budget, planId, shareUrl, isAuthenticated, showToast])

  const share = useCallback(async () => {
    if (!requireAuth()) return
    if (!planId) {
      showToast('Save your trip first, then share it', 'warning')
      return
    }
    setSharing(true)
    setError('')
    try {
      const { data } = await exploreApi.sharePlan(planId)
      // The API returns the SPA path; anchor it to this origin so the link is
      // actually clickable wherever the admin happens to be browsing from.
      setShareUrl(new URL(data.path || `/plans/shared/${data.token}`, window.location.origin).toString())
      setShowShare(true)
    } catch (err) {
      setError(err?.response?.data?.detail || 'We could not create a share link.')
    } finally {
      setSharing(false)
    }
  }, [planId, isAuthenticated, showToast])

  const unshare = async () => {
    if (!planId) return
    try {
      await exploreApi.unsharePlan(planId)
      setShareUrl('')
      showToast('Share link revoked', 'success')
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Could not revoke the link', 'error')
    }
  }

  const copyShareLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast('Copy failed — select the link and copy it manually', 'warning')
    }
  }

  /** Real export: the browser's print dialog, where the user chooses "Save as PDF". */
  const exportPlan = () => {
    if (!itinerary.days.some((d) => d.stops.length > 0)) {
      showToast('Add at least one stop before exporting', 'warning')
      return
    }
    window.print()
  }

  const field = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
        <h1 className="text-2xl font-bold">Itinerary Builder</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
          >
            <FiSave className="w-4 h-4" />
            {saving ? 'Saving…' : planId ? 'Update trip' : 'Save trip'}
          </button>
          <button
            type="button"
            onClick={share}
            disabled={sharing}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 disabled:opacity-50"
          >
            <FiShare2 className="w-4 h-4" />
            {sharing ? 'Sharing…' : 'Share'}
          </button>
          <button
            type="button"
            onClick={exportPlan}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center gap-2"
          >
            <FiPrinter className="w-4 h-4" />
            Export / Print
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <FiAlertCircle className="mt-0.5 shrink-0" />
          <span>{error}</span>
          <button type="button" onClick={() => setError('')} aria-label="Dismiss" className="ml-auto">
            <FiX />
          </button>
        </div>
      )}

      {/* Trip Details */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <input
          type="text"
          value={itinerary.title}
          onChange={(e) => patch({ title: e.target.value })}
          aria-label="Trip title"
          className="w-full text-xl font-semibold border-none outline-none bg-transparent mb-4"
          placeholder="Trip Title"
        />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor="ib-start" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
            <input id="ib-start" type="date" value={itinerary.startDate} onChange={(e) => patch({ startDate: e.target.value })} className={field} />
          </div>
          <div>
            <label htmlFor="ib-end" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
            <input id="ib-end" type="date" value={itinerary.endDate} onChange={(e) => patch({ endDate: e.target.value })} className={field} />
          </div>
          <div>
            <label htmlFor="ib-travelers" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Travellers</label>
            <input
              id="ib-travelers"
              type="number"
              min={1}
              max={50}
              value={itinerary.travelers}
              onChange={(e) => patch({ travelers: e.target.value })}
              className={field}
            />
          </div>
        </div>
      </div>

      {/* Budget */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FiDollarSign className="w-5 h-5" />
          Budget Calculator
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { key: 'accommodation', label: 'Accommodation' },
            { key: 'food', label: 'Food' },
            { key: 'transport', label: 'Transport' },
            { key: 'activities', label: 'Activities' },
          ].map((item) => (
            <div key={item.key}>
              <label htmlFor={`ib-${item.key}`} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {item.label}
              </label>
              <input
                id={`ib-${item.key}`}
                type="number"
                min={0}
                value={budget[item.key]}
                onChange={(e) => setBudget({ ...budget, [item.key]: Number(e.target.value) || 0 })}
                className={field}
                placeholder="0"
              />
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
          <p className="text-lg font-semibold text-emerald-600">
            Total Budget: NPR {totalBudget.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Days */}
      <div className="space-y-4">
        {itinerary.days.map((day, dayIndex) => (
          <div key={dayIndex} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Day {day.day}</h3>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => addStop(dayIndex)}
                  className="px-3 py-1 text-emerald-600 hover:bg-emerald-50 rounded-lg text-sm flex items-center gap-1"
                >
                  <FiPlus className="w-4 h-4" />
                  Add Stop
                </button>
                {itinerary.days.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeDay(dayIndex)}
                    aria-label={`Remove day ${day.day}`}
                    className="px-3 py-1 text-red-600 hover:bg-red-50 rounded-lg text-sm"
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            {day.stops.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No stops added yet</p>
            ) : (
              <div className="space-y-3">
                {day.stops.map((stop, stopIndex) => (
                  <div key={stop.key} className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center text-sm font-bold">
                        {stopIndex + 1}
                      </div>
                      {stopIndex < day.stops.length - 1 && <div className="w-0.5 h-full bg-emerald-200 mt-2" />}
                    </div>
                    <div className="flex-1 space-y-2">
                      <input
                        type="text"
                        value={stop.name}
                        onChange={(e) => updateStop(dayIndex, stop.key, 'name', e.target.value)}
                        aria-label={`Stop ${stopIndex + 1} on day ${day.day}`}
                        placeholder="Destination name"
                        className={field}
                      />
                      <div className="flex gap-2">
                        <input
                          type="time"
                          value={stop.time}
                          onChange={(e) => updateStop(dayIndex, stop.key, 'time', e.target.value)}
                          aria-label={`Time for stop ${stopIndex + 1}`}
                          className="px-3 py-2 border border-gray-300 rounded-lg"
                        />
                        <input
                          type="text"
                          value={stop.notes}
                          onChange={(e) => updateStop(dayIndex, stop.key, 'notes', e.target.value)}
                          aria-label={`Notes for stop ${stopIndex + 1}`}
                          placeholder="Notes..."
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeStop(dayIndex, stop.key)}
                      aria-label={`Remove stop ${stopIndex + 1} on day ${day.day}`}
                      className="text-red-500 hover:bg-red-50 p-2 rounded self-start"
                    >
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        type="button"
        onClick={addDay}
        className="w-full mt-4 px-4 py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-emerald-500 hover:text-emerald-600 flex items-center justify-center gap-2"
      >
        <FiPlus className="w-5 h-5" />
        Add Day
      </button>

      {/* Share Modal */}
      {showShare && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-1">Share Itinerary</h3>
            <p className="text-sm text-gray-500 mb-4">
              Anyone with this link can view a read-only copy of your trip.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={shareUrl}
                aria-label="Share link"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
              />
              <button
                type="button"
                onClick={copyShareLink}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center gap-1 shrink-0"
              >
                {copied ? <FiCheck className="w-4 h-4" /> : <FiCopy className="w-4 h-4" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                type="button"
                onClick={unshare}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
              >
                Revoke link
              </button>
              <button
                type="button"
                onClick={() => setShowShare(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ItineraryBuilder