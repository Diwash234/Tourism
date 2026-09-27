import { matchPath, useLocation } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"
import CMSIntro from "./CMSIntro"
import { CMSExtras } from "./CMSBlock"

/**
 * Drop-in CMS content for any page: <CMSPageIntro pageKey="emergency" />
 *
 * Self-contained (hook lives here, so consuming pages need no hook-order
 * changes). Renders:
 *   1. the page's `intro` section — tolerantly matched to the template-created
 *      `page-intro` ghost rows by usePublicConfig; renders NOTHING until an
 *      admin actually writes content, so pages keep their exact current look
 *      by default;
 *   2. every OTHER section the admin adds to this page in Website → Page
 *      Editor (hero, stats, faq, card_grid, packages, …) through the same
 *      block renderers the homepage uses — so every page in the site is
 *      fully editable from the Admin CMS, not just its intro.
 */
/** Key of the CMS page for the current URL, when it has its own content.
 *  Alias routes (e.g. /login/user, /safety, the staff tabs) have their own
 *  records; they use the shared page's content until an admin gives them
 *  sections of their own. */
export const routePageKey = (pages, pathname, fallbackKey) => {
  const list = pages || []
  const own = list.find((p) => p.route === pathname)
    || list.find((p) => p.route && p.route.includes(":") && matchPath(p.route, pathname))
  return own && own.key !== fallbackKey && own.sections?.length ? own.key : fallbackKey
}

export default function CMSPageIntro({ pageKey, compact = false }) {
  const config = usePublicConfig()
  const { pathname } = useLocation()
  const { block, extras } = config.pageCMS(routePageKey(config.pages, pathname, pageKey), ["intro", "page-intro"])
  const section = block("intro")
  const extraSections = extras.filter((s) => s.key !== "intro" && s.key !== "page-intro")
  if (!section && extraSections.length === 0) return null
  return (
    <>
      <CMSIntro section={section} compact={compact} />
      {extraSections.length > 0 && (
        <div className={compact ? "mt-4 text-left" : "container-app section-space"}>
          <CMSExtras sections={extraSections} />
        </div>
      )}
    </>
  )
}
