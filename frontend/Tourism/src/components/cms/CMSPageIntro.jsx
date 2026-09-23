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
export default function CMSPageIntro({ pageKey }) {
  const { block, extras } = usePublicConfig().pageCMS(pageKey, ["intro", "page-intro"])
  const section = block("intro")
  const extraSections = extras.filter((s) => s.key !== "intro" && s.key !== "page-intro")
  if (!section && extraSections.length === 0) return null
  return (
    <>
      <CMSIntro section={section} />
      {extraSections.length > 0 && (
        <div className="container-app section-space">
          <CMSExtras sections={extraSections} />
        </div>
      )}
    </>
  )
}
