// Default titles/descriptions for routes that have no CMS page record (the
// CMS "pages" entries, editable in the admin, take precedence). Descriptions
// state what the page actually does; no rankings, superlatives or claims.
export const BRAND = "Nepal Yatra"

export const DEFAULT_DESCRIPTION =
  "Plan travel in Nepal: search destinations, compare places, build an itinerary, and check official entry rules, fees and emergency contacts."

export const ROUTE_SEO = {
  "/": { title: "Nepal Yatra: plan travel across Nepal", description: DEFAULT_DESCRIPTION, full: true },
  "/search": { title: "Search", description: "Search Nepal destinations, districts, hotels, services and travel rules in one place." },
  "/discover": { title: "Find places by activity and season", description: "Filter Nepal destinations by activity, effort, altitude, season, official fees, accessibility notes and distance from where you start." },
  "/districts": { title: "All districts of Nepal by province", description: "Explore Nepal districts by province with recorded tourism coverage." },
  "/decide": { title: "Help me decide", description: "Compare two to four Nepal destinations for your month: season fit, distance, altitude, official fees, nearest hospital and hotels, with sources." },
  "/before-you-travel": { title: "Before you travel: visas, permits and fees", description: "Nepal visa, TIMS, restricted-area permit, national park and heritage fees, altitude safety and insurance notes, transcribed from official sources." },
  "/distances": { title: "Distances and directions", description: "Road and straight-line distances between places in Nepal, labelled by how each distance was measured." },
  "/knowledge-base": { title: "Help and how-to", description: "How to search, plan an itinerary, request bookings and submit places on Nepal Yatra." },
  "/privacy-policy": { title: "Privacy Policy", description: "What personal information Nepal Yatra stores, why, which outside services receive it, how long it is kept and how to delete it." },
  "/privacy": { title: "Privacy Policy", description: "What personal information Nepal Yatra stores, why, which outside services receive it, how long it is kept and how to delete it." },
  "/terms-of-service": { title: "Terms of Service", description: "The terms for using Nepal Yatra: accounts, booking requests, submitted content, third-party services and limits of the information provided." },
  "/terms": { title: "Terms of Service", description: "The terms for using Nepal Yatra: accounts, booking requests, submitted content, third-party services and limits of the information provided." },
  "/cookie-policy": { title: "Cookie Policy", description: "The cookies and browser storage Nepal Yatra uses, what each one is for, and how to clear them." },
  "/data-deletion": { title: "Delete your account and data", description: "How to delete your Nepal Yatra account, what is removed, and what is kept for legal or safety reasons." },
  "/unsubscribe": { title: "Unsubscribe from travel notes", description: "Stop receiving Nepal Yatra travel-note emails." },
  "/plans/shared/:token": { title: "Shared trip plan", description: "A read-only trip plan shared by its owner.", noindex: true },
}

export const formatTitle = (title) => {
  const t = String(title || "").trim()
  if (!t || t === BRAND) return ROUTE_SEO["/"].title
  return t.includes(BRAND) ? t : `${t} | ${BRAND}`
}
