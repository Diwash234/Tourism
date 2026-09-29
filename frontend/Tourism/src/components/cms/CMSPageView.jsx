import { CMSExtras } from "./CMSBlock"

/**
 * A page built entirely in Admin -> CMS (title, description, sections).
 * Used by /page/:slug and by custom routes such as /best-winter-destinations.
 * The layout already provides <main>, so this renders a plain section.
 */
export default function CMSPageView({ page }) {
  const sections = (page.sections || [])
    .slice()
    .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
  return (
    <div className="ny-page min-h-[60vh] bg-[var(--ny-bg)]" data-cms-page={page.key}>
      <header className="container-app pb-8 pt-10 text-center">
        <h1 className="text-3xl font-black text-[var(--ny-text)] md:text-4xl">{page.title}</h1>
        {page.meta_description && (
          <p className="mx-auto mt-3 max-w-2xl text-sm text-[var(--ny-text-secondary)]">{page.meta_description}</p>
        )}
      </header>
      <CMSExtras sections={sections} />
    </div>
  )
}
