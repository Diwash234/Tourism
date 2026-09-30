import { FiAlertTriangle, FiShield, FiPhone, FiMapPin, FiCheck } from "react-icons/fi"
import { useTranslation } from "../../hooks/useTranslation"
import Badge from "../common/Badge"

/**
 * Safety information panel for a destination.
 * Shows risk level, emergency contacts, and safety tips.
 */
export default function DestinationSafety({ destination, safetyInfo }) {
  const { t } = useTranslation()

  const riskLevel = safetyInfo?.risk_level || destination?.risk_level || "low"
  const emergencyContacts = safetyInfo?.emergency_contacts || [
    { name: "Police", number: "100" },
    { name: "Ambulance", number: "102" },
    { name: "Tourist Police", number: "1144" },
  ]
  const safetyTips = safetyInfo?.safety_tips || [
    "Keep copies of important documents",
    "Avoid traveling alone at night",
    "Stay on marked trails",
    "Carry a basic first aid kit",
    "Inform someone of your itinerary",
  ]

  const riskColors = {
    low: "success",
    moderate: "warning",
    medium: "warning",
    high: "danger",
    critical: "danger",
  }

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FiShield size={16} className="text-[var(--ny-green)]" />
          Safety Information
        </h3>
        <Badge variant={riskColors[riskLevel] || "default"} size="sm">
          {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk
        </Badge>
      </div>

      {/* Emergency Contacts */}
      <div className="mb-4">
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
          Emergency Contacts
        </p>
        <div className="space-y-2">
          {emergencyContacts.map((contact, i) => (
            <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-gray-50 dark:bg-slate-700/50">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 dark:bg-red-950/30 text-red-500">
                  <FiPhone size={14} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-900 dark:text-white">{contact.name}</p>
                  <p className="text-[10px] text-gray-400">{contact.number}</p>
                </div>
              </div>
              <a
                href={`tel:${contact.number}`}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-[var(--ny-green)] text-white hover:bg-[var(--ny-emerald)] transition-colors"
              >
                Call
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Safety Tips */}
      <div>
        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
          Safety Tips
        </p>
        <ul className="space-y-2">
          {safetyTips.map((tip, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400">
              <FiCheck size={14} className="text-[var(--ny-green)] shrink-0 mt-0.5" />
              {tip}
            </li>
          ))}
        </ul>
      </div>

      {/* Nearest Hospital */}
      {safetyInfo?.nearest_hospital && (
        <div className="mt-4 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900">
          <div className="flex items-start gap-2.5">
            <FiMapPin size={16} className="text-blue-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-blue-800 dark:text-blue-200">Nearest Hospital</p>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">{safetyInfo.nearest_hospital.name}</p>
              <p className="text-[10px] text-blue-500 dark:text-blue-500 mt-0.5">
                {safetyInfo.nearest_hospital.distance_km?.toFixed(1)} km away
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
