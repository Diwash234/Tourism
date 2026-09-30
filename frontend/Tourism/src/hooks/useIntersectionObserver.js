import { useState, useEffect, useRef } from "react"

/**
 * useIntersectionObserver — detects when an element enters/leaves the viewport.
 * Useful for lazy loading, infinite scroll, and scroll-triggered animations.
 */
export default function useIntersectionObserver(options = {}) {
  const ref = useRef(null)
  const [isIntersecting, setIsIntersecting] = useState(false)
  const [entry, setEntry] = useState(null)

  useEffect(() => {
    const element = ref.current
    if (!element) return undefined

    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting)
      setEntry(entry)
    }, { threshold: 0.1, rootMargin: "0px", ...options })

    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return [ref, isIntersecting, entry]
}
