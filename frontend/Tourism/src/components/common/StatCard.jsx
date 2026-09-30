import { FiTrendingUp, FiTrendingDown } from "react-icons/fi"

/**
 * Statistics card with icon, value, label, and trend indicator.
 */
export default function StatCard({ icon, label, value, trend, trendValue, color = "green", className = "" }) {
  const colors = {
    green: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]",
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-400",
    amber: "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400",
    red: "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-950/30 dark:text-purple-400",
  }

  return (
    <div className={`bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5 transition-all hover:shadow-md ${className}`}>
      <div className="flex items-start justify-between">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${colors[color] || colors.green}`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-semibold ${
            trend === "up" ? "text-emerald-600" : "text-red-500"
          }`}>
            {trend === "up" ? <FiTrendingUp size={14} /> : <FiTrendingDown size={14} />}
            {trendValue}
          </div>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{label}</p>
      </div>
    </div>
  )
}
