/**
 * Offline route packs (Phase 6): calculated routes cached in localStorage
 * so turn-by-turn navigation stays usable without connectivity. Everything
 * here is a best-effort, corruption-safe snapshot of what the API returned
 * — a pack is always labelled with when it was calculated, never presented
 * as a live route. Map tiles are not cached (not bundleable honestly).
 */
const KEY = "nepal_nav_offline_packs_v1"
const MAX_PACKS = 5

export const loadPacks = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) || "[]")
    if (!Array.isArray(parsed)) return []
    return parsed.filter((pack) => pack && Array.isArray(pack.route) && pack.route.length > 1)
  } catch {
    return [] // corrupted or blocked storage — degrade to "no packs"
  }
}

export const persistPacks = (packs) => {
  try {
    localStorage.setItem(KEY, JSON.stringify(packs))
  } catch {
    /* storage full or blocked — offline packs are best-effort */
  }
}

// Newest first, same-destination packs replaced, capped at MAX_PACKS.
export const addPack = (packs, pack) => {
  const sameDestination = String(pack?.destination_name || "").trim().toLowerCase()
  const filtered = packs.filter(
    (existing) => String(existing?.destination_name || "").trim().toLowerCase() !== sameDestination
  )
  return [pack, ...filtered].slice(0, MAX_PACKS)
}

export const removePack = (packs, id) => packs.filter((pack) => pack?.id !== id)

export const findPackForDestination = (packs, name) => {
  const target = String(name || "").trim().toLowerCase()
  if (!target) return null
  return packs.find((pack) => String(pack?.destination_name || "").trim().toLowerCase() === target) || null
}
