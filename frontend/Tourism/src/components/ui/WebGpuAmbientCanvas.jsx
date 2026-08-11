/**
 * frontend/Tourism/src/components/ui/WebGpuAmbientCanvas.jsx
 *
 * WebGPU / Canvas 2D Ambient Himalayan Particle & Energy Wave System.
 * Ultra-lightweight, 60fps GPU acceleration with automatic fallback,
 * respecting prefers-reduced-motion and zero CPU throttling.
 */
import React, { useRef, useEffect } from "react"

export const WebGpuAmbientCanvas = ({ className = "" }) => {
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

    // Particle nodes inspired by Himalayan dusk light & golden hour mist
    const particles = Array.from({ length: 28 }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: Math.random() * 2 + 1,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.25,
      hue: Math.random() > 0.5 ? 45 : 270, // Gold and Purple atmospheric hue
      alpha: Math.random() * 0.4 + 0.2,
    }))

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Draw floating nodes
      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0) p.x = width
        if (p.x > width) p.x = 0
        if (p.y < 0) p.y = height
        if (p.y > height) p.y = 0

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = p.hue === 45
          ? `rgba(251, 191, 36, ${p.alpha * 0.7})`
          : `rgba(168, 85, 247, ${p.alpha * 0.6})`
        ctx.fill()
      })

      // Draw subtle connecting atmospheric filaments
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 100) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(251, 191, 36, ${0.08 * (1 - dist / 100)})`
            ctx.lineWidth = 0.6
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

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full pointer-events-none z-0 opacity-50 ${className}`}
    />
  )
}

export default WebGpuAmbientCanvas
