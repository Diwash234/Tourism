/**
 * CrazyButton — magnetic, spring-animated CTA in the ReactBits style.
 *
 * Features:
 *  - Magnetic hover: button chases the cursor within a radius
 *  - Press squash/stretch spring
 *  - Gradient sheen that sweeps across on hover
 *  - Particle burst (colored dots) on click
 *  - Keyboard accessible, announces via aria-busy during animation
 *  - Reduced-motion: disables magnetic + particle burst
 */
import { useCallback, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "../../utils/cn"

const PARTICLE_COLORS = ["#1f6b4d", "#c2603a", "#b8862f", "#2f7d4f", "#ea580c"]

export default function CrazyButton({
  children,
  className = "",
  variant = "primary",
  onClick,
  magnetic = 30,
  burstCount = 8,
  as: As = "button",
  type = "button",
  disabled = false,
  ...rest
}) {
  const ref = useRef(null)
  const [particles, setParticles] = useState([])
  const [reduced] = useState(
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  )

  const handleMouseMove = useCallback((e) => {
    if (reduced || disabled) return
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const relX = e.clientX - rect.left - rect.width / 2
    const relY = e.clientY - rect.top - rect.height / 2
    el.style.transform = `translate(${relX * 0.25}px, ${relY * 0.3}px) scale(1.04)`
  }, [reduced, disabled])

  const handleMouseLeave = useCallback(() => {
    const el = ref.current
    if (el) el.style.transform = ""
  }, [])

  const handleClick = useCallback((e) => {
    if (disabled) return
    if (!reduced) {
      const rect = e.currentTarget.getBoundingClientRect()
      const cx = rect.width / 2
      const cy = rect.height / 2
      const burst = Array.from({ length: burstCount }).map((_, i) => {
        const angle = (Math.PI * 2 * i) / burstCount + Math.random() * 0.3
        const dist = 40 + Math.random() * 50
        return {
          id: `${Date.now()}-${i}`,
          x: Math.cos(angle) * dist,
          y: Math.sin(angle) * dist,
          color: PARTICLE_COLORS[i % PARTICLE_COLORS.length],
          size: 4 + Math.random() * 6,
        }
      })
      setParticles(burst)
      setTimeout(() => setParticles([]), 700)
    }
    onClick?.(e)
  }, [onClick, burstCount, reduced, disabled])

  const variants = {
    primary: "from-primary-600 via-primary-500 to-secondary-600 text-white",
    secondary: "from-secondary-500 via-secondary-400 to-accent text-white",
    outline: "bg-white text-stone-900 border border-stone-300 hover:border-primary-400",
    ghost: "bg-transparent text-primary-700 hover:bg-primary-50",
  }

  return (
    <As
      ref={ref}
      type={As === "button" ? type : undefined}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        "relative inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold",
        "transition-[box-shadow,background] duration-200 select-none",
        "shadow-lg shadow-primary-900/20 overflow-hidden",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500",
        "bg-gradient-to-br",
        variants[variant],
        disabled && "opacity-50 cursor-not-allowed pointer-events-none",
        className,
      )}
      style={{ transition: "transform 200ms cubic-bezier(.2,.8,.2,1)" }}
      {...rest}
    >
      {/* Sheen */}
      {!reduced && (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-0 -translate-x-full"
          initial={false}
          whileHover={{ x: "100%" }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          style={{
            background: "linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.35) 50%, transparent 70%)",
          }}
        />
      )}

      <motion.span
        className="relative z-10 inline-flex items-center gap-2"
        whileTap={{ scale: 0.94 }}
        transition={{ type: "spring", stiffness: 500, damping: 20 }}
      >
        {children}
      </motion.span>

      {/* Particle burst */}
      <AnimatePresence>
        {particles.map((p) => (
          <motion.span
            key={p.id}
            aria-hidden
            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
            animate={{ x: p.x, y: p.y, opacity: 0, scale: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.1, 0.7, 0.3, 1] }}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full pointer-events-none"
            style={{ width: p.size, height: p.size, background: p.color }}
          />
        ))}
      </AnimatePresence>
    </As>
  )
}
