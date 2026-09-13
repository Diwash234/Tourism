import { useEffect, useRef, useState } from "react"

/**
 * Continuous GPS tracking for live navigation (master spec Phase 2).
 *
 * watchPosition-based: only runs while `active` is true, always cleans up
 * the watch on deactivate/unmount. `locating` is derived (active with no
 * fix or error yet) so the effect body performs no synchronous state
 * writes — React Compiler-safe.
 */
const useLivePosition = (active) => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)
  const [code, setCode] = useState(null)
  const [fixSeen, setFixSeen] = useState(false)
  const watchRef = useRef(null)

  useEffect(() => {
    if (!active) {
      if (watchRef.current !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchRef.current)
        watchRef.current = null
      }
      return undefined
    }
    if (!navigator.geolocation) {
      // Deferred: effects must not write state synchronously (lint rule).
      const id = window.setTimeout(() => setError("Geolocation is not supported by this browser."), 0)
      return () => window.clearTimeout(id)
    }
    // Reset per-session flags asynchronously for the same reason.
    const resetId = window.setTimeout(() => { setFixSeen(false); setError(null); setCode(null) }, 0)
    watchRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setPosition({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy ?? null,
          altitude: pos.coords.altitude ?? null,
          speed: pos.coords.speed ?? null,
          heading: pos.coords.heading ?? null,
        })
        setError(null)
        setCode(null)
        setFixSeen(true)
      },
      (err) => {
        setError(err.message || "Location unavailable.")
        setCode(err.code)
      },
      { enableHighAccuracy: true, maximumAge: 2000, timeout: 15000 }
    )
    return () => {
      window.clearTimeout(resetId)
      if (watchRef.current !== null) {
        navigator.geolocation.clearWatch(watchRef.current)
        watchRef.current = null
      }
    }
  }, [active])

  // Honest "in flight" state without synchronous effect writes: true from
  // activation until the first fix or error of this session arrives.
  const locating = Boolean(active) && !fixSeen && !error

  return { position, error, code, locating }
}

export default useLivePosition
