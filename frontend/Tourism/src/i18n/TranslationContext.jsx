import { createContext, useState, useEffect, useCallback, useMemo } from "react"
import { translations, RTL_LANGUAGES, DEFAULT_LANGUAGE, STORAGE_KEY } from "./translations"

/**
 * TranslationContext - React context for i18n
 *
 * Supports 28 languages with:
 * - Fallback to English for missing translations
 * - RTL support for Arabic, Urdu, Hebrew, etc.
 * - Variable interpolation: t("hello", { name: "World" })
 * - Persistence in localStorage
 * - Cookie sync for backend language detection
 */

export const TranslationContext = createContext(null)

// ─── Language Detection ──────────────────────────────────────────────────────
const detectInitialLanguage = () => {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE

  // Check localStorage first
  const saved = window.localStorage?.getItem(STORAGE_KEY)
  if (saved && translations[saved]) return saved

  // Check cookie
  const cookieMatch = document.cookie.match(new RegExp(`${STORAGE_KEY}=([^;]+)`))
  if (cookieMatch && translations[cookieMatch[1]]) return cookieMatch[1]

  // Check browser language
  const browserLang = (window.navigator?.language || "en").slice(0, 2)
  if (translations[browserLang]) return browserLang

  return DEFAULT_LANGUAGE
}

// ─── Translation Provider ────────────────────────────────────────────────────
export const TranslationProvider = ({ children }) => {
  const [lang, setLangState] = useState(detectInitialLanguage)

  // Persist language choice
  const setLang = useCallback((code) => {
    if (!translations[code]) return

    setLangState(code)

    // Save to localStorage
    try {
      window.localStorage.setItem(STORAGE_KEY, code)
    } catch {
      // Storage unavailable
    }

    // Save to cookie for backend
    try {
      document.cookie = `${STORAGE_KEY}=${code}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`
    } catch {
      // Cookie unavailable
    }

    // Update HTML attributes
    document.documentElement.lang = code
    document.documentElement.dir = RTL_LANGUAGES.includes(code) ? "rtl" : "ltr"
  }, [])

  // Update HTML dir attribute on language change
  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = RTL_LANGUAGES.includes(lang) ? "rtl" : "ltr"
  }, [lang])

  // ─── Translation Function ─────────────────────────────────────────────────
  const t = useCallback((key, vars) => {
    const dict = translations[lang] || translations[DEFAULT_LANGUAGE]
    let str = dict[key] || translations[DEFAULT_LANGUAGE][key] || key

    // Variable interpolation: {name} -> value
    if (vars && typeof vars === "object") {
      Object.entries(vars).forEach(([k, v]) => {
        str = str.replace(new RegExp(`\\{${k}\\}`, "g"), String(v))
      })
    }

    return str
  }, [lang])

  // ─── Context Value ────────────────────────────────────────────────────────
  const value = useMemo(() => ({
    lang,
    setLang,
    t,
    dir: RTL_LANGUAGES.includes(lang) ? "rtl" : "ltr",
    isRTL: RTL_LANGUAGES.includes(lang),
    languages: Object.keys(translations).map((code) => ({
      code,
      label: translations[code]._label || code,
      native: translations[code]._native || code,
      dir: RTL_LANGUAGES.includes(code) ? "rtl" : "ltr",
    })),
  }), [lang, setLang, t])

  return (
    <TranslationContext.Provider value={value}>
      {children}
    </TranslationContext.Provider>
  )
}

export default TranslationProvider
