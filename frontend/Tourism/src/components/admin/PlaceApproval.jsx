import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiCheck, FiX, FiInfo, FiMapPin, FiCalendar, FiDollarSign } from "react-icons/fi"

export default function PlaceApproval({ pendingPlaces = [], onApprove, onReject }) {
  const [inspectingPlace, setInspectingPlace] = useState(null)

  if (!pendingPlaces || pendingPlaces.length === 0) {
    return (
      <div className="p-12 text-center bg-orange-950/40 rounded-3xl border border-orange-800/40">
        <FiCheck className="mx-auto text-emerald-400 mb-2" size={32} />
        <p className="font-bold text-lg text-white">All submissions reviewed!</p>
        <p className="text-sm text-orange-300">No pending destination submissions waiting for review.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {pendingPlaces.map((p) => (
          <motion.div
            key={p.id}
            whileHover={{ y: -4 }}
            className="bg-orange-950/70 border border-orange-700/50 rounded-2xl p-6 shadow-xl space-y-4 flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-400 text-gray-950">
                    {p.category_name}
                  </span>
                  <h4 className="text-xl font-bold text-white mt-1">{p.name}</h4>
                  <p className="text-xs text-orange-300">
                    📍 {p.municipality || p.district} {p.ward_number ? `(Ward ${p.ward_number})` : ""}, {p.province}
                  </p>
                </div>
                <span className="text-[11px] text-orange-300 font-medium">By: {p.created_by}</span>
              </div>

              {p.cover_image_url && (
                <div className="h-44 rounded-xl overflow-hidden border border-orange-800">
                  <img src={p.cover_image_url} alt={p.name} className="w-full h-full object-cover" />
                </div>
              )}

              <div className="p-3.5 rounded-xl bg-orange-900/40 border border-orange-800/40 text-xs text-orange-100 space-y-1.5">
                <p><b>Description:</b> {p.description || "No description provided."}</p>
                <p><b>Coordinates:</b> {p.latitude?.toFixed(4)}, {p.longitude?.toFixed(4)} ({p.altitude || "Altitude N/A"})</p>
                {p.history && <p><b>History:</b> {p.history}</p>}
                {p.nearest_hospital_info && <p><b>Hospital:</b> {p.nearest_hospital_info}</p>}
                {p.nearest_hotel_info && <p><b>Hotel:</b> {p.nearest_hotel_info}</p>}
              </div>
            </div>

            {/* GREEN Accept & RED Reject Buttons */}
            <div className="flex items-center justify-between gap-2 pt-3 border-t border-orange-800/40">
              <button
                onClick={() => setInspectingPlace(p)}
                className="px-3.5 py-2 rounded-xl bg-orange-900 hover:bg-orange-800 text-orange-200 text-xs font-semibold flex items-center gap-1.5 border border-orange-700"
              >
                <FiInfo size={13} /> View All Details
              </button>

              <div className="flex gap-2">
                <button
                  onClick={() => onReject(p.id)}
                  className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-rose-600/30 transition-all"
                >
                  <FiX size={15} /> Reject (Red)
                </button>
                <button
                  onClick={() => onApprove(p.id)}
                  className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-black flex items-center gap-1.5 shadow-lg shadow-emerald-500/30 transition-all"
                >
                  <FiCheck size={16} /> Accept & Publish (Green)
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Full inspection modal */}
      <AnimatePresence>
        {inspectingPlace && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-gradient-to-br from-[#1d0626] via-[#320a3d] to-[#4c0d38] border border-orange-500/60 rounded-3xl p-6 sm:p-8 max-w-3xl w-full shadow-2xl space-y-6 text-white max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-start justify-between border-b border-orange-700/60 pb-4">
                <div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-gray-950">
                    {inspectingPlace.category_name}
                  </span>
                  <h2 className="text-2xl font-black text-white mt-1">{inspectingPlace.name}</h2>
                  <p className="text-xs text-orange-300">
                    Submitted by: <b>{inspectingPlace.created_by}</b> · {new Date(inspectingPlace.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button onClick={() => setInspectingPlace(null)} className="p-2 rounded-full bg-orange-900/60 hover:bg-orange-800 text-orange-200">
                  <FiX size={20} />
                </button>
              </div>

              {inspectingPlace.cover_image_url && (
                <div className="h-64 rounded-2xl overflow-hidden border border-orange-700 shadow-lg">
                  <img src={inspectingPlace.cover_image_url} alt={inspectingPlace.name} className="w-full h-full object-cover" />
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-2xl bg-orange-950/80 border border-orange-700/50 text-xs">
                <div>
                  <span className="text-orange-300">Province</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.province || "Gandaki"}</p>
                </div>
                <div>
                  <span className="text-orange-300">District</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.district}</p>
                </div>
                <div>
                  <span className="text-orange-300">Municipality</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.municipality || "N/A"}</p>
                </div>
                <div>
                  <span className="text-orange-300">Ward Number</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.ward_number ? `Ward ${inspectingPlace.ward_number}` : "N/A"}</p>
                </div>
                <div>
                  <span className="text-orange-300">Latitude</span>
                  <p className="font-bold text-amber-300 mt-0.5">{inspectingPlace.latitude?.toFixed(6)}</p>
                </div>
                <div>
                  <span className="text-orange-300">Longitude</span>
                  <p className="font-bold text-amber-300 mt-0.5">{inspectingPlace.longitude?.toFixed(6)}</p>
                </div>
                <div>
                  <span className="text-orange-300">Altitude</span>
                  <p className="font-bold text-cyan-300 mt-0.5">{inspectingPlace.altitude || "N/A"}</p>
                </div>
                <div>
                  <span className="text-orange-300">Entry Fee</span>
                  <p className="font-bold text-emerald-300 mt-0.5">NPR {inspectingPlace.entry_fee || 0}</p>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-4 rounded-2xl bg-orange-950/60 border border-orange-800">
                  <h4 className="font-bold text-amber-300 mb-1">Full Description:</h4>
                  <p className="text-orange-100 leading-relaxed whitespace-pre-line">{inspectingPlace.description}</p>
                </div>

                {inspectingPlace.history && (
                  <div className="p-4 rounded-2xl bg-orange-950/60 border border-orange-800">
                    <h4 className="font-bold text-amber-300 mb-1">Historical & Cultural Heritage:</h4>
                    <p className="text-orange-100 leading-relaxed whitespace-pre-line">{inspectingPlace.history}</p>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-orange-700/60">
                <button
                  onClick={() => onReject(inspectingPlace.id)}
                  className="px-6 py-3 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-rose-600/30"
                >
                  <FiX size={16} /> Reject Place (Red)
                </button>
                <button
                  onClick={() => onApprove(inspectingPlace.id)}
                  className="px-8 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-2 shadow-xl shadow-emerald-500/30"
                >
                  <FiCheck size={18} /> Accept & Publish to Database (Green)
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
