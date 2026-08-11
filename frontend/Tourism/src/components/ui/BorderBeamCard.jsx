import React from "react"
import { cn } from "../../utils/cn"

export const BorderBeamCard = ({ children, className = "", hoverEffect = true }) => {
  return (
    <div
      className={cn(
        "relative rounded-3xl p-[1px] bg-gradient-to-b from-purple-500/30 via-transparent to-amber-500/20 shadow-xl overflow-hidden group",
        hoverEffect && "hover:from-amber-400/50 hover:to-purple-500/40 transition-all duration-500",
        className
      )}
    >
      <div className="relative rounded-[23px] bg-white p-6 h-full flex flex-col justify-between overflow-hidden">
        {children}
      </div>
    </div>
  )
}

export default BorderBeamCard
