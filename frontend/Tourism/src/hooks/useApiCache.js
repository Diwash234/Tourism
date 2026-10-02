import { useCallback, useEffect, useRef, useState } from "react"
import axiosClient from "../api/axiosClient"

const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes
const CACHE_PREFIX = "ny_api_cache_"

/**
 * API response caching hook with TTL, request deduplication, and cache invalidation.
 *
 * @param {string} endpoint - API endpoint path (e.g. "/destinations/")
 * @param {object} options
 * @param {number} options.ttl - Time-to-live in milliseconds (default: 5 min)
 * @param {boolean} options.enabled - Whether caching is enabled (default: true)
 * @param {object} options.params - Query params to include in cache key
 *
 * @returns {object} { data, loading, error, invalidate, refetch, fromCache }
 */
const useApiCache = (endpoint, { ttl = DEFAULT_TTL, enabled = true, params = {} } = {}) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fromCache, setFromCache] = useState(false)
  const inflightRef = useRef(null)

  const cacheKey = `${CACHE_PREFIX}${endpoint}?${new URLSearchParams(params).toString()}`

  const readCache = useCallback(() => {
    if (!enabled) return null
    try {
      const raw = localStorage.getItem(cacheKey)
      if (!raw) return null
      const cached = JSON.parse(raw)
      if (!cached || !cached.data) return null
      if (Date.now() - cached.timestamp > ttl) {
        localStorage.removeItem(cacheKey)
        return null
      }
      return cached.data
    } catch {
      return null
    }
  }, [cacheKey, ttl, enabled])

  const writeCache = useCallback(
    (responseData) => {
      if (!enabled) return
      try {
        localStorage.setItem(
          cacheKey,
          JSON.stringify({ data: responseData, timestamp: Date.now() })
        )
      } catch {
        /* storage full or unavailable */
      }
    },
    [cacheKey, enabled]
  )

  const invalidate = useCallback(() => {
    try {
      // Clear all cache entries matching this endpoint prefix
      const prefix = `${CACHE_PREFIX}${endpoint}`
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith(prefix)) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach((key) => localStorage.removeItem(key))
    } catch {
      /* ignore */
    }
    setData(null)
    setFromCache(false)
  }, [endpoint])

  const refetch = useCallback(async () => {
    // Deduplicate concurrent requests
    if (inflightRef.current) {
      return inflightRef.current
    }

    const promise = (async () => {
      setLoading(true)
      setError(null)

      // Try cache first
      const cached = readCache()
      if (cached) {
        setData(cached)
        setFromCache(true)
        setLoading(false)
        return { data: cached, fromCache: true }
      }

      setFromCache(false)
      try {
        const response = await axiosClient.get(endpoint, { params })
        const responseData = response.data
        writeCache(responseData)
        setData(responseData)
        setError(null)
        return { data: responseData, fromCache: false }
      } catch (err) {
        const message =
          err?.response?.data?.message || err?.message || "Failed to fetch data"
        setError(message)
        return { data: null, error: message }
      } finally {
        setLoading(false)
        inflightRef.current = null
      }
    })()

    inflightRef.current = promise
    return promise
  }, [endpoint, params, readCache, writeCache])

  // Auto-fetch on mount and when endpoint/params change
  useEffect(() => {
    const t = setTimeout(refetch, 0)
    return () => clearTimeout(t)
  }, [refetch])

  return { data, loading, error, invalidate, refetch, fromCache }
}

export default useApiCache
