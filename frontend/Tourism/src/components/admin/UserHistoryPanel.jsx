import { FiClock, FiMapPin, FiEye } from "react-icons/fi"

export default function UserHistoryPanel({ history = [] }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b pb-2">
        <h3 className="font-bold text-sm text-gray-900 flex items-center gap-1.5">
          <FiClock className="text-purple-600" /> Recent Destination Visits
        </h3>
        <span className="text-xs text-gray-500 font-semibold">{history.length} Logs</span>
      </div>

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {history.map((h, i) => (
          <div key={i} className="p-3 rounded-xl bg-purple-50/60 border border-purple-100 flex items-center justify-between text-xs">
            <div>
              <p className="font-bold text-gray-900">{h.destination__name || h.name}</p>
              <p className="text-[11px] text-gray-500">📍 {h.destination__city || h.city || "Nepal"}</p>
            </div>
            <span className="text-[10px] font-semibold text-purple-700">
              {h.viewed_at ? new Date(h.viewed_at).toLocaleDateString() : "Recent"}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
