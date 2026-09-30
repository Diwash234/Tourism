import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiDollarSign,
  FiX,
  FiUsers,
  FiAward,
  FiInfo,
  FiCheckCircle,
  FiHelpCircle
} from "react-icons/fi"

export default function TippingAndCurrencyGuide({
  isOpen,
  onClose,
  defaultDays = 7,
  defaultTravelers = 2
}) {
  const [days, setDays] = useState(defaultDays)
  const [travelers, setTravelers] = useState(defaultTravelers)
  const [guideCount, setGuideCount] = useState(1)
  const [porterCount, setPorterCount] = useState(1)

  if (!isOpen) return null

  // Industry norm in Nepal:
  // Guide: ~NPR 1,200 to 1,500 per day from the whole group
  // Porter: ~NPR 800 to 1,000 per day from the whole group
  const guideTotalNpr = guideCount * days * 1300
  const porterTotalNpr = porterCount * days * 900
  const combinedTotalNpr = guideTotalNpr + porterTotalNpr
  const perTravelerNpr = Math.round(combinedTotalNpr / Math.max(1, travelers))
  const perTravelerUsd = Math.round(perTravelerNpr / 133)

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden my-auto max-h-[90vh] flex flex-col"
        >
          {/* Header */}
          <div className="p-5 sm:p-6 bg-slate-900 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <FiDollarSign size={22} />
              </div>
              <div>
                <h3 className="text-lg font-black leading-tight">Tipping Etiquette & Cash Guide</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Clear, honest Nepal standards for guides, porters, tea houses, and cash handling
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition"
              aria-label="Close tipping guide"
            >
              <FiX size={20} />
            </button>
          </div>

          {/* Interactive Calculator Controls */}
          <div className="p-4 bg-slate-50 border-b border-slate-200 space-y-3 shrink-0">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
              Customize Your Trek Parameters:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="bg-white p-2 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 font-bold block">Trek Days</span>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={days}
                  onChange={(e) => setDays(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full font-black text-slate-900 font-mono text-sm focus:outline-none"
                />
              </div>

              <div className="bg-white p-2 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 font-bold block">Travelers</span>
                <input
                  type="number"
                  min="1"
                  max="12"
                  value={travelers}
                  onChange={(e) => setTravelers(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full font-black text-slate-900 font-mono text-sm focus:outline-none"
                />
              </div>

              <div className="bg-white p-2 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 font-bold block">Mountain Guides</span>
                <input
                  type="number"
                  min="0"
                  max="4"
                  value={guideCount}
                  onChange={(e) => setGuideCount(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full font-black text-slate-900 font-mono text-sm focus:outline-none"
                />
              </div>

              <div className="bg-white p-2 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] text-slate-500 font-bold block">Porters</span>
                <input
                  type="number"
                  min="0"
                  max="6"
                  value={porterCount}
                  onChange={(e) => setPorterCount(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full font-black text-slate-900 font-mono text-sm focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Body Content */}
          <div className="p-5 sm:p-6 space-y-5 overflow-y-auto flex-1 text-sm text-slate-700">
            {/* Calculated Recommendation Banner */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-amber-50 border border-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 block">
                  Recommended Tip Pool ({days} Days · {travelers} Travelers)
                </span>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="text-2xl font-black text-emerald-950 font-mono">
                    NPR {combinedTotalNpr.toLocaleString()}
                  </span>
                  <span className="text-xs text-slate-500 font-semibold">
                    (≈ ${Math.round(combinedTotalNpr / 133)} USD)
                  </span>
                </div>
              </div>

              <div className="sm:text-right border-t sm:border-t-0 sm:border-l border-emerald-200 pt-2 sm:pt-0 sm:pl-4">
                <span className="text-[10px] font-bold text-slate-500 uppercase block">Share Per Traveler</span>
                <span className="text-lg font-black text-emerald-900 font-mono">
                  NPR {perTravelerNpr.toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 block">≈ ${perTravelerUsd} USD</span>
              </div>
            </div>

            {/* Individual Envelope Recommendations */}
            <div className="grid sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 bg-white rounded-xl border border-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">Guide Envelope</span>
                  <span className="font-black text-emerald-800 font-mono">
                    NPR {guideTotalNpr.toLocaleString()}
                  </span>
                </div>
                <p className="text-slate-500 text-[11px]">
                  Based on standard NPR 1,200–1,500/day for the group. Hand over in a clean envelope at the farewell dinner.
                </p>
              </div>

              <div className="p-3.5 bg-white rounded-xl border border-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">Porter Envelope</span>
                  <span className="font-black text-emerald-800 font-mono">
                    NPR {porterTotalNpr.toLocaleString()}
                  </span>
                </div>
                <p className="text-slate-500 text-[11px]">
                  Based on standard NPR 800–1,000/day per porter. Hand directly to your porter with two hands in person.
                </p>
              </div>
            </div>

            {/* Cultural Tipping Norms */}
            <div className="space-y-2 text-xs">
              <h4 className="font-black text-slate-900 flex items-center gap-1.5">
                <FiAward className="text-amber-600" />
                How Tipping Ceremonies Work in Nepal
              </h4>
              <ul className="space-y-1.5 text-slate-600 bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
                <li className="flex items-start gap-1.5">
                  <span className="text-emerald-700 font-bold">•</span>
                  <span><b>The Farewell Dinner Ceremony:</b> On the final evening of the trek (in Lukla, Pokhara, or Syabrubesi), the trekking team gathers for a celebratory dinner. It is customary to hand the tips in sealed envelopes along with words of gratitude.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-emerald-700 font-bold">•</span>
                  <span><b>Hand with Both Hands:</b> In Nepali culture, handing money or gifts with both hands (or touching your right elbow with your left hand) signifies deep respect.</span>
                </li>
                <li className="flex items-start gap-1.5">
                  <span className="text-emerald-700 font-bold">•</span>
                  <span><b>City Restaurants & Drivers:</b> Casual city eateries don't expect tips. Mid-range restaurants often include 10% service charge on the bill. For private day drivers in Kathmandu/Pokhara, NPR 500–1,000 per day is customary.</span>
                </li>
              </ul>
            </div>

            {/* ATM & Cash Realities */}
            <div className="p-3.5 bg-amber-50/70 rounded-2xl border border-amber-200 text-xs space-y-1.5">
              <span className="font-bold text-amber-950 block">💳 Cash vs ATM Realities:</span>
              <p className="text-amber-900 leading-relaxed text-[11px]">
                Mountain villages are 100% cash-based. The ATMs in Namche Bazaar and Jomsom frequently run out of cash during peak trekking seasons or lose electricity. Withdraw all required Nepali Rupees in Kathmandu or Pokhara before departing.
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
              Understood
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
