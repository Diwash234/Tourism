import React from "react"

/**
 * ResponsiveContainer — Standard constrained content wrapper.
 * Prevents content from stretching awkwardly on 1920px+ and 2560px ultrawide displays.
 */
export function ResponsiveContainer({ children, className = "", fullBgClass = "" }) {
  return (
    <div className={`w-full ${fullBgClass}`}>
      <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 ${className}`}>
        {children}
      </div>
    </div>
  )
}

/**
 * ResponsiveGrid — Adaptable grid primitive for cards, stats, and lists.
 */
export function ResponsiveGrid({ children, cols = 3, gap = 6, className = "" }) {
  const colClasses = {
    1: "grid-cols-1",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5",
    6: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6",
  }

  const gapClasses = {
    2: "gap-2",
    3: "gap-3",
    4: "gap-4",
    5: "gap-5",
    6: "gap-6",
    8: "gap-8",
  }

  return (
    <div className={`grid ${colClasses[cols] || colClasses[3]} ${gapClasses[gap] || "gap-6"} ${className}`}>
      {children}
    </div>
  )
}

/**
 * ResponsiveModal — Accessible, touch-friendly modal primitive with max-width constraints.
 */
export function ResponsiveModal({ isOpen, onClose, title, children, maxWidth = "max-w-xl" }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm overflow-y-auto">
      <div className={`bg-slate-950 border border-slate-800 rounded-3xl w-full ${maxWidth} p-6 sm:p-8 space-y-5 shadow-2xl text-white my-8 max-h-[90vh] overflow-y-auto`}>
        <div className="flex justify-between items-start border-b border-slate-800 pb-4">
          <h3 className="text-xl font-black text-white">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
