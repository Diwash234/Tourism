import React from "react"
import { cn } from "../../utils/cn"

export const ShimmerBadge = ({ children, className = "", variant = "gold", icon: Icon = null }) => {
  return (
    <div
      className={cn(
        "relative inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full overflow-hidden text-xs font-black shadow-lg backdrop-blur border",
        variant === "gold" && "border-amber-400/40 bg-gradient-to-r from-purple-950/90 via-purple-900/70 to-purple-950/90 text-amber-300 shadow-purple-950/50",
        variant === "emerald" && "border-emerald-400/40 bg-gradient-to-r from-emerald-950/90 via-emerald-900/70 to-emerald-950/90 text-emerald-300 shadow-emerald-950/50",
        variant === "ruby" && "border-rose-400/40 bg-gradient-to-r from-rose-950/90 via-rose-900/70 to-rose-950/90 text-rose-300 shadow-rose-950/50",
        className
      )}
    >
      <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-[shimmer_3s_infinite]" />
      {Icon && <Icon size={13} className="animate-pulse shrink-0" />}
      <span className="relative z-10 tracking-wide uppercase">{children}</span>
    </div>
  )
}

export default ShimmerBadge
