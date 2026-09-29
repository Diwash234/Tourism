import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiGlobe, FiCheck, FiChevronDown } from "react-icons/fi"
import useTranslation from "../hooks/useTranslation"

/**
 * LanguageSelector - Dropdown component for switching between 28 languages
 * Supports RTL languages (Arabic, Urdu, Hebrew, Persian)
 */
const LanguageSelector = ({ compact = false, className = "" }) => {
  const { lang, setLang, languages, t, dir } = useTranslation()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const currentLang = languages.find((l) => l.code === lang) || languages[0]

  return (
    <div ref={ref} className={`relative ${className}`} dir={dir}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t("language.select")}
        className={`flex items-center gap-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700 transition-colors ${
          compact ? "" : "min-w-[160px] justify-between"
        }`}
      >
        <FiGlobe size={16} className="text-emerald-600" />
        {!compact && <span>{currentLang?.native || currentLang?.label}</span>}
        {compact && <span className="uppercase text-xs font-bold">{currentLang?.code}</span>}
        <FiChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-56 max-h-80 overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-lg z-50 py-1"
            role="listbox"
          >
            {languages.map((language) => (
              <button
                key={language.code}
                type="button"
                role="option"
                aria-selected={language.code === lang}
                onClick={() => {
                  setLang(language.code)
                  setOpen(false)
                }}
                className={`w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-gray-50 text-left ${
                  language.dir === "rtl" ? "text-right" : ""
                }`}
              >
                <span className="flex items-center gap-2">
                  <span className="font-medium text-gray-800">{language.native}</span>
                  <span className="text-xs text-gray-400">{language.label}</span>
                </span>
                {language.code === lang && (
                  <FiCheck size={16} className="text-emerald-600" />
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default LanguageSelector
