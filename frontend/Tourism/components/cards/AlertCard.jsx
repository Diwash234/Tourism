import { FiAlertTriangle } from "react-icons/fi"
import { RISK_LEVELS } from "../../utils/constants"

const AlertCard = ({ alert }) => {
  const level = RISK_LEVELS[alert.level?.toUpperCase()] || RISK_LEVELS.MODERATE
  return (
    <div className="card-base p-4 flex gap-3 items-start">
      <div className={`p-2 rounded-full ${level.color}`}>
        <FiAlertTriangle />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <h4 className="font-semibold text-sm">{alert.title}</h4>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${level.color}`}>
            {level.label}
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">{alert.description}</p>
        <p className="text-xs text-gray-400 mt-2">{alert.location} · {alert.date}</p>
      </div>
    </div>
  )
}

export default AlertCard