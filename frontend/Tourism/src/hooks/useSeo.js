import { useEffect } from "react"

/**
 * Per-page SEO metadata (§101/§104). Sets document title, meta description,
 * canonical URL, Open Graph tags and factual JSON-LD structured data.
 *
 * Everything is derived from real database records passed in by the page —
 * no fabricated ratings, prices or coordinates. Tags created by this hook
 * are marked data-seo="1" and removed when the page unmounts so SPA
 * navigation never leaks metadata between pages.
 */

const upsertMeta = (attr, key, content) => {
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (content === null || content === undefined || content === "") {
    // Only remove tags this hook created; leave index.html defaults intact.
    if (el && el.dataset.seo === "1") el.remove()
    return
  }
  if (!el) {
    el = document.createElement("meta")
    el.setAttribute(attr, key)
    el.dataset.seo = "1"
    document.head.appendChild(el)
  }
  el.setAttribute("content", content)
}

export default function useSeo({
  title,
  description,
  path,
  image,
  type = "website",
  noindex = false,
  jsonLd = null,
} = {}) {
  // Serialize so object identity churn doesn't retrigger the effect.
  const jsonLdText = jsonLd ? JSON.stringify(jsonLd) : null
  useEffect(() => {
    const prevTitle = document.title
    let canonical = document.head.querySelector('link[rel="canonical"]')
    const createdCanonical = !canonical

    if (title) document.title = title
    upsertMeta("name", "description", description || null)
    upsertMeta("name", "robots", noindex ? "noindex, nofollow" : null)
    upsertMeta("property", "og:title", title || null)
    upsertMeta("property", "og:description", description || null)
    upsertMeta("property", "og:type", type)
    upsertMeta("property", "og:image", image || null)

    if (path) {
      const href = `${window.location.origin}${path}`
      if (!canonical) {
        canonical = document.createElement("link")
        canonical.rel = "canonical"
        canonical.dataset.seo = "1"
        document.head.appendChild(canonical)
      }
      canonical.href = href
      upsertMeta("property", "og:url", href)
    }

    let script = null
    if (jsonLdText) {
      script = document.createElement("script")
      script.type = "application/ld+json"
      script.dataset.seo = "1"
      script.textContent = jsonLdText
      document.head.appendChild(script)
    }

    return () => {
      document.title = prevTitle
      if (script) script.remove()
      if (createdCanonical && canonical) canonical.remove()
      for (const sel of ['meta[name="description"]', 'meta[name="robots"]',
        'meta[property="og:title"]', 'meta[property="og:description"]',
        'meta[property="og:url"]', 'meta[property="og:image"]']) {
        document.head.querySelectorAll(sel).forEach((el) => {
          if (el.dataset.seo === "1") el.remove()
        })
      }
    }
  }, [title, description, path, image, type, noindex, jsonLdText])
}
