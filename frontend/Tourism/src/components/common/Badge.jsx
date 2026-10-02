/**
 * Flexible badge component with multiple variants and sizes.
 */
export default function Badge({ children, variant = "default", size = "md", className = "", dot = false }) {
  const variants = {
    default: "bg-gray-100 text-gray-700 dark:bg-slate-700 dark:text-gray-300",
    primary: "bg-[var(--ny-soft-green)] text-[var(--ny-green)]",
    success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
    warning: "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
    danger: "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
    info: "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
    outline: "border border-[var(--ny-border)] text-[var(--ny-text-secondary)]",
  }

  const sizes = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm",
  }

  const dotColors = {
    default: "bg-gray-400",
    primary: "bg-[var(--ny-green)]",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-red-500",
    info: "bg-blue-500",
  }

  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full ${variants[variant] || variants.default} ${sizes[size] || sizes.md} ${className}`}>
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotColors[variant] || dotColors.default}`} />}
      {children}
    </span>
  )
}
