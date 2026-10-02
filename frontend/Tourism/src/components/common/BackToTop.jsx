import { useState, useEffect } from "react"
import { FiArrowUp } from "react-icons/fi"

/**
 * Floating back-to-top button that appears after scrolling down.
 * Smooth scrolls back to top on click.
 */
export default function BackToTop() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const onScroll = () => {
      setVisible(window.scrollY > 400)
    }
    window.addEventListener("scroll", onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <button
      type="button"
      onClick={scrollToTop}
      aria-label="Back to top"
      title="Back to top"
      className={`fixed bottom-20 right-4 z-[55] flex items-center justify-center w-11 h-11 rounded-full bg-[var(--ny-green)] text-white shadow-lg shadow-emerald-950/30 transition-all duration-300 hover:bg-[var(--ny-emerald)] hover:scale-110 ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none"
      }`}
    >
      <FiArrowUp size={20} />
    </button>
  )
}
