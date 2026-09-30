import { useEffect, useState } from "react"
import { useLocation } from "react-router-dom"

/**
 * Page transition wrapper — fades in new pages and fades out old ones.
 * Provides smooth navigation between routes.
 */
export default function PageTransition({ children }) {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState("fadeIn")

  useEffect(() => {
    if (location.pathname !== displayLocation.pathname) {
      setTransitionStage("fadeOut")
    }
  }, [location, displayLocation])

  const handleAnimationEnd = () => {
    if (transitionStage === "fadeOut") {
      setDisplayLocation(location)
      setTransitionStage("fadeIn")
    }
  }

  return (
    <div
      className={`transition-opacity duration-300 ${
        transitionStage === "fadeIn" ? "opacity-100" : "opacity-0"
      }`}
      onTransitionEnd={handleAnimationEnd}
    >
      {children}
    </div>
  )
}
