import { useState, useEffect } from "react"

/**
 * Reading progress bar — shows how far the user has scrolled down the page.
 * Useful for long content pages like destination details, blog posts, etc.
 */
export default function ReadingProgress() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const onScroll = () => {
      const scrollTop = window.scrollY
      const docHeight = document.documentElement.scrollHeight - window.innerHeight
      if (docHeight > 0) {
        setProgress(Math.min((scrollTop / docHeight) * 100, 100))
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <div className="fixed top-0 left-0 right-0 z-[70] h-0.5 bg-transparent pointer-events-none">
      <div
        className="h-full bg-gradient-to-r from-[var(--ny-green)] to-[var(--ny-mint)] transition-[width] duration-100 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}
