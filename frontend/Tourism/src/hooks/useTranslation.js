import { useContext } from "react"
import { TranslationContext } from "../i18n/TranslationContext"

/**
 * useTranslation - Hook for accessing translation functions and language state
 *
 * Provides:
 * - t(key, vars) - Translate a key with optional variable interpolation
 * - lang - Current language code
 * - setLang(code) - Change the active language
 * - dir - Text direction (ltr/rtl)
 * - isRTL - Whether current language is right-to-left
 * - languages - List of all supported languages
 */
const useTranslation = () => {
  const context = useContext(TranslationContext)

  if (!context) {
    throw new Error("useTranslation must be used within a TranslationProvider")
  }

  return context
}

export default useTranslation
