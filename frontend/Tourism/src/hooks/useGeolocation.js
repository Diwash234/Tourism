import { useState, useEffect } from "react"

const useGeolocation = () => {
  const [position, setPosition] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported")
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude })
      },
      (err) => setError(err.message),
      { enableHighAccuracy: true }
    )
  }, [])

  return { position, error }
}

export default useGeolocation