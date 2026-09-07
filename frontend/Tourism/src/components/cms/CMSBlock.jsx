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

const BG_STYLES = {
  "gradient-emerald": "bg-gradient-to-br from-emerald-950 via-teal-900 to-slate-950 text-white border-emerald-800/40 shadow-xl",
  "dark-slate": "bg-slate-950 text-white border-slate-800 shadow-lg",
  "clean-white": "bg-white text-slate-900 border-emerald-100/80 shadow-sm",
  "saffron-warm": "bg-gradient-to-br from-amber-500 via-amber-400 to-amber-600 text-slate-950 border-amber-300 shadow-md",
  "hero-dark": "bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 text-white border-purple-800/30 shadow-2xl",
  "border-accent": "bg-slate-900/90 text-white border-2 border-amber-400 shadow-lg",
}

const PADDING_STYLES = {
  compact: "p-4 sm:p-5",
  medium: "p-6 sm:p-8",
  spacious: "p-8 sm:p-12",
}

const FIELD_TYPES = new Set(["text", "email", "tel", "textarea", "select", "checkbox"])

export function ContentBlockItem({ block }) {
  if (!block || block.is_visible === false) return null
  const { block_type, title, data = {} } = block

  switch (block_type) {
    case "heading": {
      const Tag = data.level || "h2"
      const align = data.align || "left"
      const color = data.color || "inherit"
      return (
        <Tag className={`font-black tracking-tight mt-4 text-${align}`} style={{ color }}>
          {title || data.text}
        </Tag>
      )
    }
    case "subheading":
      return <p className={`text-base font-bold opacity-80 mt-1 text-${data.align || "left"}`}>{title || data.text}</p>

    case "rich_text":
      return (
        <div
          className="prose prose-sm max-w-none mt-3"
          dangerouslySetInnerHTML={{ __html: data.html || data.text || block.title || "" }}
        />
      )

    case "image": {
      const url = data.url || data.image_url
      if (!url) return null
      return (
        <figure className={`mt-4 my-3 flex flex-col items-${data.align === "center" ? "center" : "start"}`}>
          {data.link ? (
            <a href={data.link} target="_blank" rel="noopener noreferrer">
              <img src={url} alt={data.alt || title || ""} className="rounded-2xl object-cover max-h-96 shadow-md" style={{ width: data.width || "100%" }} />
            </a>
          ) : (
            <img src={url} alt={data.alt || title || ""} className="rounded-2xl object-cover max-h-96 shadow-md" style={{ width: data.width || "100%" }} />
          )}
          {data.caption && <figcaption className="text-xs text-slate-500 mt-1 italic">{data.caption}</figcaption>}
        </figure>
      )
    }

    case "gallery": {
      const imgs = Array.isArray(data.images) ? data.images : []
      if (!imgs.length) return null
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
          {imgs.map((img, i) => (
            <div key={i} className="overflow-hidden rounded-2xl bg-slate-100">
              <img src={typeof img === "string" ? img : img.url} alt={img.alt || ""} className="w-full h-36 object-cover hover:scale-105 transition-transform" />
              {img.caption && <p className="p-1.5 text-[10px] text-slate-600 truncate">{img.caption}</p>}
            </div>
          ))}
        </div>
      )
    }

    case "button": {
      const btnStyle = data.style === "gold"
        ? "bg-amber-400 text-slate-950 hover:bg-amber-300 font-black"
        : data.style === "outline"
          ? "border-2 border-emerald-700 text-emerald-700 hover:bg-emerald-50 font-bold"
          : "bg-emerald-700 text-white hover:bg-emerald-800 font-bold"
      return (
        <div className={`mt-4 flex justify-${data.align === "center" ? "center" : "start"}`}>
          <a
            href={data.url || "#"}
            target={data.target || "_self"}
            rel={data.target === "_blank" ? "noopener noreferrer" : undefined}
            className={`px-5 py-2.5 rounded-xl text-sm shadow transition-all inline-flex items-center gap-2 ${btnStyle}`}
          >
            {title || data.label || "Click here"}
          </a>
        </div>
      )
    }

    case "table": {
      const columns = Array.isArray(data.columns) ? data.columns : []
      const rows = Array.isArray(data.rows) ? data.rows : []
      if (!columns.length && !rows.length) return null
      return (
        <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200">
          <table className="w-full text-xs text-left">
            {columns.length > 0 && (
              <thead className="bg-slate-100 text-slate-900 font-bold uppercase tracking-wider">
                <tr>
                  {columns.map((col, i) => (
                    <th key={i} className="p-3 border-b border-slate-200">{col}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-slate-100 bg-white">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-50">
                  {(Array.isArray(row) ? row : [row]).map((cell, cIdx) => (
                    <td key={cIdx} className="p-3 font-medium text-slate-700">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }

    case "video": {
      const url = data.url || ""
      if (!url) return null
      const src = embedUrl(url)
      return (
        <div className="mt-4 overflow-hidden rounded-2xl bg-black shadow-lg">
          {src.includes("youtube") || src.includes("vimeo") ? (
            <iframe
              title={title || "Video"}
              src={src}
              className="w-full aspect-video border-0"
              allow="accelerometer; autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <video src={url} controls className="w-full aspect-video" />
          )}
          {title && <p className="p-2 text-xs text-slate-300 bg-slate-900">{title}</p>}
        </div>
      )
    }

    case "map": {
      const lat = data.latitude || 28.2096
      const lng = data.longitude || 83.9856
      return (
        <div className="mt-4 p-4 rounded-2xl bg-slate-900 text-white space-y-2 border border-slate-800">
          <h4 className="font-bold text-sm text-amber-300">📍 {title || data.title || "Map Location"}</h4>
          <p className="text-xs text-slate-300">Coordinates: {lat}, {lng} (Zoom: {data.zoom || 12})</p>
          {data.description && <p className="text-xs text-slate-400">{data.description}</p>}
        </div>
      )
    }

    case "statistics": {
      const items = Array.isArray(data.items) ? data.items : []
      return (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
          {items.map((stat, i) => (
            <div key={i} className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-center space-y-1">
              <span className="text-2xl font-black text-emerald-700 block">{stat.number}</span>
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider block">{stat.label}</span>
            </div>
          ))}
        </div>
      )
    }

    case "alert": {
      const variant = data.variant || "info"
      const colors = {
        info: "bg-sky-50 text-sky-950 border-sky-300",
        warning: "bg-amber-50 text-amber-950 border-amber-300",
        danger: "bg-rose-50 text-rose-950 border-rose-300",
        success: "bg-emerald-50 text-emerald-950 border-emerald-300",
      }[variant] || "bg-sky-50 text-sky-950 border-sky-300"
      return (
        <div className={`p-4 rounded-2xl border ${colors} mt-4 space-y-1`}>
          <h4 className="font-extrabold text-sm uppercase tracking-wide">{title || data.title || variant}</h4>
          <p className="text-xs leading-relaxed">{data.body || data.text}</p>
        </div>
      )
    }

    case "quote":
      return (
        <blockquote className="mt-4 p-4 rounded-2xl bg-emerald-50/60 border-l-4 border-emerald-600 text-slate-800 italic space-y-1">
          <p className="text-sm font-medium">"{data.quote || title}"</p>
          {data.author && <cite className="text-xs font-bold not-italic text-emerald-900 block">— {data.author}</cite>}
        </blockquote>
      )

    case "list": {
      const items = Array.isArray(data.items) ? data.items : []
      const Tag = data.ordered ? "ol" : "ul"
      return (
        <Tag className={`mt-3 space-y-1 text-sm text-slate-700 ${data.ordered ? "list-decimal pl-5" : "list-disc pl-5"}`}>
          {items.map((it, i) => (
            <li key={i}>{typeof it === "string" ? it : it.text}</li>
          ))}
        </Tag>
      )
    }

    case "divider":
      return <hr className="my-6 border-slate-200" />

    case "html":
      return (
        <div
          className="mt-3 prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: data.html || data.text || "" }}
        />
      )

    default:
      return null
  }
}

export default function CMSBlock({ section }) {
  const [sent, setSent] = useState("")
  if (!section) return null
  const type = section.section_type || "text"
  const config = section.config || {}
  const media = config.media_url || section.image_url
  const fields = Array.isArray(config.fields) ? config.fields.filter((field) => FIELD_TYPES.has(field.field_type || "text")) : []
  const blocks = Array.isArray(section.blocks) ? section.blocks : []

  const bgStyleKey = config.background_style || config.bg_style || (section.layout_variant === "hero" ? "hero-dark" : "clean-white")
  const bgClass = BG_STYLES[bgStyleKey] || BG_STYLES["clean-white"]
  const padClass = PADDING_STYLES[config.padding_style] || (section.layout_variant === "hero" ? PADDING_STYLES.spacious : PADDING_STYLES.medium)

  const layout = section.layout_variant === "split"
    ? `grid gap-6 md:grid-cols-2 rounded-3xl border ${bgClass} ${padClass}`
    : `rounded-3xl border ${bgClass} ${padClass}`

  return (
    <article className={`${layout} ${effectClass(config.effect)}`}>
      {section.title && <h2 className="text-2xl font-black tracking-tight">{section.title}</h2>}
      {section.subtitle && <p className="mt-1 text-sm opacity-80">{section.subtitle}</p>}

      {/* RENDER CHILD CONTENT BLOCKS IF PRESENT */}
      {blocks.length > 0 ? (
        <div className="space-y-3 mt-3">
          {blocks.map((block) => (
            <ContentBlockItem key={block.id || block.position} block={block} />
          ))}
        </div>
      ) : (
        <>
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
        </>
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
