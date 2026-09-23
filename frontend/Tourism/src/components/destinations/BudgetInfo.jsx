import { FiDollarSign } from "react-icons/fi"

export default function BudgetInfo({ budgetEst, entryFee = 0 }) {
  const dailyCost = budgetEst?.estimated_daily_budget || 45
  const totalCost = budgetEst?.estimated_trip_budget || (dailyCost * 3)

  return (
    <div className="card-base p-6 shadow-xl border border-[#E5E0D5] rounded-3xl bg-gradient-to-br from-white to-purple-50/50 space-y-4">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
          <FiDollarSign className="text-emerald-600" /> Travel Budget Breakdown
        </h3>
        <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-extrabold uppercase">
          ML Estimated
        </span>
      </div>

      <div>
        <p className="text-xs text-gray-500">Estimated Daily Budget</p>
        <p className="text-3xl font-black text-purple-950">${dailyCost} <span className="text-xs font-semibold text-gray-500">USD / day</span></p>
        <p className="text-xs text-[#102A2E] font-bold mt-1">Approx. NPR {(dailyCost * 134).toLocaleString()}</p>
      </div>

      <div className="p-3.5 rounded-2xl bg-white border border-[#E5E0D5] text-xs space-y-2 text-gray-700">
        <div className="flex justify-between">
          <span>🏨 Hotel / Night:</span>
          <b>${budgetEst?.accommodation_per_night || 20}</b>
        </div>
        <div className="flex justify-between">
          <span>🍛 Food / Meals:</span>
          <b>${budgetEst?.food_cost_per_day || 15}</b>
        </div>
        <div className="flex justify-between">
          <span>🚗 Transit:</span>
          <b>${budgetEst?.transport_cost || 10}</b>
        </div>
        <div className="flex justify-between">
          <span>🎟️ Entry Fee:</span>
          <b>NPR {entryFee || 0}</b>
        </div>
      </div>
    </div>
  )
}
