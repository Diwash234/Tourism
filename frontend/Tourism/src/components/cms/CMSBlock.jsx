const embedUrl = (url = "") => {
  if (/youtube\.com\/watch\?v=/.test(url)) return url.replace("watch?v=", "embed/")
  if (/youtu\.be\//.test(url)) return url.replace("youtu.be/", "www.youtube.com/embed/")
  if (/vimeo\.com\/\d+/.test(url)) return url.replace("vimeo.com/", "player.vimeo.com/video/")
  return url
}

const effectClass = (effect) => ({
  marquee: "animate-pulse",
  fade: "animate-fadeIn",
  slide: "animate-fadeIn",
}[effect] || "")

export default function CMSBlock({ section }) {
  if (!section) return null
  const type = section.section_type || "text"
  const config = section.config || {}
  const media = config.media_url || section.image_url
  const layout = section.layout_variant === "hero"
    ? "rounded-3xl bg-emerald-950 text-white p-8"
    : section.layout_variant === "split"
      ? "grid gap-6 md:grid-cols-2 rounded-3xl border border-emerald-100 bg-white p-6"
      : "rounded-3xl border border-emerald-100 bg-white p-6"
  return (
    <article className={`${layout} ${effectClass(config.effect)}`}>
      {section.title && <h2 className="text-2xl font-black tracking-tight">{section.title}</h2>}
      {section.subtitle && <p className="mt-1 text-sm opacity-80">{section.subtitle}</p>}
      {type === "marquee" && (
        <div className="mt-4 overflow-hidden whitespace-nowrap rounded-xl bg-emerald-50 py-3 text-emerald-900">
          <p className="inline-block min-w-full animate-pulse px-4 text-sm font-bold">{section.body}</p>
        </div>
      )}
      {type === "heading" && section.body && <p className="mt-3 text-base opacity-90">{section.body}</p>}
      {["text", "animation", "cards", "faq"].includes(type) && section.body && (
        <div className="prose prose-sm mt-3 max-w-none" dangerouslySetInnerHTML={{ __html: section.body }} />
      )}
      {type === "image" && media && <img src={media} alt="" className="mt-4 max-h-80 w-full rounded-2xl object-cover" />}
      {type === "gallery" && media && <img src={media} alt="" className="mt-4 max-h-64 w-full rounded-2xl object-cover" />}
      {type === "video" && media && (
        media.includes("youtube") || media.includes("vimeo") || media.includes("youtu.be")
          ? <iframe title={section.title || "Video"} src={embedUrl(media)} className="mt-4 aspect-video w-full rounded-2xl" allow="accelerometer; autoplay; encrypted-media; picture-in-picture" allowFullScreen />
          : <video src={media} controls className="mt-4 w-full rounded-2xl" />
      )}
      {type === "audio" && media && <audio src={media} controls className="mt-4 w-full" />}
      {type === "media" && media && (
        config.media_kind === "audio"
          ? <audio src={media} controls className="mt-4 w-full" />
          : config.media_kind === "video"
            ? <video src={media} controls className="mt-4 w-full rounded-2xl" />
            : <img src={media} alt="" className="mt-4 max-h-80 w-full rounded-2xl object-cover" />
      )}
      {section.cta_text && section.cta_url && (
        <a href={section.cta_url} className="mt-4 inline-flex rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white">{section.cta_text}</a>
      )}
    </article>
  )
}

export function CMSExtras({ sections = [] }) {
  if (!sections.length) return null
  return (
    <div className="space-y-6">
      {sections.map((section) => <CMSBlock key={section.id || section.key} section={section} />)}
    </div>
  )
}
