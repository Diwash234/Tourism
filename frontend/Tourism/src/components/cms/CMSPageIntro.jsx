import usePublicConfig from "../../hooks/usePublicConfig"
import CMSIntro from "./CMSIntro"

/**
 * Drop-in CMS intro for any page: <CMSPageIntro pageKey="emergency" />
 * Self-contained (hook lives here, so consuming pages need no hook-order
 * changes). Renders the page's `intro` section — tolerantly matched to the
 * template-created `page-intro` ghost rows by usePublicConfig — and renders
 * NOTHING until an admin actually writes content, so pages keep their exact
 * current look by default.
 */
export default function CMSPageIntro({ pageKey }) {
  const { block } = usePublicConfig().pageCMS(pageKey, ["intro", "page-intro"])
  return <CMSIntro section={block("intro")} />
}
