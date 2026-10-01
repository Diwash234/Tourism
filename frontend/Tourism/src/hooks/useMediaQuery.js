import { useState, useEffect } from "react"

/**
 * useMediaQuery — reactive media query hook.
 * Returns true when the query matches, false otherwise.
 */
export default function useMediaQuery(query) {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined") return false
    return window.matchMedia(query).matches
  })
  const [prevQuery, setPrevQuery] = useState(query)

  // Adjust during render when the query prop changes (React's documented
  // pattern) — a synchronous setState inside the effect is banned by
  // react-hooks/set-state-in-effect.
  if (query !== prevQuery) {
    setPrevQuery(query)
    setMatches(typeof window === "undefined" ? false : window.matchMedia(query).matches)
  }

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = (e) => setMatches(e.matches)
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [query])

  return matches
}
