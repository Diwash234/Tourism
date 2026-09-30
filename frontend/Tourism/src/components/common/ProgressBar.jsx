/**
 * Animated progress bar with label, percentage, and color variants.
 */
export default function ProgressBar({ value, max = 100, label, showPercentage = true, size = "md", color = "primary", animated = true }) {
  const percentage = Math.min(Math.round((value / max) * 100), 100)

  const sizes = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  }

  const colors = {
    primary: "bg-[var(--ny-green)]",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-red-500",
    info: "bg-blue-500",
  }

  return (
    <div className="w-full">
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{label}</span>}
          {showPercentage && <span className="text-xs font-bold text-gray-700 dark:text-gray-300">{percentage}%</span>}
        </div>
      )}
      <div className={`w-full bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden ${sizes[size] || sizes.md}`}>
        <div
          className={`${colors[color] || colors.primary} rounded-full transition-all duration-500 ease-out ${animated ? "relative overflow-hidden" : ""}`}
          style={{ width: `${percentage}%` }}
        >
          {animated && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          )}
        </div>
      </div>
    </div>
  )
}
