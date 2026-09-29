import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiDollarSign,
  FiX,
  FiUsers,
  FiCompass,
  FiCheck,
  FiShield,
  FiHelpCircle
} from "react-icons/fi"

const NATIONALITY_OPTIONS = [
  { key: "nepali", label: "Nepali Explorer (नेपाली पर्यटक)", flag: "🇳🇵" },
  { key: "saarc", label: "SAARC National (सार्क देशहरू)", flag: "🏛️" },
  { key: "foreign", label: "International Visitor (अन्य देश)", flag: "🌍" },
]

const STYLE_OPTIONS = [
  { key: "budget", label: "Budget / Tea House", icon: "🎒", desc: "Shared rooms, local Dal Bhat, public / shared transit" },
  { key: "standard", label: "Standard Comfort", icon: "🧳", desc: "Private tea house / 3-star room, tourist coach, porter support" },
  { key: "luxury", label: "Luxury / Guided", icon: "💎", desc: "Top boutique lodge / resort, private Scorpio 4WD, certified guide & porter" },
]

export default function CostBreakdownModal({
  isOpen,
  onClose,
  costData,
  title,
  onChangeParameters,
  currentParams
}) {
  const [currencyView, setCurrencyView] = useState("NPR")

  if (!isOpen || !costData) return null

  const isNpr = currencyView === "NPR"
  const total = isNpr ? costData.total_npr : costData.total_usd
  const perPerson = isNpr ? costData.per_person_npr : costData.per_person_usd
  const currencySymbol = isNpr ? "NPR" : "USD $"

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[90vh] flex flex-col"
        >
          {/* Header */}
          <div className="p-5 sm:p-6 bg-emerald-950 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <FiDollarSign size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">Itemized Dual-Persona Cost Calculator</h3>
                <p className="text-xs text-emerald-200 mt-0.5">{title || "Estimated Itinerary Expenses"}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-emerald-300 hover:text-white hover:bg-white/10 transition"
              aria-label="Close cost breakdown modal"
            >
              <FiX size={20} />
            </button>
          </div>

          {/* Interactive Controls Bar */}
          <div className="p-4 bg-slate-50 border-b border-slate-200 space-y-3 shrink-0">
            {/* Nationality Pill Buttons */}
            <div>
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                Select Traveler Nationality:
              </span>
              <div className="grid grid-cols-3 gap-1.5">
                {NATIONALITY_OPTIONS.map((nat) => (
                  <button
                    key={nat.key}
                    type="button"
                    onClick={() => onChangeParameters?.({ nationality: nat.key })}
                    className={`py-1.5 px-2 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition ${
                      currentParams?.nationality === nat.key
                        ? "bg-emerald-900 text-white border-emerald-900 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    <span>{nat.flag}</span>
                    <span className="truncate">{nat.label.split(" ")[0]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Travel Style and Group Size */}
            <div className="grid sm:grid-cols-2 gap-3 pt-1">
              <div>
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                  Travel Comfort Style:
                </span>
                <div className="flex gap-1.5">
                  {STYLE_OPTIONS.map((sty) => (
                    <button
                      key={sty.key}
                      type="button"
                      onClick={() => onChangeParameters?.({ style: sty.key })}
                      className={`flex-1 py-1.5 px-2 rounded-xl text-xs font-semibold border text-center transition ${
                        currentParams?.style === sty.key
                          ? "bg-slate-900 text-white border-slate-900"
                          : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      <span>{sty.icon} </span>
                      <span>{sty.label.split(" ")[0]}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                  Party Size (Travelers):
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex items-center border border-slate-200 rounded-xl bg-white overflow-hidden p-1 flex-1">
                    <button
                      type="button"
                      disabled={currentParams?.travelers <= 1}
                      onClick={() => onChangeParameters?.({ travelers: Math.max(1, (currentParams?.travelers || 1) - 1) })}
                      className="px-3 py-1 font-bold text-slate-600 hover:bg-slate-100 rounded-lg disabled:opacity-30"
                    >
                      -
                    </button>
                    <span className="flex-1 text-center font-black text-sm text-slate-800">
                      {currentParams?.travelers || 1} Person{currentParams?.travelers > 1 ? "s" : ""}
                    </span>
                    <button
                      type="button"
                      disabled={currentParams?.travelers >= 10}
                      onClick={() => onChangeParameters?.({ travelers: Math.min(10, (currentParams?.travelers || 1) + 1) })}
                      className="px-3 py-1 font-bold text-slate-600 hover:bg-slate-100 rounded-lg disabled:opacity-30"
                    >
                      +
                    </button>
                  </div>

                  {/* Currency Switcher */}
                  <div className="flex border border-slate-200 rounded-xl bg-white p-1">
                    <button
                      type="button"
                      onClick={() => setCurrencyView("NPR")}
                      className={`px-2.5 py-1 text-xs font-bold rounded-lg transition ${
                        isNpr ? "bg-emerald-700 text-white" : "text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      NPR
                    </button>
                    <button
                      type="button"
                      onClick={() => setCurrencyView("USD")}
                      className={`px-2.5 py-1 text-xs font-bold rounded-lg transition ${
                        !isNpr ? "bg-emerald-700 text-white" : "text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      USD
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="p-5 sm:p-6 space-y-6 overflow-y-auto flex-1 text-sm text-slate-700">
            {/* Total Highlight Banner */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-black uppercase tracking-wider text-emerald-800 block">
                  Total Estimated Budget ({currentParams?.travelers || 1} Pax)
                </span>
                <span className="text-2xl font-black text-emerald-950 font-mono">
                  {currencySymbol} {total?.toLocaleString()}
                </span>
              </div>
              <div className="text-right border-l border-emerald-200 pl-4">
                <span className="text-[11px] font-bold text-emerald-700 block">Per Person</span>
                <span className="text-lg font-black text-emerald-900 font-mono">
                  {currencySymbol} {perPerson?.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Itemized Breakdown Table */}
            <div className="space-y-3">
              <h4 className="font-black text-slate-900 flex items-center gap-2">
                <FiShield className="text-emerald-700" />
                Itemized Expense Schedule
              </h4>

              <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 overflow-hidden bg-white">
                {costData.itemized?.map((item, idx) => {
                  const amount = isNpr ? item.amount_npr : item.amount_usd
                  const pct = total > 0 ? Math.round((amount / total) * 100) : 0
                  return (
                    <div key={idx} className="p-3.5 space-y-1.5 hover:bg-slate-50 transition">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-slate-900">{item.category}</span>
                            {item.is_mandatory ? (
                              <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-emerald-100 text-emerald-800 font-bold">
                                Required
                              </span>
                            ) : (
                              <span className="text-[10px] px-1.5 py-0.2 rounded-md bg-slate-100 text-slate-600 font-medium">
                                Buffer
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="font-black text-slate-900 font-mono text-sm">
                            {currencySymbol} {amount?.toLocaleString()}
                          </span>
                          <span className="text-[11px] text-slate-400 block">{pct}%</span>
                        </div>
                      </div>

                      {/* Visual progress bar */}
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-emerald-600 h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Notes & Domestic Advantage */}
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1">
              <p className="font-bold text-slate-800">💡 Transparent Pricing Disclaimer:</p>
              <p>
                Figures reflect standard seasonal market averages for certified guides, standard tea houses, and official government permits in Nepal. Personal expenses, international airfare, tipping, hot showers (200–500 NPR in high camps), and device charging are excluded.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="ny-btn ny-btn-primary px-6 py-2 text-xs font-bold rounded-xl"
            >
              Done
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
