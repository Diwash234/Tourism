import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCheck,
  FiCompass,
  FiMapPin,
  FiShield,
  FiX,
  FiArrowRight,
  FiAlertTriangle,
  FiCalendar,
  FiDollarSign,
  FiLayers
} from "react-icons/fi"

export default function CuratedCompareModal({
  isOpen,
  onClose,
  comparisonData,
  onSelectItinerary,
  onRemoveFromCompare
}) {
  const [nationality, setNationality] = useState("nepali")
  const [currency, setCurrency] = useState("NPR")

  if (!isOpen || !comparisonData || !comparisonData.comparison?.length) return null

  const items = comparisonData.comparison

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-5xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[92vh] flex flex-col"
        >
          {/* Header */}
          <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <FiLayers size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">Side-by-Side Itinerary Comparison</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Compare duration, alpine altitude, required permits, and estimated expenses
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
              aria-label="Close comparison modal"
            >
              <FiX size={20} />
            </button>
          </div>

          {/* Controls Bar */}
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 shrink-0 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-600">Traveler Persona:</span>
              <div className="flex bg-white rounded-xl border border-slate-200 p-0.5">
                {[
                  { key: "nepali", label: "Domestic 🇳🇵" },
                  { key: "foreign", label: "International 🌍" },
                  { key: "saarc", label: "SAARC 🏛️" },
                ].map((nat) => (
                  <button
                    key={nat.key}
                    type="button"
                    onClick={() => setNationality(nat.key)}
                    className={`px-2.5 py-1 rounded-lg font-bold transition ${
                      nationality === nat.key
                        ? "bg-slate-900 text-white"
                        : "text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {nat.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-600">Currency:</span>
              <div className="flex bg-white rounded-xl border border-slate-200 p-0.5">
                <button
                  type="button"
                  onClick={() => setCurrency("NPR")}
                  className={`px-2.5 py-1 rounded-lg font-bold transition ${
                    currency === "NPR" ? "bg-emerald-700 text-white" : "text-slate-600"
                  }`}
                >
                  NPR
                </button>
                <button
                  type="button"
                  onClick={() => setCurrency("USD")}
                  className={`px-2.5 py-1 rounded-lg font-bold transition ${
                    currency === "USD" ? "bg-emerald-700 text-white" : "text-slate-600"
                  }`}
                >
                  USD
                </button>
              </div>
            </div>
          </div>

          {/* Side by Side Grid Content */}
          <div className="p-5 sm:p-6 space-y-6 overflow-y-auto flex-1">
            <div className={`grid gap-4 ${
              items.length === 2 ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1 md:grid-cols-3"
            }`}>
              {items.map((it) => {
                const cost = it.cost_breakdown
                const totalDisplay = currency === "NPR" ? `NPR ${cost?.total_npr?.toLocaleString()}` : `$${cost?.total_usd?.toLocaleString()}`
                const safety = it.altitude_safety

                return (
                  <div
                    key={it.slug}
                    className="card-base border border-slate-200 bg-white rounded-2xl overflow-hidden flex flex-col shadow-sm hover:shadow-md transition"
                  >
                    {/* Header Image & Title */}
                    <div className="relative h-44 bg-slate-900 overflow-hidden">
                      <img
                        src={it.cover_image}
                        alt={it.title}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                      <div className="absolute top-2.5 right-2.5">
                        {onRemoveFromCompare && (
                          <button
                            type="button"
                            onClick={() => onRemoveFromCompare(it.slug)}
                            className="p-1 rounded-full bg-black/60 text-white hover:bg-rose-600 transition"
                            title="Remove from comparison"
                          >
                            <FiX size={14} />
                          </button>
                        )}
                      </div>
                      <div className="absolute bottom-2.5 left-3 right-3 text-white">
                        <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/20 backdrop-blur-xs">
                          {it.category}
                        </span>
                        <h4 className="text-sm font-bold mt-1 line-clamp-1 leading-snug">
                          {it.title}
                        </h4>
                        {it.title_nepali && (
                          <p className="text-[11px] text-emerald-300 line-clamp-1">{it.title_nepali}</p>
                        )}
                      </div>
                    </div>

                    {/* Quick Metrics Matrix */}
                    <div className="p-4 space-y-4 flex-1">
                      <div className="grid grid-cols-3 gap-2 py-2 border-b border-slate-100 text-center">
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-black block">Days</span>
                          <span className="text-sm font-black text-slate-900">{it.days} Days</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-black block">Max Alt</span>
                          <span className="text-sm font-black text-emerald-800">
                            {it.max_elevation_m ? `${it.max_elevation_m.toLocaleString()}m` : "Sub-Alpine"}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-black block">Difficulty</span>
                          <span className="text-xs font-bold text-amber-700 capitalize">
                            {it.difficulty}
                          </span>
                        </div>
                      </div>

                      {/* Estimated Cost */}
                      <div className="p-3 bg-emerald-50/70 rounded-xl border border-emerald-100">
                        <span className="text-[10px] text-emerald-800 font-bold uppercase tracking-wider block">
                          Estimated Cost ({nationality === "nepali" ? "Domestic Rate" : "Standard Rate"})
                        </span>
                        <span className="text-lg font-black text-emerald-950 font-mono">
                          {totalDisplay}
                        </span>
                      </div>

                      {/* Altitude Risk Meter */}
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-bold text-slate-700">Altitude Risk:</span>
                          <span className={`font-bold text-[11px] ${
                            safety?.risk_class === "extreme" ? "text-rose-600" : safety?.risk_class === "high" ? "text-amber-600" : "text-emerald-700"
                          }`}>
                            {safety?.risk_class?.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                          {safety?.summary}
                        </p>
                      </div>

                      {/* Highlights */}
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-black text-slate-700 uppercase tracking-wide block">
                          Key Highlights:
                        </span>
                        <ul className="space-y-1 text-xs text-slate-600">
                          {it.highlights?.slice(0, 3).map((hl, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <FiCheck className="text-emerald-600 shrink-0 mt-0.5" size={13} />
                              <span className="line-clamp-2">{hl}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Permits & Legal Requirements */}
                      <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-[11px] text-slate-600 space-y-1">
                        <span className="font-bold text-slate-800 flex items-center gap-1">
                          <FiShield className="text-emerald-700" size={12} />
                          Permit Guidelines:
                        </span>
                        <p>
                          {nationality === "nepali"
                            ? it.permits_info?.nepali || "Nepali citizen park entry (NPR 100). No TIMS permit required."
                            : nationality === "saarc"
                            ? it.permits_info?.saarc || "SAARC conservation entry + TIMS permit."
                            : it.permits_info?.foreign || "Foreign TIMS + National Park Permit required."}
                        </p>
                      </div>

                      {/* Transport Info */}
                      {it.transport_info && (
                        <p className="text-[11px] text-slate-500">
                          <strong className="text-slate-700">Transit:</strong> {it.transport_info}
                        </p>
                      )}
                    </div>

                    {/* Launch into Planner Action */}
                    <div className="p-4 pt-0 mt-auto">
                      <button
                        type="button"
                        onClick={() => {
                          onSelectItinerary?.(it.slug)
                          onClose?.()
                        }}
                        className="w-full ny-btn ny-btn-primary flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-xl"
                      >
                        <span>Choose & Load Planner</span>
                        <FiArrowRight size={14} />
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="ny-btn ny-btn-secondary px-6 py-2 text-xs font-bold rounded-xl"
            >
              Close Comparison
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
