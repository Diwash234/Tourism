import { useEffect } from "react"
import { matchPath, useLocation } from "react-router-dom"
import usePublicConfig from "./usePublicConfig"
import { pageSeoActive } from "./useSeo"
import { DEFAULT_DESCRIPTION, ROUTE_SEO, formatTitle } from "../utils/seoRoutes"

const setMeta = (attr, key, value) => {
  if (!value) return
  let element = document.querySelector(`meta[${attr}="${key}"]`)
  if (!element) {
    element = document.createElement("meta")
    element.setAttribute(attr, key)
    document.head.appendChild(element)
  }
  element.setAttribute("content", value)
}

/** Route-level title/description/canonical defaults for a layout. */
export default function useRouteSeo() {
  const location = useLocation()
  const { pages, branding } = usePublicConfig()
  useEffect(() => {
    // A page that calls useSeo() owns its metadata (its effect runs before
    // this parent effect); otherwise: CMS page record, then the route
    // defaults, then the site default. One writer per page, never both.
    if (pageSeoActive()) return
    const path = location.pathname
    const matches = (route) => route && route !== "*" && (route === path || (route.includes(":") && matchPath(route, path)))
    const page = (pages || []).find((item) => item.route === path) || (pages || []).find((item) => matches(item.route))
    const fallbackKey = Object.keys(ROUTE_SEO).find((route) => matches(route))
    const fallback = ROUTE_SEO[fallbackKey] || {}
    const cmsTitle = page?.seo_title || (page?.route === "/" ? "" : page?.title)
    document.title = fallback.full ? fallback.title : formatTitle(cmsTitle || fallback.title)
    const description = page?.meta_description || fallback.description || DEFAULT_DESCRIPTION
    setMeta("name", "description", description)
    setMeta("property", "og:title", document.title)
    setMeta("property", "og:description", description)
    if (page?.og_image_url) setMeta("property", "og:image", page.og_image_url)
    let canonical = document.head.querySelector('link[rel="canonical"]')
    if (!canonical) { canonical = document.createElement("link"); canonical.rel = "canonical"; document.head.appendChild(canonical) }
    canonical.href = `${window.location.origin}${path}`
    setMeta("property", "og:url", canonical.href)
    if (page?.search_visible === false || fallback.noindex) setMeta("name", "robots", "noindex,nofollow")
    else document.querySelector('meta[name="robots"]')?.remove()
  }, [location.pathname, pages, branding])
}
