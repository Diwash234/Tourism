/**
 * resolveSmartSearch
 * The header search box sends every query to the universal search page,
 * which is backed by /api/v1/search/ (destinations, districts, hotels,
 * restaurants, banks/ATMs, permit rules and app tools, with did-you-mean).
 */
export function resolveSmartSearch(rawQuery) {
  const query = (rawQuery || "").trim()
  if (!query) return null
  return `/search?q=${encodeURIComponent(query)}`
}
