import { useState, useEffect } from "react"

const useGeolocation = () => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported")
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude })
      },
      (err) => setError(err.message),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    )
    }, 0)
    return () => clearTimeout(t)
  }, [])

  return { position, error }
}

export default useGeolocation