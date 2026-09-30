import { FiUser } from "react-icons/fi"

/**
 * Avatar component with image fallback, status indicator, and size variants.
 */
export default function Avatar({ src, name, size = "md", status, className = "" }) {
  const sizes = {
    xs: "h-6 w-6 text-[10px]",
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 text-base",
    xl: "h-16 w-16 text-lg",
  }

  const statusSizes = {
    xs: "h-1.5 w-1.5",
    sm: "h-2 w-2",
    md: "h-2.5 w-2.5",
    lg: "h-3 w-3",
    xl: "h-4 w-4",
  }

  const statusColors = {
    online: "bg-emerald-500",
    offline: "bg-gray-400",
    away: "bg-amber-500",
    busy: "bg-red-500",
  }

  const getInitials = (name) => {
    if (!name) return "?"
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className={`relative inline-flex ${className}`}>
      {src ? (
        <img
          src={src}
          alt={name || "Avatar"}
          className={`${sizes[size] || sizes.md} rounded-full object-cover ring-2 ring-white dark:ring-slate-800`}
        />
      ) : (
        <div className={`${sizes[size] || sizes.md} rounded-full bg-[var(--ny-green)] text-white flex items-center justify-center font-bold ring-2 ring-white dark:ring-slate-800`}>
          {name ? getInitials(name) : <FiUser size={16} />}
        </div>
      )}
      {status && (
        <span className={`absolute bottom-0 right-0 ${statusSizes[size] || statusSizes.md} rounded-full border-2 border-white dark:border-slate-800 ${statusColors[status] || statusColors.offline}`} />
      )}
    </div>
  )
}
