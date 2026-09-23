const VARIANTS = {
  success: "bg-emerald-100 text-emerald-800 border-emerald-300",
  warning: "bg-amber-100 text-amber-900 border-amber-300",
  danger: "bg-rose-100 text-rose-800 border-rose-300",
  info: "bg-blue-100 text-blue-800 border-blue-300",
  purple: "bg-emerald-100 text-[#1D5146] border-[#2E6B5A]",
  neutral: "bg-slate-100 text-slate-800 border-slate-200",
}

const SIZES = {
  sm: "px-2 py-0.5 text-[10px]",
  md: "px-2.5 py-1 text-xs",
  lg: "px-3 py-1.5 text-xs font-black",
}

export default function Badge({
  children,
  variant = "neutral",
  size = "md",
  icon: Icon,
  className = "",
}) {
  const variantStyle = VARIANTS[variant] || VARIANTS.neutral
  const sizeStyle = SIZES[size] || SIZES.md

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-bold uppercase tracking-wider ${variantStyle} ${sizeStyle} ${className}`}
    >
      {Icon && <Icon size={size === "sm" ? 10 : 12} />}
      <span>{children}</span>
    </span>
  )
}
