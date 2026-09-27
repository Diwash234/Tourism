import { useCallback, useEffect, useState } from "react"
import { validateGpsPosition } from "../utils/placeUtils"

/**
 * Browser geolocation with honest state separation.
 *
 * Options:
 *  - auto (default true): request a one-shot fix on mount.
 *    Public pages where location is OPTIONAL (e.g. /travel) should pass
 *    { auto: false } and let the user opt in via the "Use my location"
 *    button (calls `retry`) — no permission prompt before consent.
 *
 * Returns the original { position, error } contract plus additive fields:
 *  - code:     GeolocationPositionError code (1 = permission denied) so UIs
 *              can tell "blocked" apart from "unavailable/timeout"
 *  - locating: true while a fix is in flight — callers must not render
 *              "nothing nearby" while this is true
 *  - retry:    re-request on demand (e.g. a "Use My Location" button)
 */
const useGeolocation = ({ auto = true } = {}) => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)
  const [code, setCode] = useState(null)
  // A fix is requested on mount (unless opt-in mode), so the honest initial
  // state is "in flight" only when a request is actually pending.
  const [locating, setLocating] = useState(auto)

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by this browser.")
      setLocating(false)
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const candidate = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy ?? null,
          altitude: pos.coords.altitude ?? null,
          speed: pos.coords.speed ?? null,
          heading: pos.coords.heading ?? null,
        }
        const validation = validateGpsPosition(candidate)
        if (!validation.valid) {
          setPosition(null)
          setError(validation.reason)
          setCode(3)
          setLocating(false)
          return
        }
        setPosition({
          ...candidate,
        })
        setError(null)
        setCode(null)
        setLocating(false)
      },
      (err) => {
        setError(err.message)
        setCode(err.code)
        setLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    )
  }, [])

  const clear = useCallback(() => {
    setPosition(null)
    setError(null)
    setCode(null)
    setLocating(false)
  }, [])

  useEffect(() => {
    if (!auto) return undefined
    // Deferred one tick: keeps synchronous setState out of the effect flush
    // (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(request, 0)
    return () => clearTimeout(t)
  }, [auto, request])

  return { position, error, code, locating, retry: request, clear }
}

export default useGeolocation
