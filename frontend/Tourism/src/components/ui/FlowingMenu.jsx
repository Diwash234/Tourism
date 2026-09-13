/**
 * FlowingMenu — Apple/Linear-style pill nav where an animated indicator
 * slides between items (spring physics via Framer Motion). Acessible:
 * uses role=tablist, arrow-key navigation, aria-selected.
 */
import { useRef, useState, useEffect } from "react"
import { motion } from "framer-motion"
import { cn } from "../../utils/cn"

export default function FlowingMenu({
  items,                 // [{key, label, icon?: Icon, onClick?, href?}]
  activeKey,
  onChange,
  className = "",
  size = "md",
}) {
  const [bounds, setBounds] = useState({ x: 0, w: 0 })
  const containerRef = useRef(null)
  const itemRefs = useRef({})

  const sizeMap = {
    sm: "text-xs px-3 py-1.5",
    md: "text-sm px-4 py-2",
    lg: "text-base px-5 py-2.5",
  }

  const moveTo = (key) => {
    const el = itemRefs.current[key]
    const parent = containerRef.current
    if (!el || !parent) return
    const pRect = parent.getBoundingClientRect()
    const iRect = el.getBoundingClientRect()
    setBounds({ x: iRect.left - pRect.left, w: iRect.width })
  }

  useEffect(() => {
    if (activeKey) moveTo(activeKey)
    const onResize = () => activeKey && moveTo(activeKey)
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeKey])

  const onKey = (e, idx) => {
    const i = items.findIndex(x => x.key === activeKey)
    if (e.key === "ArrowRight") {
      e.preventDefault()
      const next = items[(i + 1) % items.length]
      onChange?.(next.key)
    } else if (e.key === "ArrowLeft") {
      e.preventDefault()
      const prev = items[(i - 1 + items.length) % items.length]
      onChange?.(prev.key)
    } else if (e.key === "Home") {
      e.preventDefault(); onChange?.(items[0].key)
    } else if (e.key === "End") {
      e.preventDefault(); onChange?.(items[items.length - 1].key)
    }
  }

  return (
    <div
      ref={containerRef}
      role="tablist"
      className={cn(
        "relative inline-flex items-center gap-1 p-1 rounded-full bg-stone-100/80 backdrop-blur",
        "border border-stone-200 shadow-inner",
        className,
      )}
    >
      {bounds.w > 0 && (
        <motion.span
          layout
          transition={{ type: "spring", stiffness: 500, damping: 35 }}
          className="absolute top-1 bottom-1 rounded-full bg-white shadow-md ring-1 ring-stone-200"
          style={{ left: bounds.x, width: bounds.w }}
          aria-hidden
        />
      )}
      {items.map((it, idx) => {
        const active = it.key === activeKey
        const Icon = it.icon
        return (
          <button
            key={it.key}
            ref={(el) => (itemRefs.current[it.key] = el)}
            role="tab"
            tabIndex={active ? 0 : -1}
            aria-selected={active}
            onKeyDown={(e) => onKey(e, idx)}
            onFocus={() => onChange?.(it.key)}
            onMouseEnter={() => moveTo(it.key)}
            onClick={() => onChange?.(it.key)}
            className={cn(
              "relative z-10 inline-flex items-center gap-1.5 rounded-full font-medium transition-colors",
              sizeMap[size],
              active ? "text-stone-900" : "text-stone-500 hover:text-stone-700",
            )}
          >
            {Icon && <Icon size={14} />}
            {it.label}
          </button>
        )
      })}
    </div>
  )
}
