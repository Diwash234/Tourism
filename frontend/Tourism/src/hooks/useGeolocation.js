import { useCallback, useEffect, useState } from "react"

/**
 * Browser geolocation with honest state separation.
 *
 * Returns the original { position, error } contract plus additive fields:
 *  - code:     GeolocationPositionError code (1 = permission denied) so UIs
 *              can tell "blocked" apart from "unavailable/timeout"
 *  - locating: true while a fix is in flight — callers must not render
 *              "nothing nearby" while this is true
 *  - retry:    re-request on demand (e.g. a "Use My Location" button)
 */
const useGeolocation = () => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)
  const [code, setCode] = useState(null)
  // A fix is requested on mount, so the honest initial state is "in flight".
  const [locating, setLocating] = useState(true)

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by this browser.")
      setLocating(false)
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
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

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect flush
    // (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(request, 0)
    return () => clearTimeout(t)
  }, [request])

  return { position, error, code, locating, retry: request }
}

export default useGeolocation
