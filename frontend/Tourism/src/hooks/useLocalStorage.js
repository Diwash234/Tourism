import { useState, useEffect } from "react"

/**
 * useLocalStorage — persist state in localStorage with JSON serialization.
 * Syncs across tabs via the `storage` event.
 */
export default function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored !== null ? JSON.parse(stored) : initialValue
    } catch {
      return initialValue
    }
  })

  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === key) {
        try {
          setValue(e.newValue !== null ? JSON.parse(e.newValue) : initialValue)
        } catch {
          setValue(initialValue)
        }
      }
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [key, initialValue])

  const setStoredValue = (newValue) => {
    const valueToStore = newValue instanceof Function ? newValue(value) : newValue
    setValue(valueToStore)
    try {
      localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch {
      // storage full or unavailable — ignore
    }
  }

  const removeStoredValue = () => {
    setValue(initialValue)
    try {
      localStorage.removeItem(key)
    } catch {
      // ignore
    }
  }

  return [value, setStoredValue, removeStoredValue]
}
