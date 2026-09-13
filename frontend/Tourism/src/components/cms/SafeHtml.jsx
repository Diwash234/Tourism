import DOMPurify from "dompurify"

/**
 * Renders admin-authored rich text safely. Content passes DOMPurify with a
 * conservative allow-list; anything else (scripts, event handlers, javascript:
 * URLs) is stripped before it reaches the DOM. Plain-text values render as-is.
 */
export default function SafeHtml({ html = "", className = "" }) {
  const clean = DOMPurify.sanitize(String(html || ""), {
    ALLOWED_TAGS: ["p", "br", "b", "strong", "i", "em", "u", "ul", "ol", "li", "a", "h2", "h3", "h4", "blockquote", "span"],
    ALLOWED_ATTR: ["href", "title", "target", "rel"],
  })
  return <div className={className} dangerouslySetInnerHTML={{ __html: clean }} />
}
