import { useEffect, useState, useCallback } from "react"

const listeners = new Set()
// `open` drives the drawer everywhere: on mobile it slides over content, on
// desktop (lg+) hiding it also removes the content padding (lg:pl-64 -> 0).
let openState = true

// Desktop icon-rail collapse (persisted). When collapsed at lg+, the sidebar
// narrows to a 64px icon rail instead of the full 256px panel.
const COLLAPSE_KEY = "ny_sidebar_collapsed"
let collapsedState = false
try {
  collapsedState = typeof window !== "undefined" && window.localStorage?.getItem(COLLAPSE_KEY) === "1"
} catch { /* localStorage unavailable */ }

const BODY_CLASS = "sidebar-open"

const applyBodyClass = (open) => {
  if (typeof document === "undefined") return
  const el = document.body
  // Body class (scroll lock) only matters for the mobile drawer; on desktop the
  // sidebar is an inline column and must not lock page scroll.
  const mobile = typeof window !== "undefined" && window.innerWidth < 1024
  if (open && mobile) el.classList.add(BODY_CLASS)
  else el.classList.remove(BODY_CLASS)
}

export const setSidebarOpen = (next) => {
  openState = typeof next === "function" ? next(openState) : !!next
  applyBodyClass(openState)
  listeners.forEach((fn) => fn())
}

export const setSidebarCollapsed = (next) => {
  collapsedState = typeof next === "function" ? next(collapsedState) : !!next
  try {
    window.localStorage?.setItem(COLLAPSE_KEY, collapsedState ? "1" : "0")
  } catch { /* ignore */ }
  listeners.forEach((fn) => fn())
}

export const toggleSidebar = () => setSidebarOpen((v) => !v)
export const closeSidebar = () => setSidebarOpen(false)
export const openSidebar = () => setSidebarOpen(true)
export const toggleSidebarCollapsed = () => setSidebarCollapsed((v) => !v)

const useSidebarState = () => {
  const [open, setOpen] = useState(openState)
  const [collapsed, setCollapsed] = useState(collapsedState)

  useEffect(() => {
    applyBodyClass(openState)
    const sync = () => {
      setOpen(openState)
      setCollapsed(collapsedState)
    }
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
