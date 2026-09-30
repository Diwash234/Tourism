import { useState, useMemo } from "react"
import { FiCalendar, FiMapPin, FiClock, FiUsers, FiTrendingUp, FiPlus, FiTrash2, FiSave } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { useAuth } from "../../hooks/useAuth"
import { useToast } from "../common/Toast"
import { destinationApi } from "../../services/destinationService"

/**
 * Interactive trip planner with day-by-day itinerary builder.
 * Users can add destinations, set dates, and organize activities.
 */
export default function TripPlanner() {
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [destinations, setDestinations] = useState([])
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [travelers, setTravelers] = useState(2)
  const [selectedDest, setSelectedDest] = useState("")
  const [itinerary, setItinerary] = useState([])
  const [loading, setLoading] = useState(false)

  const totalDays = useMemo(() => {
    if (!startDate || !endDate) return 0
    const start = new Date(startDate)
    const end = new Date(endDate)
    return Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
  }, [startDate, endDate])

  const addDestination = async () => {
    if (!selectedDest) return
    setLoading(true)
    try {
      const dest = await destinationApi.getById(selectedDest)
      if (!destinations.find(d => d.id === dest.id)) {
        setDestinations([...destinations, dest])
        addToast(`${dest.name} added to trip!`, "success")
      }
    } catch (err) {
      addToast("Failed to add destination", "error")
    } finally {
      setLoading(false)
      setSelectedDest("")
    }
  }

  const removeDestination = (id) => {
    setDestinations(destinations.filter(d => d.id !== id))
  }

  const addDay = () => {
    if (itinerary.length >= totalDays) {
      addToast("Maximum days reached for this trip", "warning")
      return
    }
    setItinerary([...itinerary, { day: itinerary.length + 1, activities: [] }])
  }

  const addActivity = (dayIndex, activity) => {
    const updated = [...itinerary]
    updated[dayIndex].activities.push({
      id: Date.now(),
      time: activity.time || "09:00",
      title: activity.title,
      description: activity.description || "",
      location: activity.location || "",
    })
    setItinerary(updated)
  }

  const removeActivity = (dayIndex, activityId) => {
    const updated = [...itinerary]
    updated[dayIndex].activities = updated[dayIndex].activities.filter(a => a.id !== activityId)
    setItinerary(updated)
  }

  const handleSave = () => {
    if (!isAuthenticated) {
      addToast("Please login to save your trip", "warning")
      return
    }
    const trip = { destinations, startDate, endDate, travelers, itinerary }
    localStorage.setItem("ny-saved-trip", JSON.stringify(trip))
    addToast("Trip saved successfully!", "success")
  }

  return (
    <div className="space-y-6">
      {/* Trip Setup */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FiCalendar size={16} className="text-[var(--ny-green)]" />
          Trip Setup
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">
              <FiUsers size={12} className="inline mr-1" />
              Travelers
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={travelers}
              onChange={(e) => setTravelers(Number(e.target.value))}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleSave}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors"
            >
              <FiSave size={16} />
              Save Trip
            </button>
          </div>
        </div>

        {totalDays > 0 && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
            Trip duration: <span className="font-bold text-[var(--ny-green)]">{totalDays} days</span>
          </p>
        )}
      </div>

      {/* Destinations */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FiMapPin size={16} className="text-[var(--ny-green)]" />
          Destinations
        </h3>

        <div className="flex gap-2 mb-4">
          <select
            value={selectedDest}
            onChange={(e) => setSelectedDest(e.target.value)}
            className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Select a destination...</option>
            {/* Populated from API */}
          </select>
          <button
            type="button"
            onClick={addDestination}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors disabled:opacity-50"
          >
            <FiPlus size={16} />
            Add
          </button>
        </div>

        {destinations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {destinations.map((dest, i) => (
              <div
                key={dest.id || i}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)]"
              >
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{dest.name}</span>
                <button
                  type="button"
                  onClick={() => removeDestination(dest.id)}
                  className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                  aria-label={`Remove ${dest.name}`}
                >
                  <FiX size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Itinerary Builder */}
      {totalDays > 0 && (
        <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <FiClock size={16} className="text-[var(--ny-green)]" />
              Itinerary
            </h3>
            <button
              type="button"
              onClick={addDay}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 text-xs font-semibold hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
            >
              <FiPlus size={14} />
              Add Day
            </button>
          </div>

          <div className="space-y-4">
            {itinerary.map((day, dayIndex) => (
              <div key={dayIndex} className="p-4 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)]">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-gray-900 dark:text-white">Day {day.day}</h4>
                  <button
                    type="button"
                    onClick={() => removeDay(dayIndex)}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                    aria-label="Remove day"
                  >
                    <FiTrash2 size={14} />
                  </button>
                </div>

                <div className="space-y-2">
                  {day.activities.map((activity, actIndex) => (
                    <div key={actIndex} className="flex items-center gap-3 p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-[var(--ny-border)]">
                      <span className="text-xs font-bold text-[var(--ny-green)] w-12 shrink-0">{activity.time}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{activity.title}</p>
                        {activity.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{activity.description}</p>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeActivity(dayIndex, actIndex)}
                        className="p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
                        aria-label="Remove activity"
                      >
                        <FiX size={12} />
                      </button>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => addActivity(dayIndex)}
                  className="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dashed border-gray-300 dark:border-slate-600 text-gray-500 dark:text-gray-400 text-xs font-semibold hover:border-[var(--ny-green)] hover:text-[var(--ny-green)] transition-colors"
                >
                  <FiPlus size={12} />
                  Add Activity
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
