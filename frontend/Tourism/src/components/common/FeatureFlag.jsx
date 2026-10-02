import { createContext, useContext, useState, useEffect } from "react"

const FeatureFlagContext = createContext(null)

/**
 * Feature flag provider — enables/disables features at runtime.
 * Flags can be set via localStorage or a remote config endpoint.
 */
export function FeatureFlagProvider({ children, flags = {} }) {
  const [featureFlags, setFeatureFlags] = useState(() => {
    try {
      const stored = localStorage.getItem("ny-feature-flags")
      return stored ? JSON.parse(stored) : flags
    } catch {
      return flags
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem("ny-feature-flags", JSON.stringify(featureFlags))
    } catch {
      // ignore
    }
  }, [featureFlags])

  const isEnabled = (key) => featureFlags[key] === true
  const enable = (key) => setFeatureFlags(prev => ({ ...prev, [key]: true }))
  const disable = (key) => setFeatureFlags(prev => ({ ...prev, [key]: false }))
  const toggle = (key) => setFeatureFlags(prev => ({ ...prev, [key]: !prev[key] }))

  return (
    <FeatureFlagContext.Provider value={{ featureFlags, isEnabled, enable, disable, toggle }}>
      {children}
    </FeatureFlagContext.Provider>
  )
}

export function useFeatureFlag() {
  const context = useContext(FeatureFlagContext)
  if (!context) throw new Error("useFeatureFlag must be used within FeatureFlagProvider")
  return context
}

/**
 * Conditionally renders children based on a feature flag.
 */
export function Feature({ flag, children, fallback = null }) {
  const { isEnabled } = useFeatureFlag()
  return isEnabled(flag) ? children : fallback
}
