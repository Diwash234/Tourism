import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

const STORAGE_KEY = "ny_theme"
const VALID_THEMES = new Set(["light", "dark", "system"])
const ThemeContext = createContext(null)

const systemTheme = () =>
  typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light"

const getInitialTheme = () => {
  if (typeof window === "undefined") return "system"
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (VALID_THEMES.has(saved)) return saved
  } catch { /* localStorage unavailable */ }
  return "system"
}

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(getInitialTheme)
  const [system, setSystem] = useState(systemTheme)
  const resolvedTheme = theme === "system" ? system : theme

  useEffect(() => {
    const media = window.matchMedia?.("(prefers-color-scheme: dark)")
    if (!media) return undefined
    const update = () => setSystem(media.matches ? "dark" : "light")
    update()
    media.addEventListener?.("change", update)
    return () => media.removeEventListener?.("change", update)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle("dark", resolvedTheme === "dark")
    root.style.colorScheme = resolvedTheme
    root.dataset.theme = resolvedTheme
    root.dataset.themePreference = theme
    try { window.localStorage.setItem(STORAGE_KEY, theme) } catch { /* ignore */ }
  }, [theme, resolvedTheme])

  const setTheme = useCallback((next) => {
    setThemeState(VALID_THEMES.has(next) ? next : "system")
  }, [])
  const toggleTheme = useCallback(() => {
    setThemeState((current) => (current === "dark" ? "light" : "dark"))
  }, [])

  const value = useMemo(
    () => ({ theme, resolvedTheme, isDark: resolvedTheme === "dark", setTheme, toggleTheme }),
    [theme, resolvedTheme, setTheme, toggleTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

const useTheme = () => {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    return { theme: "system", resolvedTheme: "light", isDark: false, setTheme: () => {}, toggleTheme: () => {} }
  }
  return ctx
}

export default useTheme
