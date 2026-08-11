import React, { createContext, useState, useEffect } from "react"
import destinationApi from "../api/destinationApi"

export const DestinationContext = createContext(null)

export const DestinationProvider = ({ children }) => {
  const [destinations, setDestinations] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)

  const loadDestinations = async (params = {}) => {
    setLoading(true)
    try {
      const { data } = await destinationApi.getAll(params)
      setDestinations(data.results || data || [])
    } catch {
      setDestinations([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    destinationApi.getCategories().then(({ data }) => setCategories(data.results || data || [])).catch(() => {})
    loadDestinations()
  }, [])

  return (
    <DestinationContext.Provider value={{ destinations, categories, loading, loadDestinations }}>
      {children}
    </DestinationContext.Provider>
  )
}
