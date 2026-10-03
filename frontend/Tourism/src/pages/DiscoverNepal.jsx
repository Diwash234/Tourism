import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import PageHeader from "../components/common/PageHeader"
import destinationApi from "../api/destinationApi"
import DestinationCard from "../components/cards/DestinationCard"
import ErrorState from "../components/ui/ErrorState"

const PAGE_SIZE = 12

const DiscoverNepal = () => {
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let active = true
    destinationApi.getAll({
      type: "attraction",
      page: 1,
      page_size: PAGE_SIZE,
      ordering: "name",
    }).then(({ data }) => {
      if (!active) return
      setDestinations(Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [])
      setError("")
    }).catch(() => {
      if (active) setError("We couldn't load recorded Nepal destinations right now.")
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [])

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <PageHeader eyebrow="Nepal" title="Discover Nepal" subtitle="Explore recorded destinations and places across Nepal." />
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => <div key={i} className="h-72 rounded-2xl bg-slate-100 animate-pulse" />)}
        </div>
      ) : error ? (
        <ErrorState title="Could not load destinations" message={error} onRetry={() => window.location.reload()} />
      ) : destinations.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {destinations.map((destination) => (
            <DestinationCard key={destination.id} destination={destination} />
          ))}
        </div>
      ) : (
        <div className="ny-panel p-8 text-center">
          <p className="font-bold text-slate-800">No public destinations are currently available.</p>
          <Link to="/destinations" className="ny-btn ny-btn-primary mt-4 inline-flex">Browse destinations</Link>
        </div>
      )}
    </div>
  )
}

export default DiscoverNepal
