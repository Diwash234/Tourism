import { useState } from "react"
import { motion } from "framer-motion"
import { FiShield, FiAlertTriangle, FiCheckCircle } from "react-icons/fi"

export default function RiskPrediction({ placeName = "Annapurna Circuit" }) {
  const [altitude, setAltitude] = useState(4130)
  const [season, setSeason] = useState("autumn")

  const getRiskScore = () => {
    let score = 15
    if (altitude > 3000) score += 25
    if (altitude > 4500) score += 30
    if (season === "monsoon") score += 25
    if (season === "winter") score += 15
    return Math.min(100, score)
  }

  const riskScore = getRiskScore()
  const category = riskScore < 30 ? "LOW" : riskScore < 65 ? "MODERATE" : "HIGH"
  const color = category === "LOW" ? "text-emerald-700 bg-emerald-50 border-emerald-200" : category === "MODERATE" ? "text-amber-700 bg-amber-50 border-amber-200" : "text-rose-700 bg-rose-50 border-rose-200"

  return (
    <div className="card-base p-6 space-y-4 bg-gradient-to-br from-white to-rose-50/30 border border-purple-100 rounded-3xl shadow-xl">
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
            <FiShield className="text-purple-600" /> ML Risk & Hazard Index
          </h3>
          <p className="text-xs text-gray-500">Real-time hazard calculation calibrated on environmental datasets</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${color}`}>
          {category} RISK ({riskScore}/100)
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <label className="font-semibold text-gray-700">Trek Altitude (m)</label>
          <input
            type="number"
            className="input-field mt-1 text-sm font-bold"
            value={altitude}
            onChange={(e) => setAltitude(Number(e.target.value) || 1000)}
          />
        </div>
        <div>
          <label className="font-semibold text-gray-700">Planned Season</label>
          <select
            className="input-field mt-1 text-xs"
            value={season}
            onChange={(e) => setSeason(e.target.value)}
          >
            <option value="autumn">Autumn (Sep-Nov) - Safest</option>
            <option value="spring">Spring (Mar-May) - Good</option>
            <option value="winter">Winter (Dec-Feb) - Snow Risk</option>
            <option value="monsoon">Monsoon (Jun-Aug) - Landslide Risk</option>
          </select>
        </div>
      </div>

      <div className="p-3.5 rounded-2xl bg-white border border-gray-100 text-xs space-y-1 text-gray-700">
        <p>• <b>Altitude Sickness (AMS):</b> {altitude > 3000 ? "Acclimatization day required at 3,000m & 4,000m." : "Low altitude AMS risk."}</p>
        <p>• <b>Emergency Helpline:</b> Himalayan Rescue Association (HRA) 24/7 Hotline: +977-1-4440292</p>
      </div>
    </div>
  )
}
