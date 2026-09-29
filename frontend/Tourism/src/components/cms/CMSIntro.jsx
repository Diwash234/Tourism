import SafeHtml from "./SafeHtml"

const safeImageUrl = (value) => {
  const raw = String(value || "").trim()
  return (raw.startsWith("/") && !raw.startsWith("//")) || /^https?:\/\//i.test(raw) ? raw : ""
}

// Shared CMS intro block — renders the `intro` section (tolerantly matched to
// `page-intro` by usePublicConfig) for pages that previously had no CMS
// consumption at all. Renders NOTHING when the section is empty, so pages keep
// their exact current look until an admin actually writes content.
// `compact` is for placement inside a card (auth pages): no page container,
// smaller type, same content.
export default function CMSIntro({ section: s, compact = false }) {
  if (!s || (!s.title && !s.body && !s.image_url)) return null
  const imageUrl = safeImageUrl(s.image_url)
  return (
    <section className={compact ? "mt-6 border-t border-gray-100 pt-5 text-left first:mt-0 first:mb-5 first:border-t-0 first:pt-0" : "container-app pt-8 md:pt-10"} aria-label="Page introduction">
      <div className={compact ? "" : "max-w-3xl"}>
        {s.title && (
          <h2 className={compact ? "text-base font-bold text-gray-900" : "text-2xl md:text-3xl font-black tracking-tight text-gray-900"}>{s.title}</h2>
        )}
        {s.body && (
          <SafeHtml
            html={s.body}
            className={compact ? "prose prose-sm mt-2 max-w-none text-gray-600" : "prose prose-sm md:prose-base mt-3 max-w-none text-gray-600"}
          />
        )}
      </div>
      {imageUrl && (
        <img
          src={imageUrl}
          alt={s.title || "Page introduction"}
          className={compact ? "mt-3 max-h-40 w-full rounded-xl object-cover" : "mt-5 max-h-72 w-full rounded-2xl object-cover"}
        />
      )}
    </section>
  )
}
