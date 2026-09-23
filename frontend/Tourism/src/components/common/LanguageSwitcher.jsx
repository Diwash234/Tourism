import { useState, useRef, useEffect } from "react"
import { FiGlobe, FiCheck } from "react-icons/fi"
import { ALL_LANGS, useI18n } from "../../i18n"

/**
 * LanguageSwitcher
 * Accessible dropdown that changes the active UI language (en/ne/hi).
 * Persists to localStorage + django_language cookie so the backend can
 * match. Compact variant fits in the navbar; full variant for settings.
 */
export default function LanguageSwitcher({ compact = false, className = "" }) {
  const { lang, setLang } = useI18n()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [])

  const current = ALL_LANGS.find((l) => l.code === lang) || ALL_LANGS[0]

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select language"
        className={`flex items-center gap-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 px-2.5 py-1.5 text-sm font-medium text-gray-700 transition ${
          compact ? "" : "min-w-[140px] justify-between"
        }`}
      >
        <FiGlobe className="text-gray-500" size={16} />
        {!compact && <span>{current.native}</span>}
        {compact && <span className="uppercase text-xs font-bold">{current.code}</span>}
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute right-0 mt-2 w-48 rounded-xl border border-gray-100 bg-white shadow-lg z-50 py-1 overflow-hidden"
        >
          {ALL_LANGS.map((l) => (
            <li key={l.code}>
              <button
                type="button"
                role="option"
                aria-selected={l.code === lang}
                onClick={() => {
                  setLang(l.code)
                  setOpen(false)
                }}
                className="w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-gray-50 text-left"
              >
                <span className="flex items-center gap-2">
                  <span className="text-base">{l.flag}</span>
                  <span>
                    <span className="block font-semibold text-gray-800">{l.native}</span>
                    <span className="block text-xs text-gray-400">{l.label}</span>
                  </span>
                </span>
                {l.code === lang && <FiCheck className="text-himalaya-500" />}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
