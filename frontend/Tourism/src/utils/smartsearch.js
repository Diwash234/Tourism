/**
 * resolveSmartSearch
 * There's no backend "universal search" endpoint (checked — nothing in
 * tourist/urls.py combines destinations+hotels+districts+festivals+
 * emergency into one search). This is an honest client-side keyword
 * router instead: match against known intents that have REAL, working
 * destinations in this app, and fall back to the actual destination
 * search (?q=) for everything else — never a dead link.
 */
const INTENTS = [
  { keywords: ["hotel", "stay", "room", "lodge", "resort"], path: (q) => `/hotels/search?q=${encodeURIComponent(q)}` },
  { keywords: ["emergency", "police", "hospital", "ambulance", "sos", "rescue", "fire"], path: () => "/emergency" },
  { keywords: ["budget", "cost", "price", "estimate", "expense"], path: () => "/budget-estimator" },
  { keywords: ["risk", "safety", "alert", "danger", "warning"], path: () => "/risk-alerts" },
  { keywords: ["navigate", "navigation", "route", "direction", "map"], path: () => "/navigation" },
  { keywords: ["weather", "temperature", "forecast", "rain", "climate"], path: () => "/navigation" },
  { keywords: ["district", "province", "region"], path: () => "/language" },
  { keywords: ["booking", "reservation", "my trip", "my booking"], path: () => "/my-bookings" },
  { keywords: ["translate", "translation", "language", "phrase"], path: (q) => `/translation?place=${encodeURIComponent(q)}` },
  { keywords: ["festival", "dashain", "tihar", "holi", "jatra", "losar", "teej", "culture", "history", "unesco", "wildlife"], path: () => "/discover-nepal" },
  { keywords: ["chat", "himal ai", "assistant", "help"], path: () => "/chatbot" },
  { keywords: ["favorite", "favourite", "saved", "wishlist"], path: () => "/favorites" },
]

export function resolveSmartSearch(rawQuery) {
  const query = rawQuery.trim()
  if (!query) return null

  const lower = query.toLowerCase()
  const matched = INTENTS.find((intent) => intent.keywords.some((kw) => lower.includes(kw)))

  if (matched) return matched.path(query)

  // Default: treat it as a destination/place name search — this always
  // works since /destinations already reads ?q= (see DestinationList.jsx).
  return `/destinations?q=${encodeURIComponent(query)}`
}