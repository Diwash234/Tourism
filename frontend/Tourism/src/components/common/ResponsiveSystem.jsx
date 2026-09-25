import Modal from "./Modal"

/**
 * ResponsiveContainer — Standard constrained content wrapper.
 * Prevents content from stretching awkwardly on 1920px+ and 2560px ultrawide displays.
 */
export function ResponsiveContainer({ children, className = "", fullBgClass = "" }) {
  return (
    <div className={`w-full ${fullBgClass}`}>
      <div className={`ny-page container-app max-w-[1600px] ${className}`}>
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
 * ResponsiveModal — delegates to the shared accessible modal primitive.
 */
export function ResponsiveModal(props) {
  return <Modal {...props} />
}
