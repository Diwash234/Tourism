// Shared CMS intro block — renders the `intro` section (tolerantly matched to
// `page-intro` by usePublicConfig) for pages that previously had no CMS
// consumption at all. Renders NOTHING when the section is empty, so pages keep
// their exact current look until an admin actually writes content.
export default function CMSIntro({ section: s }) {
  if (!s || (!s.title && !s.body && !s.image_url)) return null
  const config = s.config || {}
  const hexOk = (v) => typeof v === "string" && /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)
  const style = {}
  if (hexOk(config.custom_color)) style.color = config.custom_color
  if (hexOk(config.custom_bg)) style.background = config.custom_bg
  return (
    <section className="container-app pt-8 md:pt-10" style={Object.keys(style).length ? style : undefined} aria-label="Page introduction">
      <div className="max-w-3xl">
        {s.title && (
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-gray-900">{s.title}</h2>
        )}
        {s.body && (
          <div
            className="prose prose-sm md:prose-base mt-3 max-w-none text-gray-600"
            dangerouslySetInnerHTML={{ __html: s.body }}
          />
        )}
      </div>
      {s.image_url && (
        <img
          src={s.image_url}
          alt={s.title || "Page introduction"}
          className="mt-5 max-h-72 w-full rounded-2xl object-cover"
        />
      )}
    </section>
  )
}
