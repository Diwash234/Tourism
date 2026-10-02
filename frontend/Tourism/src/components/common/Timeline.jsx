import { FiCheck, FiCircle } from "react-icons/fi"

/**
 * Timeline component for displaying chronological events or itinerary steps.
 */
export default function Timeline({ items, className = "" }) {
  return (
    <div className={`relative ${className}`}>
      {items.map((item, i) => (
        <div key={i} className="flex gap-4 pb-6 last:pb-0">
          <div className="flex flex-col items-center">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
              item.completed
                ? "bg-[var(--ny-green)] text-white"
                : item.active
                ? "bg-[var(--ny-soft-green)] text-[var(--ny-green)] ring-2 ring-[var(--ny-green)]"
                : "bg-gray-100 dark:bg-slate-700 text-gray-400"
            }`}>
              {item.completed ? <FiCheck size={14} /> : item.icon || <FiCircle size={14} />}
            </div>
            {i < items.length - 1 && (
              <div className={`w-0.5 flex-1 mt-1 ${item.completed ? "bg-[var(--ny-green)]" : "bg-gray-200 dark:bg-slate-700"}`} />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-semibold ${
              item.completed ? "text-[var(--ny-green)]" : item.active ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400"
            }`}>
              {item.title}
            </p>
            {item.description && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.description}</p>
            )}
            {item.time && (
              <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">{item.time}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
