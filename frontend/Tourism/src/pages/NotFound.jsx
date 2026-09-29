import { Link, useLocation } from "react-router-dom"
import { FiCompass, FiHome } from "react-icons/fi"
import { FadeIn } from "../components/common/MotionSystem"
import useSeo from "../hooks/useSeo"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSPageView from "../components/cms/CMSPageView"
import CMSPageIntro from "../components/cms/CMSPageIntro"

export default function NotFound() {
  const config = usePublicConfig()
  const { pathname } = useLocation()
  // A page an admin created in the CMS with its own route (for example
  // /best-winter-destinations) has no React route, so it lands here. Serve it
  // instead of a 404.
  const cmsPage = (config.pages || []).find((p) => p.route === pathname && !p.route.includes(":"))
  const waiting = !cmsPage && !config.loaded
  // Soft 404 for an SPA: keep it out of search results.
  useSeo(cmsPage
    ? { title: cmsPage.seo_title || cmsPage.title, description: cmsPage.meta_description || undefined, path: cmsPage.route, noindex: cmsPage.search_visible === false }
    : { title: waiting ? undefined : "Page not found", description: waiting ? undefined : "This page does not exist on Nepal Yatra.", noindex: true })
  if (cmsPage) return <CMSPageView page={cmsPage} />
  if (waiting) return <div className="container-app min-h-[60vh] py-12" aria-busy="true" />
  return (
    <>
    <div className="ny-page min-h-[75vh] flex items-center justify-center container-app section-space px-4">
      <FadeIn className="ny-panel mx-auto max-w-xl space-y-6 p-8 text-center sm:p-12">
        <div className="relative inline-block">
          <span className="text-7xl font-black text-[var(--ny-green)]">404</span>
          <span className="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-[var(--ny-soft-green)] px-3 py-0.5 text-xs font-bold text-[var(--ny-green-dark)]">Page not found</span>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-[var(--ny-text)]">
            We couldn't find that page
          </h1>
          <p className="text-sm text-[var(--ny-text-secondary)] max-w-md mx-auto leading-relaxed">
            The link may be outdated or the page may have moved. Browse the live catalogue to continue exploring Nepal.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            to="/"
            className="ny-btn ny-btn-primary w-full justify-center sm:w-auto"
          >
            <FiHome size={16} aria-hidden="true" /> Return to Home
          </Link>
          <Link
            to="/destinations"
            className="ny-btn ny-btn-secondary w-full justify-center sm:w-auto"
          >
            <FiCompass size={16} aria-hidden="true" /> Explore Destinations
          </Link>
        </div>
      </FadeIn>
    </div>
    <CMSPageIntro pageKey="not-found" />
    </>
  )
}
