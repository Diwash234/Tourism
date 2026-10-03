import "react-icons/fi"

/**
 * Flexible card component with header, body, footer, and hover effects.
 */
export default function Card({
  children,
  title,
  subtitle,
  actions,
  footer,
  hover = true,
  padding = true,
  className = "",
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className={`bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden transition-all duration-200 ${
        hover ? "hover:shadow-lg hover:-translate-y-0.5" : ""
      } ${onClick ? "cursor-pointer" : ""} ${className}`}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--ny-border)]">
          <div>
            {title && <h3 className="text-sm font-bold text-gray-900 dark:text-white">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-1">{actions}</div>}
        </div>
      )}
      <div className={padding ? "p-5" : ""}>{children}</div>
      {footer && (
        <div className="px-5 py-3.5 border-t border-[var(--ny-border)] bg-gray-50 dark:bg-slate-800/50">
          {footer}
        </div>
      )}
    </div>
  )
}
