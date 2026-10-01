import { useState } from "react"
import { FiCalendar, FiClock, FiMapPin, FiDollarSign, FiUsers, FiPlus, FiTrash2, FiEdit2, FiSave } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { useAuth } from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

/**
 * Interactive itinerary planner for a destination.
 * Users can add activities, set times, and plan their day.
 */
export default function DestinationItinerary({ destination }) {
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [days, setDays] = useState([
    {
      day: 1,
      activities: [
        { time: "09:00", title: "Arrival & Check-in", description: "Arrive at destination and settle in", cost: 0, duration: 60 },
        { time: "11:00", title: "Local Sightseeing", description: "Explore the main attractions nearby", cost: 500, duration: 120 },
        { time: "14:00", title: "Lunch Break", description: "Try local cuisine at a recommended restaurant", cost: 300, duration: 60 },
        { time: "16:00", title: "Cultural Experience", description: "Visit museums, temples, or cultural sites", cost: 200, duration: 120 },
      ],
    },
  ])
  const [editingCell, setEditingCell] = useState(null)
  const [showAddDay, setShowAddDay] = useState(false)

  const addDay = () => {
    const newDay = {
      day: days.length + 1,
      activities: [],
    }
    setDays([...days, newDay])
    setShowAddDay(false)
    addToast(`Day ${newDay.day} added to itinerary!`, "success")
  }

  const removeDay = (dayIndex) => {
    if (days.length <= 1) {
      addToast("Must have at least one day", "warning")
      return
    }
    setDays(days.filter((_, i) => i !== dayIndex))
    addToast("Day removed", "info")
  }

  const addActivity = (dayIndex) => {
    const newActivity = {
      time: "10:00",
      title: "New Activity",
      description: "Describe your activity here",
      cost: 0,
      duration: 60,
    }
    const updated = [...days]
    updated[dayIndex].activities.push(newActivity)
    setDays(updated)
    setEditingCell({ day: dayIndex, activity: updated[dayIndex].activities.length - 1 })
  }

  const removeActivity = (dayIndex, actIndex) => {
    const updated = [...days]
    updated[dayIndex].activities.splice(actIndex, 1)
    setDays(updated)
  }

  const updateActivity = (dayIndex, actIndex, field, value) => {
    const updated = [...days]
    updated[dayIndex].activities[actIndex][field] = value
    setDays(updated)
  }

  const totalCost = days.reduce((sum, day) => sum + day.activities.reduce((s, a) => s + (a.cost || 0), 0), 0)
  const totalActivities = days.reduce((sum, day) => sum + day.activities.length, 0)

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FiCalendar size={16} className="text-[var(--ny-green)]" />
          Trip Itinerary
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {totalActivities} activities
          </span>
          <span className="text-xs font-bold text-[var(--ny-green)]">
            NPR {totalCost.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Days */}
      <div className="space-y-6">
        {days.map((day, dayIndex) => (
          <div key={dayIndex} className="relative">
            {/* Day Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--ny-green)] text-white text-xs font-bold">
                  {day.day}
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">Day {day.day}</span>
                <span className="text-xs text-gray-400">
                  {day.activities.length} activities
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => addActivity(dayIndex)}
                  className="p-1.5 rounded-lg text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] transition-colors"
                  aria-label="Add activity"
                >
                  <FiPlus size={14} />
                </button>
                <button
                  type="button"
                  onClick={() => removeDay(dayIndex)}
                  className="p-1.5 rounded-lg text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                  aria-label="Remove day"
                >
                  <FiTrash2 size={14} />
                </button>
              </div>
            </div>

            {/* Timeline */}
            <div className="relative pl-6 border-l-2 border-[var(--ny-border)] space-y-3">
              {day.activities.map((activity, actIndex) => (
                <div key={actIndex} className="relative">
                  {/* Timeline dot */}
                  <div className="absolute -left-[31px] top-2 h-3 w-3 rounded-full border-2 border-[var(--ny-green)] bg-white dark:bg-slate-800" />

                  {/* Activity Card */}
                  <div className="p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-[var(--ny-border)] hover:border-[var(--ny-green)] transition-colors">
                    {editingCell?.day === dayIndex && editingCell?.activity === actIndex ? (
                      /* Edit Mode */
                      <div className="space-y-2">
                        <div className="flex gap-2">
                          <input
                            type="time"
                            value={activity.time}
                            onChange={(e) => updateActivity(dayIndex, actIndex, "time", e.target.value)}
                            className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300"
                          />
                          <input
                            type="number"
                            value={activity.cost}
                            onChange={(e) => updateActivity(dayIndex, actIndex, "cost", Number(e.target.value))}
                            placeholder="Cost"
                            className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 w-20"
                          />
                          <input
                            type="number"
                            value={activity.duration}
                            onChange={(e) => updateActivity(dayIndex, actIndex, "duration", Number(e.target.value))}
                            placeholder="Min"
                            className="text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 w-16"
                          />
                        </div>
                        <input
                          type="text"
                          value={activity.title}
                          onChange={(e) => updateActivity(dayIndex, actIndex, "title", e.target.value)}
                          className="w-full text-sm font-semibold rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300"
                        />
                        <textarea
                          value={activity.description}
                          onChange={(e) => updateActivity(dayIndex, actIndex, "description", e.target.value)}
                          rows={2}
                          className="w-full text-xs rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 resize-none"
                        />
                        <div className="flex justify-end">
                          <button
                            type="button"
                            onClick={() => setEditingCell(null)}
                            className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
                          >
                            <FiSave size={12} /> Done
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* View Mode */
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[var(--ny-green)]">{activity.time}</span>
                            <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                              <FiClock size={10} /> {activity.duration} min
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{activity.title}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{activity.description}</p>
                          {activity.cost > 0 && (
                            <p className="text-xs font-semibold text-[var(--ny-green)] mt-1">NPR {activity.cost.toLocaleString()}</p>
                          )}
                        </div>
                        <div className="flex gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => setEditingCell({ day: dayIndex, activity: actIndex })}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] transition-colors"
                            aria-label="Edit activity"
                          >
                            <FiEdit2 size={12} />
                          </button>
                          <button
                            type="button"
                            onClick={() => removeActivity(dayIndex, actIndex)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                            aria-label="Remove activity"
                          >
                            <FiTrash2 size={12} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                ))}
              </div>
            </div>
          ))}
      </div>

      {/* Add Day Button */}
      <button
        type="button"
        onClick={() => setShowAddDay(true)}
        className="flex w-full items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed border-gray-300 dark:border-slate-600 text-sm font-semibold text-gray-500 dark:text-gray-400 hover:border-[var(--ny-green)] hover:text-[var(--ny-green)] transition-colors"
      >
        <FiPlus size={16} />
        Add Day
      </button>
    </div>
  )
}
