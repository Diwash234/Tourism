import { useState, useCallback } from "react"
import { FiPlus, FiTrash2, FiGripVertical, FiClock, FiMapPin, FiDollarSign, FiCalendar } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"

/**
 * Interactive trip itinerary builder with drag-and-drop ordering,
 * day-by-day planning, and budget tracking.
 */
export default function TripItineraryBuilder({ destinations = [], onSave }) {
  const { t } = useTranslation()
  const [tripName, setTripName] = useState("")
  const [days, setDays] = useState([
    { id: 1, date: "", activities: [] }
  ])
  const [budget, setBudget] = useState({ accommodation: 0, food: 0, transport: 0, activities: 0 })

  const addDay = useCallback(() => {
    setDays(prev => [...prev, { id: Date.now(), date: "", activities: [] }])
  }, [])

  const removeDay = useCallback((dayId) => {
    setDays(prev => prev.filter(d => d.id !== dayId))
  }, [])

  const addActivity = useCallback((dayId) => {
    setDays(prev => prev.map(d => d.id === dayId ? {
      ...d,
      activities: [...d.activities, { id: Date.now(), time: "", title: "", description: "", cost: 0, location: "" }]
    } : d))
  }, [])

  const updateActivity = useCallback((dayId, activityId, field, value) => {
    setDays(prev => prev.map(d => d.id === dayId ? {
      ...d,
      activities: d.activities.map(a => a.id === activityId ? { ...a, [field]: value } : a)
    } : d))
  }, [])

  const removeActivity = useCallback((dayId, activityId) => {
    setDays(prev => prev.map(d => d.id === dayId ? {
      ...d,
      activities: d.activities.filter(a => a.id !== activityId)
    } : d))
  }, [])

  const moveActivity = useCallback((dayId, fromIndex, toIndex) => {
    setDays(prev => prev.map(d => {
      if (d.id !== dayId) return d
      const activities = [...d.activities]
      const [moved] = activities.splice(fromIndex, 1)
      activities.splice(toIndex, 0, moved)
      return { ...d, activities }
    }))
  }, [])

  const totalBudget = Object.values(budget).reduce((sum, val) => sum + (Number(val) || 0), 0)

  const handleSave = () => {
    const trip = { name: tripName, days, budget, totalBudget }
    localStorage.setItem("ny-trip-plan", JSON.stringify(trip))
    onSave?.(trip)
  }

  return (
    <div className="space-y-6">
      {/* Trip Header */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1.5">
              Trip Name
            </label>
            <input
              type="text"
              value={tripName}
              onChange={(e) => setTripName(e.target.value)}
              placeholder="My Nepal Adventure"
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleSave}
              className="px-6 py-2.5 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors"
            >
              Save Trip
            </button>
          </div>
        </div>
      </div>

      {/* Budget Overview */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h4 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FiDollarSign size={16} className="text-[var(--ny-green)]" />
          Budget Planner
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { key: "accommodation", label: "Accommodation" },
            { key: "food", label: "Food & Drinks" },
            { key: "transport", label: "Transport" },
            { key: "activities", label: "Activities" },
          ].map(item => (
            <div key={item.key}>
              <label className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider block mb-1">
                {item.label}
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">NPR</span>
                <input
                  type="number"
                  value={budget[item.key]}
                  onChange={(e) => setBudget(prev => ({ ...prev, [item.key]: e.target.value }))}
                  className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 pl-12 pr-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-[var(--ny-border)] flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Total Budget</span>
          <span className="text-lg font-bold text-[var(--ny-green)]">NPR {totalBudget.toLocaleString()}</span>
        </div>
      </div>

      {/* Days */}
      {days.map((day, dayIndex) => (
        <div key={day.id} className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--ny-green)] text-white text-xs font-bold">
                {dayIndex + 1}
              </span>
              <div>
                <h4 className="text-sm font-bold text-gray-900 dark:text-white">Day {dayIndex + 1}</h4>
                <input
                  type="date"
                  value={day.date}
                  onChange={(e) => setDays(prev => prev.map(d => d.id === day.id ? { ...d, date: e.target.value } : d))}
                  className="text-xs text-gray-500 dark:text-gray-400 bg-transparent border-none focus:outline-none"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={() => removeDay(day.id)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
              aria-label="Remove day"
            >
              <Trash2 size={14} />
            </button>
          </div>

          {/* Activities */}
          <div className="space-y-2">
            {day.activities.map((activity, actIndex) => (
              <div key={actIndex} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)]">
                <GripVertical size={14} className="text-gray-300 dark:text-gray-600 shrink-0" />
                <input
                  type="time"
                  value={activity.time}
                  onChange={(e) => {
                    const updated = [...days]
                    updated[dayIndex].activities[actIndex].time = e.target.value
                    setDays(updated)
                  }}
                  className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <input
                  type="text"
                  value={activity.title}
                  onChange={(e) => {
                    const updated = [...days]
                    updated[dayIndex].activities[actIndex].title = e.target.value
                    setDays(updated)
                  }}
                  placeholder="Activity name"
                  className="flex-1 text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <input
                  type="number"
                  value={activity.cost}
                  onChange={(e) => {
                    const updated = [...days]
                    updated[dayIndex].activities[actIndex].cost = Number(e.target.value)
                    setDays(updated)
                  }}
                  placeholder="Cost"
                  className="w-20 text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => addActivity(dayIndex, { time: "09:00", title: "", description: "", cost: 0, location: "" })}
            className="mt-3 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] transition-colors"
          >
            <Plus size={14} />
            Add Activity
          </button>
        </div>
      ))}

      {/* Add Day Button */}
      <button
        type="button"
        onClick={addDay}
        className="flex w-full items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-600 text-sm font-semibold text-gray-500 dark:text-gray-400 hover:border-[var(--ny-green)] hover:text-[var(--ny-green)] transition-colors"
      >
        <Plus size={16} />
        Add Day
      </button>
    </div>
  )
}
