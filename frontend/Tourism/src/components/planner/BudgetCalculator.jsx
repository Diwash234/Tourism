import { useState, useMemo } from "react"
import { FiDollarSign, FiCalendar, FiUsers, FiTrendingUp, FiInfo } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import { TRAVEL_MODES, DURATION_PRESETS } from "../../utils/constants"

/**
 * Advanced budget calculator with:
 * - Travel mode selection
 * - Duration presets
 * - Accommodation type
 * - Daily expense breakdown
 * - Visual budget distribution
 */
export default function BudgetCalculator() {
  const { t } = useTranslation()
  const [mode, setMode] = useState("flight")
  const [days, setDays] = useState(7)
  const [travelers, setTravelers] = useState(2)
  const [accommodation, setAccommodation] = useState("mid")
  const [showBreakdown, setShowBreakdown] = useState(false)

  const rates = useMemo(() => ({
    flight: { transport: 15000, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
    bus: { transport: 3000, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
    car: { transport: 8000, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
    train: { transport: 5000, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
    bike: { transport: 2000, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
    walking: { transport: 0, accommodation: { budget: 1500, mid: 3500, luxury: 8000 }, food: 1200, activities: 2000, misc: 800 },
  }), [])

  const breakdown = useMemo(() => {
    const r = rates[mode] || rates.flight
    const acc = r.accommodation[accommodation] || r.accommodation.mid
    const transport = r.transport
    const accTotal = acc * days
    const foodTotal = r.food * days * travelers
    const activitiesTotal = r.activities * days * travelers
    const miscTotal = r.misc * days * travelers
    const total = transport + accTotal + foodTotal + activitiesTotal + miscTotal
    return { transport, accTotal, foodTotal, activitiesTotal, miscTotal, total }
  }, [mode, days, travelers, accommodation, rates])

  const distribution = useMemo(() => {
    const items = [
      { label: "Transport", value: breakdown.transport, color: "bg-blue-500" },
      { label: "Accommodation", value: breakdown.accTotal, color: "bg-emerald-500" },
      { label: "Food", value: breakdown.foodTotal, color: "bg-amber-500" },
      { label: "Activities", value: breakdown.activitiesTotal, color: "bg-purple-500" },
      { label: "Miscellaneous", value: breakdown.miscTotal, color: "bg-gray-400" },
    ]
    return items.map(item => ({
      ...item,
      percentage: breakdown.total > 0 ? Math.round((item.value / breakdown.total) * 100) : 0,
    }))
  }, [breakdown])

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FiDollarSign size={16} className="text-[var(--ny-green)]" />
          Budget Calculator
        </h3>

        {/* Travel Mode */}
        <div className="mb-4">
          <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-2">Travel Mode</label>
          <div className="flex flex-wrap gap-2">
            {TRAVEL_MODES.map(m => (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={`px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${
                  mode === m.value
                    ? "bg-[var(--ny-green)] text-white"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Duration Presets */}
        <div className="mb-4">
          <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-2">
            <FiCalendar size={12} className="inline mr-1" />
            Trip Duration
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATION_PRESETS.map(p => (
              <button
                key={p.days}
                type="button"
                onClick={() => setDays(p.days)}
                className={`px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${
                  days === p.days
                    ? "bg-[var(--ny-green)] text-white"
                    : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Travelers & Accommodation */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">
              <FiUsers size={12} className="inline mr-1" />
              Travelers
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={travelers}
              onChange={(e) => setTravelers(Number(e.target.value))}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 block mb-1.5">Accommodation</label>
            <select
              value={accommodation}
              onChange={(e) => setAccommodation(e.target.value)}
              className="w-full text-sm rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="budget">Budget (Hostel/Guesthouse)</option>
              <option value="mid">Mid-range (3-star Hotel)</option>
              <option value="luxury">Luxury (4-5 star Hotel)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {breakdown.total > 0 && (
        <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">Estimated Budget</h3>
            <button
              type="button"
              onClick={() => setShowBreakdown(v => !v)}
              className="text-xs text-[var(--ny-green)] font-semibold hover:underline"
            >
              {showBreakdown ? "Hide" : "Show"} Breakdown
            </button>
          </div>

          <div className="text-center mb-6">
            <p className="text-4xl font-bold text-[var(--ny-green)]">NPR {breakdown.total.toLocaleString()}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {days} days × {travelers} travelers
            </p>
          </div>

          {/* Distribution Bar */}
          <div className="h-4 rounded-full overflow-hidden flex mb-4">
            {distribution.map((item, i) => (
              <div
                key={i}
                className={`${item.color} transition-all duration-500`}
                style={{ width: `${item.percentage}%` }}
                title={`${item.label}: ${item.percentage}%`}
              />
            ))}
          </div>

          {/* Breakdown */}
          {showBreakdown && (
            <div className="space-y-2">
              {distribution.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-slate-700 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className={`h-3 w-3 rounded-full ${item.color}`} />
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{item.label}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-bold text-gray-900 dark:text-white">NPR {item.value.toLocaleString()}</p>
                    <p className="text-[10px] text-gray-400">{item.percentage}%</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Info Note */}
          <div className="mt-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900">
            <p className="text-[10px] text-amber-700 dark:text-amber-400 flex items-start gap-1.5">
              <FiInfo size={12} className="shrink-0 mt-0.5" />
              This is a rough estimate. Actual costs vary based on season, availability, and personal preferences. Always research current prices before traveling.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
