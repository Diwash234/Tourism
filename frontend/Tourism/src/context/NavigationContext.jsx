import React, { createContext, useState } from "react"

export const NavigationContext = createContext(null)

export const NavigationProvider = ({ children }) => {
  const [activeRoute, setActiveRoute] = useState([])
  const [activeDestination, setActiveDestination] = useState(null)
  const [hudActive, setHudActive] = useState(true)

  return (
    <NavigationContext.Provider value={{ activeRoute, setActiveRoute, activeDestination, setActiveDestination, hudActive, setHudActive }}>
      {children}
    </NavigationContext.Provider>
  )
}
