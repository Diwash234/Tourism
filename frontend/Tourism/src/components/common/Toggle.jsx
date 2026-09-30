/**
 * Accessible toggle switch component.
 */
export default function Toggle({ checked, onChange, label, description, disabled = false, size = "md", className = "" }) {
  const sizes = {
    sm: { track: "h-5 w-9", thumb: "h-3.5 w-3.5", translate: "translate-x-4" },
    md: { track: "h-6 w-11", thumb: "h-4.5 w-4.5", translate: "translate-x-5" },
    lg: { track: "h-7 w-13", thumb: "h-5.5 w-5.5", translate: "translate-x-6" },
  }

  const s = sizes[size] || sizes.md

  return (
    <label className={`flex items-center gap-3 ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"} ${className}`}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange?.(!checked)}
        className={`relative inline-flex ${s.track} items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${
          checked ? "bg-[var(--ny-green)]" : "bg-gray-300 dark:bg-slate-600"
        }`}
      >
        <span
          className={`${s.thumb} inline-block transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
            checked ? s.translate : "translate-x-0.5"
          }`}
        />
      </button>
      {(label || description) && (
        <div className="flex flex-col">
          {label && <span className="text-sm font-medium text-gray-900 dark:text-white">{label}</span>}
          {description && <span className="text-xs text-gray-500 dark:text-gray-400">{description}</span>}
        </div>
      )}
    </label>
  )
}
