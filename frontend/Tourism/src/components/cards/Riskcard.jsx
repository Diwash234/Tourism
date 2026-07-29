import { FiShield, FiAlertTriangle } from "react-icons/fi"
import { RISK_LEVELS } from "../../utils/constants"

/**
 * RiskCard
 * props: { title, level: "LOW"|"MODERATE"|"HIGH", description, value }
 * `value` is an optional 0-100 safety score shown as a ring/number.
 */
const RiskCard = ({ title, level = "LOW", description, value }) => {
  const risk = RISK_LEVELS[level] || RISK_LEVELS.LOW

  return (
    <div className="card-base p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-xl ${risk.color}`}>
            {level === "HIGH" ? <FiAlertTriangle size={18} /> : <FiShield size={18} />}
          </div>
          <h4 className="font-semibold text-dark">{title}</h4>
        </div>
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${risk.color}`}>
          {risk.label}
        </span>
      </div>

      {value != null && (
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
          <div
            className="h-full bg-himalaya-500 rounded-full transition-all duration-500"
            style={{ width: `${value}%` }}
          />
        </div>
      )}

      {description && <p className="text-sm text-gray-500">{description}</p>}
    </div>
  )
}

export default RiskCard