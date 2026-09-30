/**
 * Section header with title, subtitle, and optional action.
 */
export default function SectionHeader({ title, subtitle, action, className = "" }) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6 ${className}`}>
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">{title}</h2>
        {subtitle && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  )
}
