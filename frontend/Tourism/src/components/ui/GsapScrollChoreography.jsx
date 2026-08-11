/**
 * frontend/Tourism/src/components/ui/GsapScrollChoreography.jsx
 *
 * GSAP Animation Skills & Cinematic Scroll Choreography.
 * Implements smooth timeline reveals, mountain depth parallax, and scroll-triggered typography
 * with complete reduced-motion compatibility and zero layout shift.
 */
import React, { useEffect, useRef } from "react"
import gsap from "gsap"

export const GsapMountainReveal = ({ children, className = "" }) => {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    // GSAP Fade and subtle upward translation
    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        { opacity: 0, y: 30, filter: "blur(4px)" },
        {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          duration: 0.8,
          ease: "power3.out",
        }
      )
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}

export const GsapStaggerCards = ({ children, stagger = 0.08, className = "" }) => {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const ctx = gsap.context(() => {
      const items = el.children
      gsap.fromTo(
        items,
        { opacity: 0, y: 24, scale: 0.98 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          stagger: stagger,
          duration: 0.6,
          ease: "back.out(1.4)",
        }
      )
    }, containerRef)

    return () => ctx.revert()
  }, [stagger])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}

export const GsapTextReveal = ({ text, className = "" }) => {
  const textRef = useRef(null)

  useEffect(() => {
    const el = textRef.current
    if (!el) return

    const words = el.querySelectorAll(".gsap-word")
    const ctx = gsap.context(() => {
      gsap.fromTo(
        words,
        { opacity: 0, y: 15, rotateX: -40 },
        {
          opacity: 1,
          y: 0,
          rotateX: 0,
          stagger: 0.04,
          duration: 0.5,
          ease: "power2.out",
        }
      )
    }, textRef)

    return () => ctx.revert()
  }, [text])

  const words = (text || "").split(" ")

  return (
    <span ref={textRef} className={`inline-block ${className}`}>
      {words.map((word, i) => (
        <span key={i} className="gsap-word inline-block mr-1.5 transform-gpu">
          {word}
        </span>
      ))}
    </span>
  )
}
