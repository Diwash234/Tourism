import { FiMapPin, FiClock, FiDollarSign, FiActivity, FiCalendar, FiUsers } from "react-icons/fi"
import Badge from "../common/Badge"

/**
 * Destination information panel with key details,
 * best time to visit, and quick facts.
 */
export default function DestinationInfo({ destination }) {
  const infoItems = [
    { icon: FiMapPin, label: "Location", value: `${destination?.district || ""}, ${destination?.province || "Nepal"}` },
    { icon: FiClock, label: "Best Time", value: destination?.best_season || "Year-round" },
    { icon: FiDollarSign, label: "Budget", value: destination?.budget_level || "Moderate" },
    { icon: FiActivity, label: "Activity", value: destination?.category || "Sightseeing" },
    { icon: FiCalendar, label: "Duration", value: destination?.recommended_duration || "1-2 days" },
    { icon: FiUsers, label: "Group Size", value: destination?.group_size || "Any" },
  ].filter(item => item.value)

  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5">
      <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-4">Quick Facts</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {infoItems.map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-start gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--ny-soft-green)] text-[var(--ny-green)] shrink-0">
              <Icon size={16} />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">{label}</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {destination?.tags?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[var(--ny-border)]">
          <p className="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">Tags</p>
          <div className="flex flex-wrap gap-1.5">
            {destination.tags.map((tag) => (
              <Badge key={tag} variant="primary" size="sm">{tag}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
