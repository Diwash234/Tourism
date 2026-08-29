/** Relative in-app path only. Blocks open redirects. */
export default function safeNextPath(value) {
  if (!value || typeof value !== "string") return null
  const next = value.trim()
  if (!next.startsWith("/") || next.startsWith("//") || next.includes("://")) return null
  return next
}
