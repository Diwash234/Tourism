import { useEffect, useState, useCallback } from "react"

const listeners = new Set()
let openState = false

export const setSidebarOpen = (next) => {
  openState = typeof next === "function" ? next(openState) : !!next
  listeners.forEach((fn) => fn(openState))
}

export const toggleSidebar = () => setSidebarOpen((v) => !v)

const useSidebarState = () => {
  const [open, setOpen] = useState(openState)

  useEffect(() => {
    const onChange = (v) => setOpen(v)
    listeners.add(onChange)
    return () => listeners.delete(onChange)
  }, [])

  const setValue = useCallback((next) => setSidebarOpen(next), [])
  const toggle = useCallback(() => setSidebarOpen((v) => !v), [])

  return [open, setValue, toggle]
}

export default useSidebarState
