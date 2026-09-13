import { forwardRef } from "react"

const Select = forwardRef(
  (
    {
      label,
      helperText,
      error,
      options = [],
      children,
      className = "",
      required = false,
      ...props
    },
    ref
  ) => {
    return (
      <div className="space-y-1 text-xs">
        {label && (
          <label className="block font-bold text-slate-700">
            {label} {required && <span className="text-rose-500">*</span>}
          </label>
        )}
        <select
          ref={ref}
          required={required}
          className={`w-full rounded-2xl px-4 py-2.5 bg-white border border-slate-300 text-slate-900 text-xs font-medium focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all ${
            error ? "border-rose-500" : ""
          } ${className}`}
          {...props}
        >
          {children
            ? children
            : options.map((opt) => (
                <option key={opt.value || opt.id || opt} value={opt.value || opt.id || opt}>
                  {opt.label || opt.name || opt}
                </option>
              ))}
        </select>
        {helperText && !error && <p className="text-[11px] text-slate-500">{helperText}</p>}
        {error && <p className="text-[11px] font-bold text-rose-600">{error}</p>}
      </div>
    )
  }
)

Select.displayName = "Select"
export default Select
