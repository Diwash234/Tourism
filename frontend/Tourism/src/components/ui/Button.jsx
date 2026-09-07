import { forwardRef } from "react"
import { FiLoader } from "react-icons/fi"

const VARIANTS = {
  primary: "bg-[#123B52] hover:bg-[#0F3246] text-white shadow-sm focus:ring-[#123B52]",
  secondary: "bg-white hover:bg-slate-100 text-slate-900 border border-slate-300 shadow-sm focus:ring-slate-400",
  emerald: "bg-[#059669] hover:bg-[#047857] text-white shadow-sm focus:ring-[#059669]",
  amber: "bg-[#D99A3D] hover:bg-[#C88A2D] text-slate-950 font-black shadow-sm focus:ring-[#D99A3D]",
  saffron: "bg-[#D99A3D] hover:bg-[#C88A2D] text-slate-950 font-black shadow-sm focus:ring-[#D99A3D]",
  destructive: "bg-[#DC2626] hover:bg-[#B91C1C] text-white shadow-sm focus:ring-[#DC2626]",
  danger: "bg-[#DC2626] hover:bg-[#B91C1C] text-white shadow-sm focus:ring-[#DC2626]",
  ghost: "bg-transparent hover:bg-slate-100 text-slate-800 focus:ring-slate-400",
  outline: "bg-white hover:bg-slate-50 text-slate-900 border border-slate-300 shadow-sm focus:ring-[#123B52]",
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
