import { useState } from "react"
import { FiCalendar, FiMapPin, FiPlus, FiCheck } from "react-icons/fi"

export default function TripPlanner() {
  const [trips, setTrips] = useState([
    { title: "Annapurna Sanctuary Trek", days: 8, start: "2026-10-15", status: "Planning" },
    { title: "Kathmandu Valley Cultural Walk", days: 3, start: "2026-11-02", status: "Confirmed" },
  ])
  const [newTitle, setNewTitle] = useState("")

  const handleAdd = (e) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    setTrips([...trips, { title: newTitle, days: 4, start: new Date().toISOString().split("T")[0], status: "Planning" }])
    setNewTitle("")
  }

  return (
    <div className="card-base p-6 shadow-xl border border-purple-100 rounded-3xl space-y-4">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
          <FiCalendar className="text-purple-600" /> Nepal Custom Trip Planner
        </h3>
        <span className="text-xs font-semibold text-purple-700">{trips.length} Trips</span>
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          placeholder="New trip title (e.g. Rara Lake Wilderness Drive)..."
          className="input-field text-xs flex-1"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
        />
        <button type="submit" className="btn-primary px-4 py-2 text-xs font-bold bg-purple-700 text-white rounded-xl">
          Add Trip
        </button>
      </form>

      <div className="space-y-2">
        {trips.map((t, i) => (
          <div key={i} className="p-3.5 rounded-2xl bg-purple-50/70 border border-purple-100 flex items-center justify-between text-xs">
            <div>
              <p className="font-bold text-gray-900">{t.title}</p>
              <p className="text-[11px] text-gray-500">📅 {t.start} · {t.days} Days</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-purple-200/80 text-purple-900">
              {t.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
