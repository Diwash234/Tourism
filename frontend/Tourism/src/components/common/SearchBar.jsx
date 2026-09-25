import { useCallback, useEffect, useId, useRef, useState } from "react"
import { FiArrowRight, FiCompass, FiMapPin, FiNavigation, FiSearch, FiX } from "react-icons/fi"
import { AnimatePresence, motion } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { useI18n } from "../../i18n"

const SearchBar = ({ placeholder, onSearch, className = "", defaultValue = "", fetchSuggestions }) => {
  const [query, setQuery] = useState(defaultValue)
  const inputId = useId()
  const previousDefaultValue = useRef(defaultValue)
  const [suggestions, setSuggestions] = useState([])
  const [didYouMean, setDidYouMean] = useState(null)
  const [isOpen, setIsOpen] = useState(false)
  const [loadingSug, setLoadingSug] = useState(false)
  const containerRef = useRef(null)
  const abortRef = useRef(null)
  const navigate = useNavigate()
  const { t } = useI18n()

  useEffect(() => {
    // Only reset when the parent actually changes the default. Depending on
    // `query` here would erase every character as the visitor types.
    if (defaultValue !== previousDefaultValue.current) {
      previousDefaultValue.current = defaultValue
      const timer = setTimeout(() => setQuery(defaultValue), 0)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [defaultValue])

  const loadSuggestions = useCallback(async (value) => {
    if (!fetchSuggestions || value.trim().length < 1) { setSuggestions([]); return }
    setLoadingSug(true)
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const result = await fetchSuggestions(value.trim(), controller.signal)
      if (controller.signal.aborted) return
      if (Array.isArray(result)) { setSuggestions(result); setDidYouMean(null) }
      else { setSuggestions(result?.results || []); setDidYouMean(result?.did_you_mean || null) }
    } catch { if (!controller.signal.aborted) setSuggestions([]) }
    finally { if (!controller.signal.aborted) setLoadingSug(false) }
  }, [fetchSuggestions])

  useEffect(() => {
    const timer = setTimeout(() => {
      const value = query.trim()
      
      if (fetchSuggestions && value.length >= 1) loadSuggestions(value)
      else { setSuggestions([]); setDidYouMean(null) }
      if (!value) setDidYouMean(null)
      setIsOpen(value.length >= 1)
    }, 0)
    return () => clearTimeout(timer)
  }, [query, fetchSuggestions, loadSuggestions])

  useEffect(() => {
    const close = (event) => { if (containerRef.current && !containerRef.current.contains(event.target)) setIsOpen(false) }
    document.addEventListener("mousedown", close)
    return () => document.removeEventListener("mousedown", close)
  }, [])

  const submit = (event) => {
    event.preventDefault()
    const value = query.trim()
    if (!value) return
    setIsOpen(false)
    if (onSearch) onSearch(value)
    else navigate(`/destinations?q=${encodeURIComponent(value)}`)
  }
  const chooseSuggestion = (item) => { setQuery(item.name); setIsOpen(false); navigate(item.slug ? `/destinations/${item.slug}` : `/destinations?q=${encodeURIComponent(item.name)}`) }
  const hasDropdown = isOpen && (suggestions.length > 0 || didYouMean || loadingSug)

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <form onSubmit={submit} className="relative" role="search">
        <FiSearch size={18} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-green)]" aria-hidden="true" />
        <label htmlFor={inputId} className="sr-only">Search destinations</label>
        <input id={inputId} type="search" value={query} onChange={(event) => setQuery(event.target.value)} onFocus={() => query.trim() && setIsOpen(true)} placeholder={placeholder || t("nav.search")} data-testid="destination-search" className="input-field pl-11 pr-10" autoComplete="off" />
        {query && <button type="button" onClick={() => { setQuery(""); setSuggestions([]); setIsOpen(false); onSearch?.("") }} className="absolute right-2 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-[var(--ny-radius-sm)] text-[var(--ny-text-muted)] hover:bg-[var(--ny-soft-green)] hover:text-[var(--ny-green)]" aria-label="Clear search"><FiX size={16} aria-hidden="true" /></button>}
      </form>

      <AnimatePresence>
        {hasDropdown && <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.16 }} className="absolute inset-x-0 top-full z-[70] mt-2 max-h-96 overflow-y-auto rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-white p-2 text-left shadow-[var(--ny-shadow-elevated)]">
          {didYouMean && <div className="border-b border-[var(--ny-border)] p-2"><p className="mb-1 text-xs font-semibold text-[var(--ny-text-secondary)]">Did you mean</p><button type="button" onClick={() => chooseSuggestion(didYouMean)} className="flex w-full items-center justify-between rounded-[var(--ny-radius-sm)] px-2 py-2 text-left text-sm font-semibold text-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]">{didYouMean.name}<FiArrowRight size={15} aria-hidden="true" /></button></div>}
          {suggestions.length > 0 && <div className="p-2"><div className="mb-1 flex items-center justify-between px-2 text-xs font-semibold text-[var(--ny-text-muted)]"><span>Destinations</span>{loadingSug && <span>Searching…</span>}</div>{suggestions.slice(0, 8).map((suggestion) => <button type="button" key={suggestion.id || suggestion.slug} onClick={() => chooseSuggestion(suggestion)} className="flex w-full items-center gap-3 rounded-[var(--ny-radius-sm)] px-2 py-2 text-left hover:bg-[var(--ny-soft-green)]"><span className="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-[var(--ny-radius-sm)] bg-[var(--ny-soft-green)] text-[var(--ny-green)]">{suggestion.cover_image_url ? <img src={suggestion.cover_image_url} alt="" className="h-full w-full object-cover" /> : <FiMapPin size={16} aria-hidden="true" />}</span><span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold">{suggestion.name}</span><span className="block truncate text-xs text-[var(--ny-text-secondary)]">{[suggestion.category_name, suggestion.district].filter(Boolean).join(" · ") || "Nepal"}</span></span><FiArrowRight size={15} className="shrink-0 text-[var(--ny-text-muted)]" aria-hidden="true" /></button>)}</div>}
          {loadingSug && suggestions.length === 0 && <p className="p-4 text-center text-sm text-[var(--ny-text-secondary)]">Searching destinations…</p>}
          {!loadingSug && suggestions.length === 0 && query.trim().length > 0 && <p className="p-4 text-center text-sm text-[var(--ny-text-secondary)]">Press Enter to search for “{query.trim()}”.</p>}
        </motion.div>}
      </AnimatePresence>
    </div>
  )
}

export default SearchBar
