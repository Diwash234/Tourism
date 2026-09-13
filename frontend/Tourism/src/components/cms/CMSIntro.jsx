import SafeHtml from "./SafeHtml"
// Shared CMS intro block — renders the `intro` section (tolerantly matched to
// `page-intro` by usePublicConfig) for pages that previously had no CMS
// consumption at all. Renders NOTHING when the section is empty, so pages keep
// their exact current look until an admin actually writes content.
//
// Honors the same structured style controls as CMSBlock (spec §47): text
// scale, alignment, background image/theme colors, font family, heading
// level/size and title color — all enum/hex allow-lists, never raw CSS.
const TEXT_SCALES = { sm: "text-sm", base: "text-base", lg: "text-lg", xl: "text-xl" }
const INTRO_HEADING_SIZES = {
  sm: "text-xl md:text-2xl",
  base: "text-2xl md:text-3xl",
  lg: "text-3xl md:text-4xl",
  xl: "text-4xl md:text-5xl",
}
const FONT_STACKS = {
  serif: "Georgia, 'Times New Roman', serif",
  mono: "ui-monospace, SFMono-Regular, Menlo, monospace",
  display: "'Trebuchet MS', 'Segoe UI', system-ui, sans-serif",
}
const hexOk = (v) => typeof v === "string" && /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)

export default function CMSIntro({ section: s }) {
  if (!s || (!s.title && !s.body && !s.image_url)) return null
  const config = s.config || {}
  const style = {}
  if (hexOk(config.custom_color)) style.color = config.custom_color
  if (hexOk(config.custom_bg)) style.background = config.custom_bg
  if (FONT_STACKS[config.font_family]) style.fontFamily = FONT_STACKS[config.font_family]
  const bgImage = typeof config.bg_image === "string" && /^https:\/\//.test(config.bg_image) ? config.bg_image : ""
  if (bgImage) {
    style.backgroundImage = `url(${bgImage})`
    style.backgroundSize = "cover"
    style.backgroundPosition = "center"
  }
  const scaleClass = TEXT_SCALES[config.text_scale] || ""
  const alignClass = config.align === "center" ? "text-center" : config.align === "right" ? "text-right" : ""
  const headingClass = INTRO_HEADING_SIZES[config.heading_size] || INTRO_HEADING_SIZES.base
  const HeadingTag = ["h1", "h3", "h4"].includes(config.heading_level) ? config.heading_level : "h2"
  return (
    <section
      className={`container-app pt-8 md:pt-10 ${scaleClass} ${alignClass}`}
      style={Object.keys(style).length ? style : undefined}
      aria-label="Page introduction"
    >
      <div className={config.align === "center" ? "mx-auto max-w-3xl" : config.align === "right" ? "ml-auto max-w-3xl" : "max-w-3xl"}>
        {s.title && (
          <HeadingTag
            className={`${headingClass} font-black tracking-tight text-gray-900`}
            style={hexOk(config.title_color) ? { color: config.title_color } : undefined}
          >
            {s.title}
          </HeadingTag>
        )}
        {s.body && (
          <SafeHtml className="prose prose-sm md:prose-base mt-3 max-w-none text-gray-600" html={s.body} />
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
