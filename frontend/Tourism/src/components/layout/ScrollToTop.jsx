import { useEffect } from "react"
import { useLocation } from "react-router-dom"

const ScrollToTop = () => {
  const { pathname, search, hash } = useLocation()

  useEffect(() => {
    try {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual"
      }
    } catch (_) {}

    const id = hash.replace(/^#/, "")

    if (id) {
      const el = document.getElementById(id)
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" })
        return
      }
    }

    // Always scroll window to absolute top-left on navigation
    window.scrollTo({ top: 0, left: 0, behavior: "instant" })
    document.documentElement.scrollTop = 0
    document.body.scrollTop = 0

    const t1 = setTimeout(() => {
      window.scrollTo({ top: 0, left: 0, behavior: "instant" })
      document.documentElement.scrollTop = 0
      document.body.scrollTop = 0
    }, 50)

    return () => clearTimeout(t1)
  }, [pathname, search, hash])

  return null
}

export default ScrollToTop
