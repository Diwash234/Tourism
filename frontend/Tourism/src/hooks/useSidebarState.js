import { useEffect, useState, useCallback } from "react"

const listeners = new Set()
// Mobile-only drawer state. On desktop (lg+) the sidebar is always visible
// regardless of this flag -- the CSS handles that.
let openState = false

const BODY_CLASS = "sidebar-open"

const applyBodyClass = (open) => {
  if (typeof document === "undefined") return
  const el = document.body
  if (open) el.classList.add(BODY_CLASS)
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
