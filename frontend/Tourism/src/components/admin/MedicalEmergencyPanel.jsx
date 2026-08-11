import { motion } from "framer-motion"
import { FiAlertTriangle, FiCheck, FiPhoneCall, FiMapPin, FiClock } from "react-icons/fi"

export default function MedicalEmergencyPanel({ emergencies = [], onResolve }) {
  const activeEmergencies = emergencies.filter((e) => e.status === "active")

  return (
    <div className="space-y-6">
      <div className="bg-rose-950/50 border border-rose-700/60 p-5 rounded-3xl flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg text-white flex items-center gap-2">
            <FiAlertTriangle className="text-rose-400" /> Live Medical Emergency Sentinel & Rescue Dispatch
          </h3>
          <p className="text-xs text-rose-200">
            Immediate 24/7 rescue & hospital coordination dispatch center for tourists in distress across Nepal.
          </p>
        </div>
        <span className="px-3.5 py-1 rounded-full bg-rose-600 text-white font-black text-xs shadow-md">
          {activeEmergencies.length} Active SOS
        </span>
      </div>

      <div className="space-y-4">
        {emergencies.map((e) => (
          <motion.div
            key={e.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl ${
              e.status === "active"
                ? "bg-rose-950/80 border-rose-500 shadow-rose-500/20"
                : "bg-purple-950/60 border-purple-700/40 opacity-80"
            }`}
          >
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  e.status === "active" ? "bg-rose-600 text-white animate-pulse" : "bg-gray-700 text-gray-300"
                }`}>
                  {e.status.toUpperCase()}
                </span>
                <h4 className="font-bold text-white text-base">{e.user_name} ({e.user_email})</h4>
              </div>
              <p className="text-sm text-purple-100 font-medium">{e.message}</p>
              <div className="text-xs text-purple-300 flex flex-wrap items-center gap-4 pt-1">
                {e.user_phone && <span className="flex items-center gap-1">📞 Phone: <b className="text-white">{e.user_phone}</b></span>}
                {e.latitude && <span className="flex items-center gap-1">📍 Coordinates: <b className="text-amber-300">{e.latitude.toFixed(4)}, {e.longitude.toFixed(4)}</b></span>}
                <span className="flex items-center gap-1">🕒 {new Date(e.triggered_at).toLocaleString()}</span>
              </div>
            </div>

            {e.status === "active" && (
              <button
                onClick={() => onResolve(e.id)}
                className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/30 shrink-0"
              >
                <FiCheck size={16} /> Mark Resolved (Green)
              </button>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
