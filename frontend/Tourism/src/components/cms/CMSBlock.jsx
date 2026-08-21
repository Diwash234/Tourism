import { useState } from "react"

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

const FIELD_TYPES = new Set(["text", "email", "tel", "textarea", "select", "checkbox"])

export default function CMSBlock({ section }) {
  if (!section) return null
  const type = section.section_type || "text"
  const config = section.config || {}
  const media = config.media_url || section.image_url
  const fields = Array.isArray(config.fields) ? config.fields.filter((field) => FIELD_TYPES.has(field.field_type || "text")) : []
  const [sent, setSent] = useState("")
  const layout = section.layout_variant === "hero"
    ? "rounded-3xl bg-emerald-950 text-white p-8"
    : section.layout_variant === "split"
      ? "grid gap-6 md:grid-cols-2 rounded-3xl border border-emerald-100 bg-white p-6 text-slate-900"
      : "rounded-3xl border border-emerald-100 bg-white p-6 text-slate-900"
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
      {["text", "animation", "cards", "faq", "testimonials", "contact"].includes(type) && section.body && (
        <div className="prose prose-sm mt-3 max-w-none" dangerouslySetInnerHTML={{ __html: section.body }} />
      )}
      {type === "image" && media && <img src={media} alt="" className="mt-4 max-h-80 w-full rounded-2xl object-cover" />}
      {type === "gallery" && media && <img src={media} alt="" className="mt-4 max-h-64 w-full rounded-2xl object-cover" />}
      {type === "figure" && media && (
        <figure className="mt-4">
          <img src={media} alt="" className="max-h-80 w-full rounded-2xl object-cover" />
          {section.body && <figcaption className="mt-2 text-xs text-slate-500">{section.body}</figcaption>}
        </figure>
      )}
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
      {type === "search" && (
        <form action="/destinations" className="mt-4 flex gap-2">
          <input name="q" className="input-field" placeholder={section.body || "Search destinations"} />
          <button className="rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white">Search</button>
        </form>
      )}
      {type === "breadcrumbs" && Array.isArray(config.items) && (
        <nav className="mt-3 text-xs text-slate-600">{config.items.map((item) => item.label || item).filter(Boolean).join(" / ")}</nav>
      )}
      {type === "table" && Array.isArray(config.rows) && (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-sm">
            {Array.isArray(config.headers) && <thead><tr>{config.headers.map((header) => <th key={header} className="border-b p-2 text-left">{header}</th>)}</tr></thead>}
            <tbody>{config.rows.map((row, index) => <tr key={index}>{(Array.isArray(row) ? row : [row]).map((cell, cellIndex) => <td key={cellIndex} className="border-b p-2">{cell}</td>)}</tr>)}</tbody>
          </table>
        </div>
      )}
      {type === "form" && (
        <form className="mt-4 space-y-3" onSubmit={async (event) => {
          event.preventDefault()
          const form = new FormData(event.target)
          const message = fields.map((field) => `${field.label}: ${form.get(field.name) || ""}`).join("\n")
          try {
            await fetch("/api/v1/feedback", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ subject: section.title || "Page form", message, category: "general" }),
            })
            setSent("Received. An administrator will review this submission.")
            event.target.reset()
          } catch {
            setSent("Could not send the form.")
          }
        }}>
          {fields.map((field) => (
            <label key={field.name} className="block text-xs font-bold">
              {field.label}{field.required ? " *" : ""}
              {field.field_type === "textarea"
                ? <textarea name={field.name} required={field.required} className="input-field mt-1" rows="3" />
                : field.field_type === "select"
                  ? <select name={field.name} required={field.required} className="input-field mt-1">{(field.options || []).map((option) => <option key={option}>{option}</option>)}</select>
                  : field.field_type === "checkbox"
                    ? <input type="checkbox" name={field.name} className="ml-2" />
                    : <input type={field.field_type || "text"} name={field.name} required={field.required} className="input-field mt-1" />}
            </label>
          ))}
          <button type="submit" className="rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white">{section.cta_text || "Submit"}</button>
          {sent && <p className="text-xs text-emerald-800">{sent}</p>}
        </form>
      )}
      {section.cta_text && section.cta_url && type !== "form" && (
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
