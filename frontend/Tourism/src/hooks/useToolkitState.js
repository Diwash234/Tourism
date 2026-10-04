import { useCallback, useMemo } from "react"
import useLocalStorage from "./useLocalStorage"
import { TOOLKIT_TOOLS, TOOL_BY_ID } from "../data/travelToolkit"

/**
 * useToolkitState — the automation layer behind the Travel Toolkit hub.
 *
 * Persists two things locally (never on the server: a traveller's browsing
 * habits are theirs) and derives everything else:
 *
 *   favourites  explicit stars, kept until the traveller removes them
 *   recents     tools opened, most-recent-first, capped and de-duplicated
 *
 * From those it computes a recommendation ranking that combines favourite
 * status, recency with a 3-day half-life, repeat usage, category affinity and
 * the curated `popular` flag — so the hub reorders itself to what this
 * traveller actually does instead of showing a static list.
 *
 * Everything degrades to "no personalisation" when storage is unavailable
 * (private mode, disabled cookies): the hook never throws and never blocks.
 */

const MAX_RECENTS = 12
const MAX_HITS = 9
const NO_FAVOURITES = []
const NO_RECENTS = []

/** Recommend the same thing you just opened? Only after a cooling-off period. */
const COOL_OFF_MS = 15 * 60 * 1000
const HALF_LIFE_MS = 72 * 60 * 60 * 1000 // 3 days

export default function useToolkitState({ authenticated = false } = {}) {
  const [favourites, setFavourites] = useLocalStorage("ny.toolkit.favourites", NO_FAVOURITES)
  const [recents, setRecents] = useLocalStorage("ny.toolkit.recents", NO_RECENTS)

  // --- favourites -----------------------------------------------------------
  const isFavourite = useCallback(
    (id) => Array.isArray(favourites) && favourites.includes(id),
    [favourites]
  )

  const toggleFavourite = useCallback(
    (id) => {
      if (!TOOL_BY_ID[id]) return
      setFavourites((current) => {
        const list = Array.isArray(current) ? current : []
        return list.includes(id) ? list.filter((x) => x !== id) : [id, ...list]
      })
    },
    [setFavourites]
  )

  const removeFavourite = useCallback(
    (id) => setFavourites((current) => (Array.isArray(current) ? current.filter((x) => x !== id) : [])),
    [setFavourites]
  )

  // --- recents --------------------------------------------------------------
  /** Record that a tool was opened. Idempotent per tool, capped, newest first. */
  const trackVisit = useCallback(
    (id) => {
      if (!TOOL_BY_ID[id]) return
      setRecents((current) => {
        const list = Array.isArray(current) ? current : []
        const existing = list.find((row) => row && row.id === id)
        const entry = {
          id,
          at: Date.now(),
          hits: Math.min(((existing && existing.hits) || 0) + 1, MAX_HITS),
        }
        return [entry, ...list.filter((row) => row && row.id !== id)].slice(0, MAX_RECENTS)
      })
    },
    [setRecents]
  )

  const clearRecents = useCallback(() => setRecents(NO_RECENTS), [setRecents])

  // --- derived --------------------------------------------------------------
  const favouriteTools = useMemo(
    () => (Array.isArray(favourites) ? favourites.map((id) => TOOL_BY_ID[id]).filter(Boolean) : []),
    [favourites]
  )

  const recentTools = useMemo(() => {
    if (!Array.isArray(recents)) return []
    return recents.map((row) => ({ ...TOOL_BY_ID[row.id], hits: row.hits || 0, lastAt: row.at })).filter((t) => t.id)
  }, [recents])

  /** How many recent entries fell in each category — drives affinity. */
  const categoryAffinity = useMemo(() => {
    const counts = {}
    if (!Array.isArray(recents)) return counts
    recents.forEach((row) => {
      const tool = row && TOOL_BY_ID[row.id]
      if (!tool) return
      counts[tool.category] = (counts[tool.category] || 0) + 1
    })
    return counts
  }, [recents])

  const recommendations = useMemo(() => {
    const now = Date.now()
    const favSet = new Set(Array.isArray(favourites) ? favourites : [])
    const recentById = new Map()
    if (Array.isArray(recents)) recents.forEach((row) => row && recentById.set(row.id, row))

    const scored = TOOLKIT_TOOLS.map((tool) => {
      let score = 0
      if (tool.authOnly && !authenticated) return { tool, score: -1 }

      if (favSet.has(tool.id)) score += 60

      const row = recentById.get(tool.id)
      if (row) {
        const age = Math.max(0, now - (row.at || 0))
        score += 45 * Math.pow(0.5, age / HALF_LIFE_MS)
        score += Math.min(row.hits || 1, 5) * 3
        if (age < COOL_OFF_MS) score -= 35 // just used it — show something else
      }

      if (tool.popular) score += 12
      if (tool.live) score += 4
      score += (categoryAffinity[tool.category] || 0) * 5

      return { tool, score }
    })

    return scored
      .filter((row) => row.score > 0)
      .sort((a, b) => b.score - a.score || a.tool.label.localeCompare(b.tool.label))
      .map((row) => row.tool)
  }, [favourites, recents, categoryAffinity, authenticated])

  const stats = useMemo(
    () => ({
      tools: TOOLKIT_TOOLS.filter((t) => authenticated || !t.authOnly).length,
      favourites: Array.isArray(favourites) ? favourites.length : 0,
      recent: Array.isArray(recents) ? recents.length : 0,
      recommended: recommendations.length,
    }),
    [favourites, recents, recommendations, authenticated]
  )

  return {
    favourites,
    favouriteTools,
    isFavourite,
    toggleFavourite,
    removeFavourite,
    recents,
    recentTools,
    trackVisit,
    clearRecents,
    recommendations,
    stats,
  }
}
