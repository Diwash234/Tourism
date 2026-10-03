import { FiInbox, FiSearch, FiMapPin, FiHeart, FiCalendar } from "react-icons/fi"

/**
 * Empty state component with icon, title, description, and optional action.
 */
export default function EmptyState({
  icon = "inbox",
  title = "Nothing here yet",
  description = "There's nothing to display at the moment.",
  actionLabel,
  onAction,
  className = "",
}) {
  const icons = {
    inbox: <FiInbox size={48} />,
    search: <FiSearch size={48} />,
    location: <FiMapPin size={48} />,
    heart: <FiHeart size={48} />,
    calendar: <FiCalendar size={48} />,
  }

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}>
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--ny-soft-green)] text-[var(--ny-green)] mb-4">
        {icons[icon] || icons.inbox}
      </div>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-4">{description}</p>
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--ny-green)] text-white text-sm font-semibold hover:bg-[var(--ny-emerald)] transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
