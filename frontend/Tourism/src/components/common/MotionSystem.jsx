import React, { useRef, useState, useEffect } from "react"
import { motion, useReducedMotion } from "framer-motion"

// Smooth cubic bezier easing matching modern digital agency standards (Refero / Emil Kowalski)
export const TRANSITION_SMOOTH = {
  duration: 0.5,
  ease: [0.22, 1, 0.36, 1],
}

export const TRANSITION_SPRING = {
  type: "spring",
  stiffness: 260,
  damping: 24,
}

/**
 * FadeIn — Smooth opacity and vertical reveal with reduced-motion support
 */
export const FadeIn = ({ children, delay = 0, y = 16, className = "" }) => {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * SlideUp — On-scroll viewport reveal
 */
export const SlideUp = ({ children, delay = 0, className = "" }) => {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * Stagger container and child items
 */
export const Stagger = ({ children, delayOrder = 0.08, className = "" }) => {
  return (
    <motion.div
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-30px" }}
      variants={{
        hidden: {},
        show: {
          transition: {
            staggerChildren: delayOrder,
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export const StaggerItem = ({ children, className = "" }) => {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 20 },
        show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
      }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * HoverCard — Interactive card with Refero-grade scale, lift, and subtle glow
 */
export const HoverCard = ({ children, className = "", onClick }) => {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      whileHover={shouldReduceMotion ? {} : { y: -6, scale: 1.015 }}
      whileTap={shouldReduceMotion ? {} : { scale: 0.985 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      onClick={onClick}
      className={`transition-shadow hover:shadow-2xl ${className}`}
    >
      {children}
    </motion.div>
  )
}

/**
 * MagneticButton — Refero / Emil Kowalski style magnetic attraction button
 */
export const MagneticButton = ({ children, onClick, className = "", disabled = false }) => {
  const ref = useRef(null)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const shouldReduceMotion = useReducedMotion()

  const handleMouseMove = (e) => {
    if (shouldReduceMotion || !ref.current || disabled) return
    const { clientX, clientY } = e
    const { left, top, width, height } = ref.current.getBoundingClientRect()
    const x = (clientX - (left + width / 2)) * 0.25
    const y = (clientY - (top + height / 2)) * 0.25
    setPos({ x, y })
  }

  const handleMouseLeave = () => {
    setPos({ x: 0, y: 0 })
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: pos.x, y: pos.y }}
      transition={{ type: "spring", stiffness: 220, damping: 18, mass: 0.1 }}
      className="inline-block"
    >
      <motion.button
        whileHover={{ scale: 1.04 }}
        whileTap={{ scale: 0.96 }}
        onClick={onClick}
        disabled={disabled}
        className={className}
      >
        {children}
      </motion.button>
    </motion.div>
  )
}

/**
 * BurnGlowBadge — Luxury energy sweep glow pill
 */
export const BurnGlowBadge = ({ text, icon: Icon = null, variant = "gold" }) => {
  return (
    <div className="relative inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full overflow-hidden border border-amber-400/40 bg-gradient-to-r from-purple-950/80 via-purple-900/60 to-purple-950/80 text-amber-300 text-xs font-bold shadow-lg shadow-purple-950/40 backdrop-blur">
      <span className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-400/20 to-transparent -translate-x-full animate-[shimmer_2.5s_infinite]" />
      {Icon && <Icon size={13} className="text-amber-400 animate-pulse" />}
      <span className="relative z-10 tracking-wide">{text}</span>
    </div>
  )
}

/**
 * InteractiveHeroCanvas — Ambient interactive particle glow (Unicorn / WebGL style with zero crash risk)
 */
export const InteractiveHeroCanvas = () => {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    let animationFrameId
    let width = (canvas.width = canvas.offsetWidth)
    let height = (canvas.height = canvas.offsetHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = canvas.offsetWidth
      height = canvas.height = canvas.offsetHeight
    }
    window.addEventListener("resize", handleResize)

    // Particle nodes
    const particles = Array.from({ length: 32 }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.5 + 0.2,
    }))

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Draw floating particles
      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0) p.x = width
        if (p.x > width) p.x = 0
        if (p.y < 0) p.y = height
        if (p.y > height) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(251, 191, 36, ${p.alpha * 0.7})`
        ctx.fill()
      })

      // Draw connecting energy strands
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 110) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(168, 85, 247, ${0.12 * (1 - dist / 110)})`
            ctx.lineWidth = 0.8
            ctx.stroke()
          }
        }
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      window.removeEventListener("resize", handleResize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-60" />
}

/**
 * ElevationScrollProgress — Ambient Himalayan altitude tracker on scroll
 */
export const ElevationScrollProgress = () => {
  const [scrollPercent, setScrollPercent] = useState(0)
  const shouldReduceMotion = useReducedMotion()

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight
      if (totalHeight > 0) {
        const current = (window.scrollY / totalHeight) * 100
        setScrollPercent(Math.min(100, Math.max(0, current)))
      }
    }
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Approximate Nepal elevation curve from 70m (Jhapa) to 8,848m (Sagarmatha)
  const currentAlt = Math.round(70 + (scrollPercent / 100) * (8848 - 70))

  return (
    <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none h-1 bg-black/10 backdrop-blur-sm">
      <motion.div
        className="h-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-600 shadow-sm"
        style={{ width: `${scrollPercent}%` }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.1 }}
      />
      {scrollPercent > 3 && (
        <div
          className="absolute top-2 right-4 bg-slate-900/85 border border-white/15 px-2.5 py-0.5 rounded-full text-[10px] font-mono text-amber-300 backdrop-blur shadow-md flex items-center gap-1.5 transition-all"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Elevation: {currentAlt.toLocaleString()}m</span>
        </div>
      )}
    </div>
  )
}

/**
 * PrayerFlagsBanner — Subtle 5-color prayer flags (Wind, Space, Fire, Water, Earth)
 */
export const PrayerFlagsBanner = ({ className = "" }) => {
  const flags = [
    { color: "bg-blue-600/70", label: "Sky / Space" },
    { color: "bg-white/80", label: "Air / Wind" },
    { color: "bg-red-600/70", label: "Fire" },
    { color: "bg-green-600/70", label: "Water" },
    { color: "bg-yellow-500/80", label: "Earth" },
    { color: "bg-blue-600/70", label: "Sky" },
    { color: "bg-white/80", label: "Wind" },
    { color: "bg-red-600/70", label: "Fire" },
    { color: "bg-green-600/70", label: "Water" },
    { color: "bg-yellow-500/80", label: "Earth" },
  ]

  return (
    <div className={`relative overflow-hidden py-1 opacity-75 hover:opacity-100 transition-opacity ${className}`}>
      <div className="absolute inset-x-0 top-1/2 h-[1px] bg-amber-800/30" />
      <div className="flex items-start justify-around relative z-10 px-2">
        {flags.map((f, i) => (
          <motion.div
            key={i}
            className={`w-3.5 h-4.5 sm:w-5 sm:h-6 ${f.color} rounded-b-[2px] shadow-sm transform origin-top`}
            animate={{
              rotate: [0, 4, -3, 2, 0],
              skewX: [0, 2, -2, 0],
            }}
            transition={{
              duration: 3.5 + (i % 3) * 0.8,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.2,
            }}
            title={f.label}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * DokoMotifBadge — Subtle Nepalese Doko wicker travel emblem
 */
export const DokoMotifBadge = ({ label = "My Doko", count = null, className = "" }) => {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/40 border border-amber-500/30 text-amber-300 backdrop-blur shadow-sm ${className}`}>
      <span className="text-sm">🧺</span>
      <span>{label}</span>
      {count !== null && (
        <span className="ml-0.5 px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-200 text-[10px]">
          {count}
        </span>
      )}
    </span>
  )
}

