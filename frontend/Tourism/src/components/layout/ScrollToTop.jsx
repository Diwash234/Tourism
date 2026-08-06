import { useEffect } from "react"
import { useLocation } from "react-router-dom"

const setScrollNow = (top = 0, left = 0) => {
  if (typeof window === "undefined") return
  const html = document.documentElement
  const body = document.body
  const prevHtml = html.getAttribute("style") || ""
  const prevBody = body.getAttribute("style") || ""
  html.style.cssText = "scroll-behavior:auto !important; overflow:visible;"
  body.style.cssText = "scroll-behavior:auto !important; overflow:visible;"

  try {
    window.scrollTo(left, top)
  } catch (_) {}

  try {
    const se = document.scrollingElement || document.documentElement
    se.scrollTop = top
    se.scrollLeft = left
  } catch (_) {}

  try {
    html.scrollTop = top
    html.scrollLeft = left
  } catch (_) {}

  try {
    body.scrollTop = top
    body.scrollLeft = left
  } catch (_) {}

  html.setAttribute("style", prevHtml)
  body.setAttribute("style", prevBody)
}

const ScrollToTop = () => {
  const { pathname, hash } = useLocation()

  useEffect(() => {
    try {
      if ("scrollRestoration" in window.history) {
        window.history.scrollRestoration = "manual"
      }
    } catch (_) {}

    const id = hash.replace(/^#/, "")

    if (id) {
      const goToHash = () => {
        const el = document.getElementById(id)
        if (el) {
          try {
            el.scrollIntoView({ behavior: "smooth", block: "start" })
          } catch (_) {}
        } else {
          setScrollNow(0, 0)
        }
      }
      goToHash()
      const t1 = setTimeout(goToHash, 0)
      const t2 = setTimeout(goToHash, 150)
      return () => {
        clearTimeout(t1)
        clearTimeout(t2)
      }
    }

    setScrollNow(0, 0)
    const raf1 = requestAnimationFrame(() => setScrollNow(0, 0))
    const raf2 = requestAnimationFrame(() =>
      requestAnimationFrame(() => setScrollNow(0, 0)),
    )
    const t3 = setTimeout(() => setScrollNow(0, 0), 0)
    const t4 = setTimeout(() => setScrollNow(0, 0), 80)
    const t5 = setTimeout(() => setScrollNow(0, 0), 220)

    return () => {
      cancelAnimationFrame(raf1)
      cancelAnimationFrame(raf2)
      clearTimeout(t3)
      clearTimeout(t4)
      clearTimeout(t5)
    }
  }, [pathname, hash])

  return null
}

export default ScrollToTop
