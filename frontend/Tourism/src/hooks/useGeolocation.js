import { useCallback, useEffect, useRef, useState } from "react"
import { validateGpsPosition } from "../utils/placeUtils"

const CACHE_KEY = "ny_cached_position"
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

/**
 * Browser geolocation with caching, IP fallback, and honest state separation.
 *
 * Returns both new and legacy fields for backward compatibility:
 *  - latitude / longitude: coordinates (null when unavailable)
 *  - accuracy: GPS accuracy in meters (null when unavailable)
 *  - loading: true while a fix is in flight
 *  - error: human-readable error message (null when no error)
 *  - refresh: re-request location on demand
 *  - clear: clear cached position and reset state
 *  - source: "gps" | "cache" | "ip" | null
 *  - position: legacy object { lat, lng, accuracy, ... } (null when unavailable)
 *  - locating: legacy alias for loading
 *  - retry: legacy alias for refresh
 *  - code: legacy GeolocationPositionError code (null when no error)
 *
 * The last known position is cached in localStorage for 5 minutes.
 * If GPS fails, falls back to IP-based geolocation via the backend.
 */
const useGeolocation = ({ auto = true, enableIpFallback = true } = {}) => {
  const [coords, setCoords] = useState(null)
  const [accuracy, setAccuracy] = useState(null)
  const [error, setError] = useState(null)
  const [code, setCode] = useState(null)
  const [loading, setLoading] = useState(auto)
  const [source, setSource] = useState(null)
  const ipFallbackAttempted = useRef(false)

  // Read cached position from localStorage
  const readCache = useCallback(() => {
    try {
      const raw = localStorage.getItem(CACHE_KEY)
      if (!raw) return null
      const cached = JSON.parse(raw)
      if (!cached || cached.latitude == null || cached.longitude == null) return null
      if (Date.now() - cached.timestamp > CACHE_TTL) {
        localStorage.removeItem(CACHE_KEY)
        return null
      }
      return cached
    } catch {
      return null
    }
  }, [])

  // Write position to localStorage cache
  const writeCache = useCallback((latitude, longitude, acc) => {
    try {
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({ latitude, longitude, accuracy: acc, timestamp: Date.now() })
      )
    } catch {
      /* storage full or unavailable */
    }
  }, [])

  // IP-based geolocation fallback via backend
  const fetchIpLocation = useCallback(async () => {
    if (ipFallbackAttempted.current) return false
    ipFallbackAttempted.current = true
    try {
      const resp = await fetch("/api/v1/auth/update-location/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      const data = await resp.json()
      if (data?.latitude && data?.longitude) {
        setCoords({ latitude: data.latitude, longitude: data.longitude })
        setAccuracy(data.accuracy || null)
        setSource("ip")
        setError(null)
        setCode(null)
        setLoading(false)
        return true
      }
    } catch {
      /* IP fallback failed */
    }
    return false
  }, [])

  const request = useCallback(async (forceFresh = false) => {
    // Automatic location can use a short cache, but an explicit refresh/
    // "Use My Location" action must request a fresh browser GPS fix.
    const cached = forceFresh ? null : readCache()
    if (cached) {
      setCoords({ latitude: cached.latitude, longitude: cached.longitude })
      setAccuracy(cached.accuracy)
      setSource("cache")
      setLoading(false)
      return
    }

    if (!navigator.geolocation) {
      setError("Geolocation is not supported by this browser.")
      setCode(3)
      setLoading(false)
      if (enableIpFallback) {
        const ok = await fetchIpLocation()
        if (!ok) setError("Location is unavailable. Please enable location services.")
      }
      return
    }

    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const candidate = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy ?? null,
        }
        const validation = validateGpsPosition(candidate)
        // A coarse GPS fix is still useful for nearby search. Keep it as a
        // usable source instead of treating accuracy as a hard failure; the
        // UI can show the accuracy and the user can refine it when needed.
        if (!validation.valid && validation.reason?.toLowerCase().includes("accuracy")) {
          setCoords({ latitude: pos.coords.latitude, longitude: pos.coords.longitude })
          setAccuracy(pos.coords.accuracy ?? null)
          setSource("gps")
          setError(null)
          setCode(null)
          setLoading(false)
          writeCache(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy ?? null)
          return
        }
        if (!validation.valid) {
          setCoords(null)
          setAccuracy(null)
          setError(validation.reason)
          setCode(3)
          setLoading(false)
          return
        }
        const latitude = pos.coords.latitude
        const longitude = pos.coords.longitude
        const acc = pos.coords.accuracy ?? null
        setCoords({ latitude, longitude })
        setAccuracy(acc)
        setSource("gps")
        setError(null)
        setCode(null)
        setLoading(false)
        writeCache(latitude, longitude, acc)
      },
      async (err) => {
        const codeMap = {
          1: "Location permission denied. Please enable location access.",
          2: "Location unavailable. Please try again.",
          3: "Location request timed out. Please try again.",
        }
        const message = codeMap[err.code] || err.message || "Unable to retrieve your location."
        setError(message)
        setCode(err.code)
        setLoading(false)
        // Try IP fallback on GPS failure
        if (enableIpFallback) {
          const ok = await fetchIpLocation()
          if (!ok) setError(message)
        }
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: forceFresh ? 0 : 300000 }
    )
  }, [readCache, writeCache, enableIpFallback, fetchIpLocation])

  const refresh = useCallback(() => {
    ipFallbackAttempted.current = false
    request(true)
  }, [request])

  const clear = useCallback(() => {
    setCoords(null)
    setAccuracy(null)
    setError(null)
    setCode(null)
    setSource(null)
    setLoading(false)
    try {
      localStorage.removeItem(CACHE_KEY)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    if (!auto) return undefined
    const t = setTimeout(request, 0)
    return () => clearTimeout(t)
  }, [auto, request])

  // Build legacy position object for backward compatibility
  const position = coords
    ? {
        lat: coords.latitude,
        lng: coords.longitude,
        accuracy,
        altitude: null,
        speed: null,
        heading: null,
      }
    : null

  return {
    // New API
    latitude: coords?.latitude ?? null,
    longitude: coords?.longitude ?? null,
    accuracy,
    loading,
    error,
    refresh,
    clear,
    source,
    // Legacy API (backward compatible)
    position,
    locating: loading,
    retry: refresh,
    code,
  }
}

export default useGeolocation
