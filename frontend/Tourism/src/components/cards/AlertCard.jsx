import { FiAlertTriangle, FiCheckCircle, FiExternalLink, FiMapPin } from "react-icons/fi"
import { RISK_LEVELS } from "../../utils/constants"

const AlertCard = ({ alert }) => {
  const severity = (alert.severity || alert.level || "moderate").toUpperCase()
  const level = RISK_LEVELS[severity] || RISK_LEVELS.MODERATE
  const location = [alert.city, alert.municipality, alert.district, alert.province].filter(Boolean).join(", ")
  return <article className="card-base p-4 flex gap-3 items-start">
    <div className={`p-2 rounded-full ${level.color}`}><FiAlertTriangle /></div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between gap-2"><h4 className="font-semibold text-sm">{alert.title}</h4><span className={`text-xs font-medium px-2 py-0.5 rounded-full ${level.color}`}>{level.label}</span></div>
      <p className="text-sm text-gray-500 mt-1">{alert.description}</p>
      <div className="flex flex-wrap gap-2 text-[11px] text-gray-400 mt-2">
        {location && <span><FiMapPin className="inline" /> {location}</span>}
        {alert.distance_km != null && <span>{alert.distance_km} km from you</span>}
        {alert.radius_km && <span>{alert.radius_km} km alert zone</span>}
      </div>
      {(alert.source || alert.source_url) && <div className="mt-2 text-[11px]">{alert.is_verified && <span className="text-emerald-700 font-bold mr-2"><FiCheckCircle className="inline" /> Verified</span>}{alert.source_url ? <a className="text-blue-700 hover:underline" href={alert.source_url} target="_blank" rel="noreferrer">{alert.source || "Source"} <FiExternalLink className="inline" /></a> : <span className="text-gray-400">{alert.source}</span>}</div>}
    </div>
  </article>
}

export default AlertCard
