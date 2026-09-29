import { useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"

/**
 * Global keyboard shortcuts for power users.
 * Ctrl+K: Focus search | Ctrl+D: Toggle theme | Ctrl+/: Show shortcuts
 * g then d: Go to dashboard | g then h: Go to home | g then e: Go to explore
 */
export default function useKeyboardShortcuts() {
  const navigate = useNavigate()

  const handleKeyDown = useCallback((e) => {
    // Ctrl+K — focus search
    if (e.ctrlKey && e.key === "k") {
      e.preventDefault()
      const searchInput = document.querySelector('input[type="search"]')
      if (searchInput) {
        searchInput.focus()
        searchInput.select()
      }
      return
    }

    // Ctrl+D — toggle theme
    if (e.ctrlKey && e.key === "d") {
      e.preventDefault()
      const themeToggle = document.querySelector('[aria-label*="theme"], [aria-label*="Switch to"]')
      if (themeToggle) themeToggle.click()
      return
    }

    // Ctrl+/ — show keyboard shortcuts help
    if (e.ctrlKey && e.key === "/") {
      e.preventDefault()
      const event = new CustomEvent("ny:show-shortcuts")
      window.dispatchEvent(event)
      return
    }

    // g then d — Go to dashboard
    if (e.key === "g" && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const handler = (ev) => {
        if (ev.key === "d") {
          e.preventDefault()
          navigate("/dashboard")
        } else if (ev.key === "h") {
          e.preventDefault()
          navigate("/")
        } else if (ev.key === "e") {
          e.preventDefault()
          navigate("/destinations")
        } else if (ev.key === "p") {
          e.preventDefault()
          navigate("/itinerary")
        }
        window.removeEventListener("keydown", handler, true)
      }
      window.addEventListener("keydown", handler, true)
      setTimeout(() => window.removeEventListener("keydown", handler, true), 1500)
    }
  }, [navigate])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])
}
