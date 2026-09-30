import { FiSun, FiMoon } from "react-icons/fi"
import useTheme from "../../context/ThemeContext"

/**
 * Accessible dark mode toggle with smooth transition.
 * Works in both navbar and mobile menu contexts.
 */
export default function DarkModeToggle({ variant = "default" }) {
  const { isDark, toggleTheme } = useTheme()

  const baseClasses = variant === "mobile"
    ? "flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium text-[#C7D9D2] hover:bg-white/10 hover:text-white transition-colors"
    : "p-1.5 rounded-lg text-[#BDEBD9] hover:text-white hover:bg-white/10 transition-colors"

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={baseClasses}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? <FiSun size={18} /> : <FiMoon size={18} />}
      {variant === "mobile" && <span>{isDark ? "Light Mode" : "Dark Mode"}</span>}
    </button>
  )
}
