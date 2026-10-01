import { useI18n, ALL_LANGS } from "../i18n"

/**
 * Compatibility hook for older components.
 *
 * The application uses the reactive i18n store in src/i18n/index.js.
 * The previous implementation consumed TranslationContext, but main.jsx
 * intentionally does not mount that provider; any component using the
 * legacy hook therefore crashed at runtime with:
 * "useTranslation must be used within a TranslationProvider".
 */
const useTranslation = () => {
  const { lang, setLang, t, dir } = useI18n()
  return {
    lang,
    setLang,
    t,
    dir,
    isRTL: dir === "rtl",
    languages: ALL_LANGS.map((language) => ({
      ...language,
      label: language.label,
      native: language.native,
    })),
  }
}

export default useTranslation
