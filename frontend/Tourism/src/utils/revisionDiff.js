/**
 * Pure helpers for the CMS revision-history diff view.
 *
 * Backend revision snapshots (CMSRevision.snapshot) are flat field dicts of
 * the saved record. These helpers turn two consecutive snapshots into a
 * human-readable list of what changed — no JSON jargon, code-free labels
 * (brief: admin UI must never expose implementation details).
 */

// Bookkeeping fields that move on every save and say nothing about content.
const NOISE_KEYS = new Set(["id", "created_at", "updated_at", "published_at"])

const LABELS = {
  title: "Title",
  subtitle: "Subtitle",
  body: "Body",
  key: "Key",
  route: "Route",
  cta_text: "Button text",
  cta_url: "Button link",
  image_url: "Image",
  icon: "Icon",
  section_type: "Section type",
  layout_variant: "Layout",
  display_order: "Display order",
  is_visible: "Visible",
  status: "Status",
  seo_title: "Search title",
  meta_description: "Search description",
  og_image_url: "Share image",
  search_visible: "Show in search",
  config: "Settings",
  blocks: "Blocks",
  location: "Menu location",
  label: "Label",
  parent_id: "Parent item",
  allowed_roles: "Allowed roles",
  value: "Value",
  is_public: "Public",
  sections: "Sections",
  scheduled_publish_at: "Scheduled for",
}

export const revisionFieldLabel = (key) =>
  LABELS[key] || String(key).replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase())

export const formatSnapshotValue = (value) => {
  if (value === null || value === undefined || value === "") return "empty"
  if (typeof value === "boolean") return value ? "On" : "Off"
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? "" : "s"}`
  if (typeof value === "object") return "Updated"
  const text = String(value)
  return text.length > 60 ? `${text.slice(0, 60)}…` : text
}

/**
 * Compare two consecutive revision snapshots (newest first ordering).
 * Returns [{ field, label, from, to }] for every content field that differs;
 * bookkeeping keys are ignored.
 */
export const diffSnapshots = (current, previous) => {
  const from = previous || {}
  const to = current || {}
  const keys = new Set([...Object.keys(from), ...Object.keys(to)])
  const changes = []
  keys.forEach((key) => {
    if (NOISE_KEYS.has(key)) return
    const a = JSON.stringify(from[key] ?? null)
    const b = JSON.stringify(to[key] ?? null)
    if (a !== b) changes.push({ field: key, label: revisionFieldLabel(key), from: from[key], to: to[key] })
  })
  return changes
}
