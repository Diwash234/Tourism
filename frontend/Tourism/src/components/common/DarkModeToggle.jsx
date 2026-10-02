import { useState, useEffect } from "react"
import { FiSun, FiMoon } from "react-icons/fi"

/**
 * Dark mode toggle with system preference detection.
 * Persists user choice in localStorage.
 */
export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem("ny-theme")
    if (stored) return stored === "dark"
    return window.matchMedia("(prefers-color-scheme: dark)").matches
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark")
      localStorage.setItem("ny-theme", "dark")
    } else {
      document.documentElement.classList.remove("dark")
      localStorage.setItem("ny-theme", "light")
    }
  }, [isDark])

  return (
    <button
      type="button"
      onClick={() => setIsDark(!isDark)}
      className="p-2 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? <FiSun size={20} /> : <FiMoon size={20} />}
    </button>
  )
}
