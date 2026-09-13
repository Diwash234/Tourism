import { useEffect } from "react"
import { useParams, Navigate } from "react-router-dom"
import usePublicConfig from "../hooks/usePublicConfig"
import { CMSExtras } from "../components/cms/CMSBlock"

/**
 * Renders ANY published ManagedPage by key or route slug — the proof that an
 * admin can create a new page (Admin → CMS → Create Page → add sections →
 * Publish) and it appears publicly with NO React code change. Sections render
 * through the same controlled registry the home page uses (spec §50-51).
 */
export default function DynamicCMSPage() {
  const { slug } = useParams()
  const config = usePublicConfig()
  const page = (config.pages || []).find(
    (p) => p.key === slug || p.route === `/${slug}` || p.route === slug
  )
  // SEO: title/meta straight from the CMS record (spec §28).
  useEffect(() => {
    if (!page) return
    document.title = page.seo_title || page.title || "Nepal Yatra"
    let tag = document.querySelector('meta[name="description"]')
    if (!tag) { tag = document.createElement("meta"); tag.name = "description"; document.head.appendChild(tag) }
    tag.content = page.meta_description || ""
  }, [page])
  if (!page) return <Navigate to="/404" replace />
  const sections = (page.sections || [])
    .slice()
    .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
  return (
    <main className="min-h-screen bg-white">
      <header className="container-app pt-28 pb-8 text-center">
        <h1 className="text-3xl md:text-4xl font-black text-slate-900">{page.title}</h1>
        {page.meta_description && (
          <p className="mt-3 text-sm text-slate-600 max-w-2xl mx-auto">{page.meta_description}</p>
        )}
      </header>
      <CMSExtras sections={sections} />
    </main>
  )
}
