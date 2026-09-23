import { useCallback, useSyncExternalStore } from "react"

/**
 * Single reusable viewport hook for the whole app (brief §24: one responsive
 * detection system, no scattered window.innerWidth/resize listeners and no
 * device/userAgent sniffing — behavior keys off available viewport width).
 *
 *   const isDesktop = useMediaQuery("(min-width: 1024px)")
 *
 * Built on useSyncExternalStore: subscribes to the MediaQueryList directly,
 * so it is render-safe (no effect-phase setState) and tearing-free.
 */
export default function useMediaQuery(query) {
  const subscribe = useCallback(
    (onChange) => {
      const mql = window.matchMedia(query)
      mql.addEventListener("change", onChange)
      return () => mql.removeEventListener("change", onChange)
    },
    [query]
  )

  const getSnapshot = useCallback(() => window.matchMedia(query).matches, [query])
  const getServerSnapshot = useCallback(() => false, [])

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
