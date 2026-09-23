import { useState, useEffect, useCallback } from "react"

// Generic data-fetching hook: pass an axios-returning function.
// Example: useFetch(() => destinationApi.getAll({ page }), [page])
const useFetch = (fetcher, deps = []) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetcher()
      setData(res.data)
    } catch (err) {
      setError(err?.response?.data?.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps, react-hooks/use-memo -- deps are caller-provided (dynamic by design), so no array literal is possible here
  }, deps)

  useEffect(() => {
    load()
  }, [load])

  return { data, loading, error, refetch: load }
}

export default useFetch