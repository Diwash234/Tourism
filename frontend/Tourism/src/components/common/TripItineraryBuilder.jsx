import { useState, useCallback } from "react"
import { FiPlus, FiTrash2, FiGripVertical, FiDollarSign, FiChevronUp, FiChevronDown } from "react-icons/fi"

/**
 * Interactive trip itinerary builder with day-by-day planning and budget tracking.
 * Keeps the plan locally so an unfinished trip survives a page refresh.
 */
export default function TripItineraryBuilder({ onSave }) {
  const [tripName, setTripName] = useState("")
  const [days, setDays] = useState([
    { id: 1, date: "", activities: [] }
  ])
  const [budget, setBudget] = useState({
    accommodation: 0,
    food: 0,
    transport: 0,
    activities: 0,
  })

  const addDay = useCallback(() => {
    setDays((prev) => [
      ...prev,
      { id: Date.now(), date: "", activities: [] },
    ])
  }, [])

  const removeDay = useCallback((dayId) => {
    setDays((prev) => {
      if (prev.length === 1) return prev
      return prev.filter((day) => day.id !== dayId)
    })
  }, [])

  const addActivity = useCallback((dayId) => {
    setDays((prev) => prev.map((day) => (
      day.id === dayId
        ? {
            ...day,
            activities: [
              ...day.activities,
              {
                id: Date.now(),
                time: "09:00",
                title: "",
                description: "",
                cost: 0,
                location: "",
              },
            ],
          }
        : day
    )))
  }, [])

  const updateActivity = useCallback((dayId, activityId, field, value) => {
    setDays((prev) => prev.map((day) => (
      day.id === dayId
        ? {
            ...day,
            activities: day.activities.map((activity) => (
              activity.id === activityId
                ? { ...activity, [field]: value }
                : activity
            )),
          }
        : day
    )))
  }, [])

  const removeActivity = useCallback((dayId, activityId) => {
    setDays((prev) => prev.map((day) => (
      day.id === dayId
        ? { ...day, activities: day.activities.filter((activity) => activity.id !== activityId) }
        : day
    )))
  }, [])

  const moveActivity = useCallback((dayId, fromIndex, toIndex) => {
    setDays((prev) => prev.map((day) => {
      if (day.id !== dayId) return day

      const activities = [...day.activities]
      if (
        fromIndex < 0 ||
        toIndex < 0 ||
        fromIndex >= activities.length ||
        toIndex >= activities.length
      ) {
        return day
      }

      const [moved] = activities.splice(fromIndex, 1)
      activities.splice(toIndex, 0, moved)
      return { ...day, activities }
    }))
  }, [])

  const totalBudget = Object.values(budget).reduce(
    (sum, value) => sum + (Number(value) || 0),
    0
  )

  const handleSave = () => {
    const trip = {
      name: tripName.trim() || "My Nepal Trip",
      days,
      budget,
      totalBudget,
    }

    try {
      localStorage.setItem("ny-trip-plan", JSON.stringify(trip))
    } catch {
      // Saving through onSave still works when browser storage is unavailable.
    }

    onSave?.(trip)
  }

  return (
    <div className="space-y-6">
      <div className="ny-card p-5">
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex-1">
            <label htmlFor="trip-name" className="ny-field-label">
              Trip Name
            </label>
            <input
              id="trip-name"
              type="text"
              value={tripName}
              onChange={(event) => setTripName(event.target.value)}
              placeholder="My Nepal Adventure"
              className="w-full"
            />
          </div>
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleSave}
              className="ny-btn ny-btn-primary w-full sm:w-auto"
            >
              Save Trip
            </button>
          </div>
        </div>
      </div>

      <div className="ny-card p-5">
        <h2 className="mb-4 flex items-center gap-2 text-base font-bold">
          <FiDollarSign size={17} className="text-[var(--ny-green)]" aria-hidden="true" />
          Budget Planner
        </h2>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { key: "accommodation", label: "Accommodation" },
            { key: "food", label: "Food & Drinks" },
            { key: "transport", label: "Transport" },
            { key: "activities", label: "Activities" },
          ].map((item) => (
            <div key={item.key}>
              <label htmlFor={`budget-${item.key}`} className="ny-field-label text-xs">
                {item.label}
              </label>
              <div className="relative">
                <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--ny-text-muted)]">
                  NPR
                </span>
                <input
                  id={`budget-${item.key}`}
                  type="number"
                  min="0"
                  inputMode="decimal"
                  value={budget[item.key]}
                  onChange={(event) => setBudget((prev) => ({
                    ...prev,
                    [item.key]: event.target.value,
                  }))}
                  className="w-full pl-12"
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-[var(--ny-border)] pt-4">
          <span className="text-sm font-semibold">Total Budget</span>
          <span className="text-lg font-bold text-[var(--ny-green)]">
            NPR {totalBudget.toLocaleString()}
          </span>
        </div>
      </div>

      {days.map((day, dayIndex) => (
        <section key={day.id} className="ny-card p-5" aria-labelledby={`trip-day-${day.id}`}>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[var(--ny-green)] text-xs font-bold text-white">
                {dayIndex + 1}
              </span>
              <div className="min-w-0">
                <h2 id={`trip-day-${day.id}`} className="text-sm font-bold">
                  Day {dayIndex + 1}
                </h2>
                <label htmlFor={`day-date-${day.id}`} className="sr-only">
                  Date for day {dayIndex + 1}
                </label>
                <input
                  id={`day-date-${day.id}`}
                  type="date"
                  value={day.date}
                  onChange={(event) => setDays((prev) => prev.map((item) => (
                    item.id === day.id ? { ...item, date: event.target.value } : item
                  )))}
                  className="mt-1 min-h-8 border-0 bg-transparent p-0 text-xs shadow-none focus:ring-0"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => removeDay(day.id)}
              disabled={days.length === 1}
              className="rounded-lg p-2 text-[var(--ny-text-muted)] transition hover:bg-[var(--ny-soft-red)] hover:text-[var(--ny-danger)] disabled:cursor-not-allowed disabled:opacity-40"
              aria-label={days.length === 1 ? "At least one trip day is required" : `Remove day ${dayIndex + 1}`}
            >
              <FiTrash2 size={16} aria-hidden="true" />
            </button>
          </div>

          <div className="space-y-2">
            {day.activities.map((activity, activityIndex) => (
              <div
                key={activity.id}
                className="grid gap-3 rounded-xl border border-[var(--ny-border)] bg-[var(--ny-soft-green)]/40 p-3 sm:grid-cols-[auto_auto_1fr_7rem_auto]"
              >
                <div className="flex items-center text-[var(--ny-text-muted)]" aria-hidden="true">
                  <FiGripVertical size={16} />
                </div>

                <label className="sr-only" htmlFor={`activity-time-${activity.id}`}>
                  Activity time
                </label>
                <input
                  id={`activity-time-${activity.id}`}
                  type="time"
                  value={activity.time}
                  onChange={(event) => updateActivity(day.id, activity.id, "time", event.target.value)}
                  className="min-h-10"
                />

                <div className="min-w-0">
                  <label className="sr-only" htmlFor={`activity-title-${activity.id}`}>
                    Activity name
                  </label>
                  <input
                    id={`activity-title-${activity.id}`}
                    type="text"
                    value={activity.title}
                    onChange={(event) => updateActivity(day.id, activity.id, "title", event.target.value)}
                    placeholder="Activity name"
                    className="w-full"
                  />
                </div>

                <div className="relative">
                  <label className="sr-only" htmlFor={`activity-cost-${activity.id}`}>
                    Activity cost
                  </label>
                  <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--ny-text-muted)]">
                    NPR
                  </span>
                  <input
                    id={`activity-cost-${activity.id}`}
                    type="number"
                    min="0"
                    inputMode="decimal"
                    value={activity.cost}
                    onChange={(event) => updateActivity(day.id, activity.id, "cost", event.target.value)}
                    placeholder="Cost"
                    className="w-full pl-12"
                  />
                </div>

                <div className="flex items-center justify-end gap-1">
                  <button
                    type="button"
                    onClick={() => moveActivity(day.id, activityIndex, activityIndex - 1)}
                    disabled={activityIndex === 0}
                    className="rounded-lg p-2 text-[var(--ny-text-muted)] hover:bg-white hover:text-[var(--ny-green)] disabled:opacity-30"
                    aria-label="Move activity up"
                  >
                    <FiChevronUp size={16} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveActivity(day.id, activityIndex, activityIndex + 1)}
                    disabled={activityIndex === day.activities.length - 1}
                    className="rounded-lg p-2 text-[var(--ny-text-muted)] hover:bg-white hover:text-[var(--ny-green)] disabled:opacity-30"
                    aria-label="Move activity down"
                  >
                    <FiChevronDown size={16} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    onClick={() => removeActivity(day.id, activity.id)}
                    className="rounded-lg p-2 text-[var(--ny-text-muted)] hover:bg-[var(--ny-soft-red)] hover:text-[var(--ny-danger)]"
                    aria-label={`Remove ${activity.title || `activity ${activityIndex + 1}`}`}
                  >
                    <FiTrash2 size={16} aria-hidden="true" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => addActivity(day.id)}
            className="ny-btn ny-btn-secondary ny-btn-sm mt-3"
          >
            <FiPlus size={15} aria-hidden="true" />
            Add Activity
          </button>
        </section>
      ))}

      <button
        type="button"
        onClick={addDay}
        className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-[var(--ny-border)] py-3 text-sm font-semibold text-[var(--ny-text-secondary)] transition hover:border-[var(--ny-green)] hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]"
      >
        <FiPlus size={16} aria-hidden="true" />
        Add Day
      </button>
    </div>
  )
}
