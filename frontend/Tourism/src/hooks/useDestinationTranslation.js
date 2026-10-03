import { useState, useEffect, useCallback } from "react"
import destinationApi from "../api/destinationApi"
import { useTranslation } from "./useTranslation"

/**
 * Hook to fetch and manage translated content for a destination.
 * Returns translated fields when available, falls back to original.
 */
export function useDestinationTranslation(slug, enabled = true) {
  const { lang } = useTranslation()
  const [translated, setTranslated] = useState(null)
  const [error, setError] = useState(null)

  const fetchTranslation = useCallback(async () => {
    if (!enabled || !slug) return
    try {
      const response = await destinationApi.translate(slug, { language_code: lang })
      setTranslated(response.data)
      setError(null)
    } catch (err) {
      setError(err)
      setTranslated(null)
    } finally {
    }
  }, [slug, lang, enabled])

  useEffect(() => {
    if (enabled && slug) {
      fetchTranslation()
    }
  }, [fetchTranslation, slug, lang, enabled])

  const refresh = useCallback(() => {
    fetchTranslation()
  }, [fetchTranslation])

  const loading = Boolean(enabled && slug && !translated && !error)

  return { translated, loading, error, refresh }
}

export default useDestinationTranslation