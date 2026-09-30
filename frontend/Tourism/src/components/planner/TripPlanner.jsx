import { useState, useMemo } from "react"
import { FiCalendar, FiMapPin, FiClock, FiUsers, FiPlus, FiTrash2, FiSave } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { useAuth } from "../../hooks/useAuth"
import { useToast } from "../common/Toast"
import { destinationApi } from "../../services/destinationService"

/**
 * Interactive trip planner with day-by-day itinerary builder.
 * Users can add destinations, set dates, and plan their day.
 */
export default function TripPlanner() {
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [destinations, setDestinations] = useState([])
  const [selectedDest, setSelectedDest] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [travelers, setTravelers] = useState(2)
  const [days, setDays] = useState([])

  const addDestination = async () => {
    if (!selectedDest) return
    try {
      const dest = await destinationApi.getById(selectedDest)
      setDestinations([...destinations, dest])
      setSelectedDest("")
      addToast(`${dest.name} added to trip!`, "success")
    } catch (err) {
      addToast("Failed to add destination", "error")
    }
  }

  const removeDestination = (id) => {
    setDestinations(destinations.filter(d => d.id !== id))
  }

  const totalDays = useMemo(() => {
    if (!startDate || !endDate) return 0
    const start = new Date(startDate)
    const end = new Date(endDate)
    return Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
  }, [startDate, endDate])

  const estimatedBudget = useMemo(() => {
    const baseCost = 500 // per day per person
    return totalDays * travelers * baseCost
  }, [totalDays, travelers])

  const handleSave = () => {
    if (!isAuthenticated) {
      addToast("Please login to save your trip", "warning")
      return
    }
    const trip = { destinations, startDate, endDate, travelers, days }
    localStorage.setItem("ny-current-trip", JSON.stringify(trip))
    addToast("Trip saved successfully!", "success")
  }

  return (
    <div className="space-y-6">
      {/* Trip Setup */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FiCalendar size={16} className="text-[var(--ny-green)]" />
          Plan Your Trip
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
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">Add Destination</label>
            <div className="flex gap-2">
              <select
                value={selectedDest}
                onChange={(e) => setSelectedDest(e.target.value)}
                className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">Select...</option>
                {/* Populated from API */}
              </select>
              <button
                type="button"
                onClick={addDestination}
                className="px-3 py-2 rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
                aria-label="Add destination"
              >
                <FiPlus size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Trip Summary */}
      {totalDays > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 text-center">
            <FiClock size={20} className="mx-auto text-[var(--ny-green)] mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{totalDays}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Days</p>
          </div>
          <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 text-center">
            <FiMapPin size={20} className="mx-auto text-[var(--ny-green)] mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{destinations.length}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Destinations</p>
          </div>
          <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 text-center">
            <FiUsers size={20} className="mx-auto text-[var(--ny-green)] mb-2" />
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{travelers}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Travelers</p>
          </div>
          <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl p-4 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Est. Budget</p>
            <p className="text-2xl font-bold text-[var(--ny-green)]">NPR {estimatedBudget.toLocaleString()}</p>
            <p className="text-xs text-gray-400">Total</p>
          </div>
        </div>
      )}

      {/* Destinations List */}
      {destinations.length > 0 && (
        <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Your Itinerary</h3>
            <button
              type="button"
              onClick={handleSave}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
            >
              <FiSave size={14} />
              Save Trip
            </button>
          </div>
          <div className="space-y-3">
            {destinations.map((dest, i) => (
              <div key={dest.id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)]">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--ny-green)] text-white text-xs font-bold shrink-0">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{dest.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{dest.district}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeDestination(dest.id)}
                  className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                  aria-label={`Remove ${dest.name}`}
                >
                  <FiTrash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
