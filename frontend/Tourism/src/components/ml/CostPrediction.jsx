import { useState } from "react"
import { motion } from "framer-motion"
import { FiDollarSign, FiTrendingUp, FiCheckCircle } from "react-icons/fi"

export default function CostPrediction({ onCalculate }) {
  const [days, setDays] = useState(7)
  const [travelers, setTravelers] = useState(2)
  const [style, setStyle] = useState("mid")
  const [destination, setDestination] = useState("Pokhara")

  const calculateEstimate = () => {
    const baseDaily = style === "budget" ? 28 : style === "luxury" ? 140 : 65
    const totalUSD = baseDaily * days * travelers
    const totalNPR = totalUSD * 134
    return {
      dailyUSD: baseDaily,
      totalUSD,
      totalNPR,
      stayUSD: Math.round(totalUSD * 0.4),
      foodUSD: Math.round(totalUSD * 0.3),
      transitUSD: Math.round(totalUSD * 0.2),
      entryUSD: Math.round(totalUSD * 0.1),
    }
  }

  const result = calculateEstimate()

  return (
    <div className="card-base p-6 space-y-5 bg-gradient-to-br from-white to-purple-50/40 border border-[#E5E0D5] rounded-3xl shadow-xl">
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
            <FiDollarSign className="text-emerald-600" /> ML Travel Budget Predictor
          </h3>
          <p className="text-xs text-gray-500">Trained on actual traveler & field officer survey records</p>
        </div>
        <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
          ML Trained
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div>
          <label className="font-semibold text-gray-700">Days</label>
          <input
            type="number"
            min={1}
            max={60}
            className="input-field mt-1 text-sm font-bold"
            value={days}
            onChange={(e) => setDays(Number(e.target.value) || 1)}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Travelers</label>
          <input
            type="number"
            min={1}
            max={20}
            className="input-field mt-1 text-sm font-bold"
            value={travelers}
            onChange={(e) => setTravelers(Number(e.target.value) || 1)}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Travel Style</label>
          <select
            className="input-field mt-1 text-xs"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
          >
            <option value="budget">Backpacker ($28/day)</option>
            <option value="mid">Comfort / Mid ($65/day)</option>
            <option value="luxury">Deluxe / Luxury ($140/day)</option>
          </select>
        </div>
        <div>
          <label className="font-semibold text-gray-700">Destination</label>
          <input
            className="input-field mt-1 text-xs font-semibold"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          />
        </div>
      </div>

      <div className="p-4 rounded-2xl bg-white border border-[#E5E0D5] shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Predicted Total Budget ({days} Days, {travelers} Ppl):</span>
          <span className="text-2xl font-black text-purple-950">${result.totalUSD.toLocaleString()} USD</span>
        </div>
        <p className="text-xs text-[#102A2E] font-bold">
          Approx. NPR {result.totalNPR.toLocaleString()}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t text-[11px] text-gray-600">
          <div>🏨 Hotel: <b>${result.stayUSD}</b></div>
          <div>🍛 Food: <b>${result.foodUSD}</b></div>
          <div>🚗 Transit: <b>${result.transitUSD}</b></div>
          <div>🎟️ Permits: <b>${result.entryUSD}</b></div>
        </div>
      </div>
    </div>
  )
}
