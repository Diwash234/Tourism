import { forwardRef } from "react"
import { FiLoader } from "react-icons/fi"

const VARIANTS = {
  primary: "bg-[#0B3D91] hover:bg-blue-900 text-white shadow-sm focus:ring-blue-500",
  secondary: "bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200 focus:ring-slate-400",
  emerald: "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm focus:ring-emerald-500",
  amber: "bg-amber-400 hover:bg-amber-500 text-slate-950 font-black shadow-sm focus:ring-amber-500",
  destructive: "bg-rose-600 hover:bg-rose-700 text-white shadow-sm focus:ring-rose-500",
  ghost: "bg-transparent hover:bg-slate-100 text-slate-700 focus:ring-slate-400",
  outline: "bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 focus:ring-blue-500",
}

const SIZES = {
  sm: "px-3 py-1.5 text-xs rounded-xl",
  md: "px-4 py-2 text-xs font-bold rounded-2xl",
  lg: "px-6 py-3 text-sm font-extrabold rounded-2xl",
}

const Button = forwardRef(
  (
    {
      children,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled = false,
      className = "",
      icon: Icon,
      type = "button",
      ...props
    },
    ref
  ) => {
    const variantStyle = VARIANTS[variant] || VARIANTS.primary
    const sizeStyle = SIZES[size] || SIZES.md

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center gap-2 font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${variantStyle} ${sizeStyle} ${className}`}
        {...props}
      >
        {isLoading ? (
          <FiLoader className="animate-spin" size={size === "sm" ? 12 : 16} />
        ) : Icon ? (
          <Icon size={size === "sm" ? 13 : 16} />
        ) : null}
        <span>{children}</span>
      </button>
    )
  }
)

Button.displayName = "Button"
export default Button
