/**
 * Reusable loading spinner with accessible label.
 */
export default function LoadingSpinner({ size = "md", label = "Loading..." }) {
  const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-2",
    lg: "h-12 w-12 border-3",
  }

  return (
    <div className="flex items-center justify-center" role="status" aria-live="polite">
      <span
        className={`${sizeClasses[size] || sizeClasses.md} animate-spin rounded-full border-[var(--ny-border)] border-t-[var(--ny-green)]`}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  )
}
