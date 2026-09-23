/**
 * Pure helpers for the Content Translations panel.
 *
 * The backend (CMSContentTranslation) accepts only these fields per target
 * and stores them as a JSON dict; the public config applies them when the
 * visitor's language matches. These helpers keep the panel honest:
 *  - only whitelisted fields are ever sent,
 *  - empty values are stripped (an empty string in `content` would override
 *    the source text with nothing on the public site),
 *  - coverage counts only rows that actually carry text.
 */

export const TRANSLATION_FIELDS = {
  pages: [
    { name: "title", label: "Title" },
    { name: "meta_description", label: "Search description", multiline: true },
  ],
  sections: [
    { name: "title", label: "Title" },
    { name: "subtitle", label: "Subtitle" },
    { name: "body", label: "Body", multiline: true },
    { name: "cta_text", label: "Button text" },
  ],
  navigation: [{ name: "label", label: "Menu label" }],
}

export const TYPE_LABELS = { pages: "Page", sections: "Section", navigation: "Menu item" }

export const buildTranslationKey = (type, id, lang) => `${type}:${id}:${lang}`

/** Keep only whitelisted fields with real text; everything else is dropped. */
export const cleanTranslationContent = (content, type) => {
  const allowed = (TRANSLATION_FIELDS[type] || []).map((f) => f.name)
  const cleaned = {}
  Object.entries(content || {}).forEach(([field, value]) => {
    if (allowed.includes(field) && typeof value === "string" && value.trim()) cleaned[field] = value
  })
  return cleaned
}

/** Keys of translation rows that carry at least one non-empty field. */
export const translatedKeySet = (translations, lang) => {
  const set = new Set()
  ;(translations || []).forEach((row) => {
    if (row.language_code !== lang) return
    if (Object.keys(cleanTranslationContent(row.content, row.target_resource)).length) {
      set.add(buildTranslationKey(row.target_resource, row.object_id, lang))
    }
  })
  return set
}

export const translationCoverage = (records, translatedKeys) => {
  const total = records.length
  const done = records.filter((r) => translatedKeys.has(buildTranslationKey(r.type, r.id, r.lang))).length
  return { done, total }
}
