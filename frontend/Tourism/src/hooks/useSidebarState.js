import { useEffect, useState, useCallback } from "react"

// Sidebar state store, decoupled from viewport state (brief §25).
//
// Semantics:
//   Desktop (>= lg): the sidebar is a docked rail; `open` decides docked vs
//     hidden and MainLayout mirrors it with lg:pl-* padding.
//   Mobile (< lg): the sidebar is an overlay drawer; `open` decides whether
//     the drawer covers content, with a backdrop + body scroll lock.
//
// A matchMedia listener (not device detection, not a one-shot innerWidth
// read) keeps behavior correct across live resizes, split-screen, orientation
// changes and zoom:
//   crossing INTO desktop  -> drawer state is stale mobile state, so the
//     docked sidebar becomes visible again and any scroll lock is released;
//   crossing INTO mobile   -> stale desktop-open state must not cover content,
//     so the drawer starts closed.
// The user's icon-rail `collapsed` preference is viewport-independent and
// persists across crossings.

const DESKTOP_QUERY = "(min-width: 1024px)"
const COLLAPSE_KEY = "ny_sidebar_collapsed"
const BODY_CLASS = "sidebar-open"

const isDesktopNow = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia(DESKTOP_QUERY).matches

const listeners = new Set()

// Correct initial state per current viewport: docked+visible on desktop,
// closed drawer on mobile (never cover content on first load).
let openState = isDesktopNow()

let collapsedState = false
try {
  collapsedState = typeof window !== "undefined" && window.localStorage?.getItem(COLLAPSE_KEY) === "1"
} catch { /* localStorage unavailable */ }

const applyBodyClass = (open) => {
  if (typeof document === "undefined") return
  const el = document.body
  // Scroll lock only ever applies to the mobile drawer; the desktop rail is
  // a layout column and must not lock page scroll.
  if (open && !isDesktopNow()) el.classList.add(BODY_CLASS)
  else el.classList.remove(BODY_CLASS)
}

const notify = () => listeners.forEach((fn) => fn())

export const setSidebarOpen = (next) => {
  openState = typeof next === "function" ? next(openState) : !!next
  applyBodyClass(openState)
  notify()
}

export const setSidebarCollapsed = (next) => {
  collapsedState = typeof next === "function" ? next(collapsedState) : !!next
  try {
    window.localStorage?.setItem(COLLAPSE_KEY, collapsedState ? "1" : "0")
  } catch { /* ignore */ }
  notify()
}

export const toggleSidebar = () => setSidebarOpen((v) => !v)
export const closeSidebar = () => setSidebarOpen(false)
export const openSidebar = () => setSidebarOpen(true)
export const toggleSidebarCollapsed = () => setSidebarCollapsed((v) => !v)

// One viewport listener for the entire store (brief §30: no per-component
// resize listeners). Crossing a breakpoint normalizes the open state so no
// stale mobile/desktop state survives the transition.
let viewportHooked = false
const hookViewport = () => {
  if (viewportHooked) return
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return
  viewportHooked = true
  const mql = window.matchMedia(DESKTOP_QUERY)
  mql.addEventListener("change", (event) => {
    openState = event.matches // desktop: rail visible; mobile: drawer closed
    applyBodyClass(openState)
    notify()
  })
}

// Escape closes the drawer anywhere in the app (brief §7 / §29).
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
  const [collapsed, setCollapsed] = useState(collapsedState)

  useEffect(() => {
    hookViewport()
    applyBodyClass(openState)
    const sync = () => {
      setOpen(openState)
      setCollapsed(collapsedState)
    }
    sync()
    listeners.add(sync)
    return () => listeners.delete(sync)
  }, [])

  const setValue = useCallback((next) => setSidebarOpen(next), [])
  const toggle = useCallback(() => setSidebarOpen((v) => !v), [])
  const close = useCallback(() => setSidebarOpen(false), [])
  const setCollapsedValue = useCallback((next) => setSidebarCollapsed(next), [])
  const toggleCollapsed = useCallback(() => setSidebarCollapsed((v) => !v), [])

  // Extended tuple — existing `const [open, setValue, toggle, close] = …`
  // destructuring keeps working unchanged.
  return [open, setValue, toggle, close, collapsed, setCollapsedValue, toggleCollapsed]
}

export default useSidebarState
