import { forwardRef } from "react"

const Input = forwardRef(
  (
    {
      label,
      helperText,
      error,
      className = "",
      type = "text",
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
        <input
          ref={ref}
          type={type}
          required={required}
          className={`w-full rounded-2xl px-4 py-2.5 bg-white border border-slate-300 text-slate-900 text-xs font-medium placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all ${
            error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500/20" : ""
          } ${className}`}
          {...props}
        />
        {helperText && !error && <p className="text-[11px] text-slate-500">{helperText}</p>}
        {error && <p className="text-[11px] font-bold text-rose-600">{error}</p>}
      </div>
    )
  }
)

Input.displayName = "Input"
export default Input
