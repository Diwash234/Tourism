import i18n from "i18next"
import { initReactI18next } from "react-i18next"
import LanguageDetector from "i18next-browser-languagedetector"

import en from "./locales/en.json"
import ne from "./locales/ne.json"
import hi from "./locales/hi.json"
import es from "./locales/es.json"
import fr from "./locales/fr.json"
import de from "./locales/de.json"
import ja from "./locales/ja.json"
import zh from "./locales/zh.json"
import ar from "./locales/ar.json"

/**
 * i18n/index.js
 *
 * WHY THIS EXISTS:
 * Settings.jsx already had a "Language" dropdown that saved
 * `preferred_language` to the user's backend profile -- but nothing
 * in the app ever read that value back to actually change what text
 * is displayed. Selecting "Nepali" saved successfully and changed...
 * nothing visible. There was no i18n library in the project at all.
 *
 * This sets up real language switching using i18next, covering Nepali
 * plus a broad set of major international languages (add more by
 * dropping another locales/xx.json file and registering it below --
 * the shape only needs to match en.json's keys).
 *
 * SCOPE, HONESTLY: this translates the parts of the UI that appear on
 * every page -- Navbar, Sidebar, Footer, and the Settings page itself
 * -- via the `common`/`nav`/`settings` keys below, and switching
 * language changes all of those immediately, everywhere, without a
 * page reload. Destination/hotel *content* (descriptions, names) is a
 * separate, already-existing feature (see Translation.jsx and the
 * DestinationTranslation backend model) -- that's real per-content AI
 * translation, not this. Extending full UI translation to every
 * remaining page's body text means wrapping more of that page's
 * strings in `t('key')` the same way Navbar.jsx/Sidebar.jsx/Footer.jsx
 * now are; the infrastructure here already supports it, it's just a
 * matter of doing that same mechanical step page by page.
 */

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English", nativeLabel: "English" },
  { code: "ne", label: "Nepali", nativeLabel: "नेपाली" },
  { code: "hi", label: "Hindi", nativeLabel: "हिन्दी" },
  { code: "es", label: "Spanish", nativeLabel: "Español" },
  { code: "fr", label: "French", nativeLabel: "Français" },
  { code: "de", label: "German", nativeLabel: "Deutsch" },
  { code: "ja", label: "Japanese", nativeLabel: "日本語" },
  { code: "zh", label: "Chinese", nativeLabel: "中文" },
  { code: "ar", label: "Arabic", nativeLabel: "العربية" },
]

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ne: { translation: ne },
      hi: { translation: hi },
      es: { translation: es },
      fr: { translation: fr },
      de: { translation: de },
      ja: { translation: ja },
      zh: { translation: zh },
      ar: { translation: ar },
    },
    fallbackLng: "en",
    interpolation: { escapeValue: false }, // React already escapes
    detection: {
      // Checks localStorage first (so Settings.jsx's choice sticks
      // across sessions), then the browser's own language, in that order.
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "tourism_site_language",
    },
  })

export default i18n