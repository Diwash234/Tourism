import { FiCalendar } from "react-icons/fi"

export default function BestTimeToVisit({ bestTime, altitude, hours }) {
  return (
    <div className="card-base p-6 shadow-lg border border-purple-100 rounded-3xl space-y-4">
      <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
        <FiCalendar className="text-purple-600" /> Best Time to Visit & Climate
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200">
          <p className="font-bold text-amber-900">Recommended Season</p>
          <p className="text-amber-800 mt-1 font-semibold">{bestTime || "Not recorded"}</p>
        </div>
        <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200">
          <p className="font-bold text-blue-900">Elevation / Altitude</p>
          <p className="text-blue-800 mt-1 font-semibold">{altitude || "Not recorded"}</p>
        </div>
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200">
          <p className="font-bold text-emerald-900">Visiting Hours</p>
          <p className="text-emerald-800 mt-1 font-semibold">{hours || "Not recorded"}</p>
        </div>
      </div>
    </div>
  )
}
