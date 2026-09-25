import SafeHtml from "./SafeHtml"

const safeImageUrl = (value) => {
  const raw = String(value || "").trim()
  return (raw.startsWith("/") && !raw.startsWith("//")) || /^https?:\/\//i.test(raw) ? raw : ""
}

// Shared CMS intro block — renders the `intro` section (tolerantly matched to
// `page-intro` by usePublicConfig) for pages that previously had no CMS
// consumption at all. Renders NOTHING when the section is empty, so pages keep
// their exact current look until an admin actually writes content.
export default function CMSIntro({ section: s }) {
  if (!s || (!s.title && !s.body && !s.image_url)) return null
  const imageUrl = safeImageUrl(s.image_url)
  return (
    <section className="container-app pt-8 md:pt-10" aria-label="Page introduction">
      <div className="max-w-3xl">
        {s.title && (
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-gray-900">{s.title}</h2>
        )}
        {s.body && (
          <SafeHtml
            html={s.body}
            className="prose prose-sm md:prose-base mt-3 max-w-none text-gray-600"
          />
        )}
      </div>
      {imageUrl && (
        <img
          src={imageUrl}
          alt={s.title || "Page introduction"}
          className="mt-5 max-h-72 w-full rounded-2xl object-cover"
        />
      )}
    </section>
  )
}
