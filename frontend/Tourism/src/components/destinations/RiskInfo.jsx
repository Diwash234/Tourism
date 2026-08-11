import { FiShield, FiAlertTriangle } from "react-icons/fi"

export default function RiskInfo({ riskAnalysis, alertTitle }) {
  const score = riskAnalysis?.tourism_risk_index || 18
  const category = (riskAnalysis?.risk_category || "LOW").toUpperCase()
  const color = category === "LOW" ? "bg-emerald-100 text-emerald-800" : category === "MODERATE" ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800"

  return (
    <div className="card-base p-6 shadow-xl border border-purple-100 rounded-3xl bg-gradient-to-br from-white to-rose-50/40 space-y-4">
      <div className="flex items-center justify-between border-b pb-3">
        <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
          <FiShield className="text-purple-600" /> Safety & Risk Score
        </h3>
        <span className={`px-3 py-1 rounded-full text-xs font-bold ${color}`}>
          {category} Risk
        </span>
      </div>

      <div className="space-y-2 text-xs text-gray-700">
        <div className="flex justify-between">
          <span>Tourism Risk Index:</span>
          <b className="text-purple-900">{score} / 100</b>
        </div>
        <div className="flex justify-between">
          <span>Natural Hazard Level:</span>
          <b className="text-emerald-700">{score < 40 ? "Safe Trail" : "Advisory Active"}</b>
        </div>
      </div>

      <p className="text-xs text-gray-500 bg-white p-3 rounded-xl border border-gray-100">
        {alertTitle || "No active natural hazard alerts. Standard trekking guidance applies."}
      </p>
    </div>
  )
}
