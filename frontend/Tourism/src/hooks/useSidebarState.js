import { useEffect, useState, useCallback } from "react"

// Sidebar state store — three-state navigation model (brief §42):
//
//   Desktop (>= lg):  open=true  -> expanded rail (labels visible)
//                     open=false -> collapsed icon rail (icons only, still
//                                   clickable, still takes layout space)
//   Mobile  (< lg):   open=true  -> overlay drawer + backdrop + scroll lock
//                     open=false -> drawer closed, content full width
//
// The desktop rail is NEVER fully hidden: content always reserves either the
// expanded or the collapsed rail width, so the hamburger and the sidebar's
// own chevron toggle the same understandable state and content width always
// matches the visible sidebar width (brief §3/§24).
//
// The preference persists (brief §8) and viewport crossings normalize state
// (brief §43): entering desktop restores the saved rail preference; entering
// mobile always starts with the drawer closed. Detection uses matchMedia —
// viewport width, never device sniffing (brief §9).

const DESKTOP_QUERY = "(min-width: 1024px)"
const OPEN_KEY = "ny_sidebar_open"
const LEGACY_COLLAPSE_KEY = "ny_sidebar_collapsed"
const BODY_CLASS = "sidebar-open"

const isDesktopNow = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia(DESKTOP_QUERY).matches

const readPersistedOpen = () => {
  try {
    const stored = window.localStorage?.getItem(OPEN_KEY)
    if (stored !== null) return stored === "1"
    // Migrate the older "collapsed" preference: collapsed === closed rail.
    const legacy = window.localStorage?.getItem(LEGACY_COLLAPSE_KEY)
    if (legacy !== null) return legacy !== "1"
  } catch { /* localStorage unavailable */ }
  return true
}

// Correct initial state per current viewport: saved rail preference on
// desktop, closed drawer on mobile (never cover content on first load).
let openState = typeof window === "undefined" ? true : (isDesktopNow() ? readPersistedOpen() : false)

const persistOpen = () => {
  try {
    window.localStorage?.setItem(OPEN_KEY, openState ? "1" : "0")
  } catch { /* ignore */ }
}

const applyBodyClass = (open) => {
  if (typeof document === "undefined") return
  const el = document.body
  // Scroll lock only ever applies to the mobile drawer; the desktop rail is
  // a layout column and must not lock page scroll.
  if (open && !isDesktopNow()) el.classList.add(BODY_CLASS)
  else el.classList.remove(BODY_CLASS)
}

const listeners = new Set()
const notify = () => listeners.forEach((fn) => fn())

export const setSidebarOpen = (next) => {
  openState = typeof next === "function" ? next(openState) : !!next
  if (typeof window !== "undefined") {
    persistOpen()
    applyBodyClass(openState)
  }
  notify()
}

export const toggleSidebar = () => setSidebarOpen((v) => !v)
export const closeSidebar = () => setSidebarOpen(false)
export const openSidebar = () => setSidebarOpen(true)

// Back-compat aliases: "collapsed" is now simply the closed desktop rail,
// so the old API keeps working with consistent semantics.
export const setSidebarCollapsed = (next) => {
  const collapsed = typeof next === "function" ? next(!openState) : !!next
  setSidebarOpen(!collapsed)
}
export const toggleSidebarCollapsed = () => setSidebarOpen((v) => !v)

// One viewport listener for the entire store (brief §30: no per-component
// resize listeners). Crossing a breakpoint normalizes the open state so no
// stale mobile/desktop state survives the transition (brief §43).
let viewportHooked = false
const hookViewport = () => {
  if (viewportHooked) return
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return
  viewportHooked = true
  const mql = window.matchMedia(DESKTOP_QUERY)
  mql.addEventListener("change", (event) => {
    // desktop: restore saved rail preference; mobile: drawer always closed
    openState = event.matches ? readPersistedOpen() : false
    applyBodyClass(openState)
    notify()
  })
}

// Escape closes the mobile drawer anywhere in the app (brief §35/§36).
const hookEscape = () => {
  if (typeof window === "undefined") return
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && openState && !isDesktopNow()) closeSidebar()
  })
}

if (typeof window !== "undefined") {
  hookViewport()
  hookEscape()
}

const useSidebarState = () => {
  const [open, setOpen] = useState(openState)

  useEffect(() => {
    hookViewport()
    applyBodyClass(openState)
    const sync = () => setOpen(openState)
    sync()
    listeners.add(sync)
    return () => listeners.delete(sync)
  }, [])

  const setValue = useCallback((next) => setSidebarOpen(next), [])
  const toggle = useCallback(() => setSidebarOpen((v) => !v), [])
  const close = useCallback(() => setSidebarOpen(false), [])
  const setCollapsedValue = useCallback((next) => setSidebarCollapsed(next), [])
  const toggleCollapsed = useCallback(() => setSidebarOpen((v) => !v), [])

  // Extended tuple — existing `const [open, setValue, toggle, close] = …`
  // destructuring keeps working unchanged. Position 4 (`collapsed`) is the
  // closed desktop rail, i.e. !open.
  return [open, setValue, toggle, close, !open, setCollapsedValue, toggleCollapsed]
}

export default useSidebarState
