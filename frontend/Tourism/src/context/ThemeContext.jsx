import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

const STORAGE_KEY = "ny_theme"
const ThemeContext = createContext(null)

const getInitialTheme = () => {
  if (typeof window === "undefined") return "light"
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === "dark" || saved === "light") return saved
  } catch { /* localStorage unavailable (private mode) */ }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(getInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === "dark") root.classList.add("dark")
    else root.classList.remove("dark")
    root.style.colorScheme = theme
    try {
      window.localStorage.setItem(STORAGE_KEY, theme)
    } catch { /* ignore quota/private-mode errors */ }
  }, [theme])

  const setTheme = useCallback((next) => setThemeState(next === "dark" ? "dark" : "light"), [])
  const toggleTheme = useCallback(
    () => setThemeState((t) => (t === "dark" ? "light" : "dark")),
    []
  )

  const value = useMemo(
    () => ({ theme, isDark: theme === "dark", setTheme, toggleTheme }),
    [theme, setTheme, toggleTheme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

const useTheme = () => {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    // Safe no-op fallback so components never crash if the provider is absent.
    return { theme: "light", isDark: false, setTheme: () => {}, toggleTheme: () => {} }
  }
  return ctx
}

export default useTheme
