import { useParams } from "react-router-dom"
import useSeo from "../hooks/useSeo"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSPageView from "../components/cms/CMSPageView"
import NotFound from "./NotFound"

/**
 * Renders ANY published ManagedPage by key or route slug, so an admin can
 * create a page (Admin -> CMS -> Create Page -> add sections -> Publish) and
 * it appears publicly with no code change. Custom routes (e.g.
 * /best-winter-destinations) are also served directly; see NotFound.
 */
export default function DynamicCMSPage() {
  const { slug } = useParams()
  const config = usePublicConfig()
  const page = (config.pages || []).find(
    (p) => p.key === slug || p.route === `/${slug}` || p.route === slug
  )
  useSeo({
    title: page ? page.seo_title || page.title : undefined,
    description: page?.meta_description || undefined,
    path: page ? page.route || `/${slug}` : undefined,
    noindex: page?.search_visible === false,
  })
  if (!page) {
    if (!config.loaded) return <div className="container-app min-h-[60vh] py-12" aria-busy="true" />
    return <NotFound />
  }
  return <CMSPageView page={page} />
}
