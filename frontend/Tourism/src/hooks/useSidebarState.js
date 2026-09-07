import { useEffect, useState, useCallback } from "react"

const listeners = new Set()
// Mobile-only drawer state. On desktop (lg+) the sidebar is always visible
// regardless of this flag -- the CSS handles that.
let openState = true

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
  listeners.forEach((fn) => fn(openState))
}

export const toggleSidebar = () => setSidebarOpen((v) => !v)
export const closeSidebar = () => setSidebarOpen(false)
export const openSidebar = () => setSidebarOpen(true)

const useSidebarState = () => {
  const [open, setOpen] = useState(openState)

  useEffect(() => {
    applyBodyClass(openState)
    const onChange = (v) => setOpen(v)
    listeners.add(onChange)
    return () => listeners.delete(onChange)
  }, [])

  const setValue = useCallback((next) => setSidebarOpen(next), [])
  const toggle = useCallback(() => setSidebarOpen((v) => !v), [])
  const close = useCallback(() => setSidebarOpen(false), [])

  return [open, setValue, toggle, close]
}

export default useSidebarState
