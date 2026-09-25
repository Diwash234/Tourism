import { useState } from "react"
import { Link } from "react-router-dom"
import { FiMapPin, FiSearch } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import EmptyState from "../components/common/EmptyState"
import SkeletonLoader from "../components/common/SkeletonLoader"
import HotelCard from "../components/cards/HotelCard"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import hotelApi from "../api/hotelApi"
import useAuth from "../hooks/useAuth"

export default function HotelSearch() {
  const [query, setQuery] = useState("")
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState("")
  const { isAuthenticated } = useAuth()

  const handleSearch = async (event) => {
    event.preventDefault()
    if (!query.trim()) {
      setError("Enter a place, property or area to search.")
      return
    }
    setLoading(true)
    setSearched(true)
    setError("")
    setHotels([])
    try {
      const data = await hotelApi.search(query.trim())
      setHotels(Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [])
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "We could not load the stay catalogue right now. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="hotel-search" />
      <PageHeader title="Find a hotel or lodge" subtitle="Search the live stay catalogue by place, property or area. Prices, ratings and availability appear only when the record provides them." />

      <form onSubmit={handleSearch} className="ny-panel flex flex-col gap-3 p-4 sm:flex-row" role="search">
        <div className="relative min-w-0 flex-1">
          <FiSearch size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" />
          <label htmlFor="hotel-search" className="sr-only">Search hotels and lodges</label>
          <input id="hotel-search" className="input-field pl-11" placeholder="Search Pokhara, a hotel name or an area" value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <button className="ny-btn ny-btn-primary" type="submit" disabled={loading}>{loading ? "Searching…" : "Search stays"}</button>
      </form>

      {error && <div role="alert" className="ny-panel border-[#E9B9B9] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)]">{error}</div>}
      {loading ? <SkeletonLoader count={6} /> : searched && hotels.length === 0 && !error ? (
        <EmptyState title="No stays match this search" subtitle="Try a broader place name or browse the full destination catalogue to continue exploring." action={<Link to="/destinations" className="ny-btn ny-btn-primary">Browse destinations</Link>} />
      ) : hotels.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {hotels.map((hotel) => {
            const bookingPath = `/hotels/${hotel.id}/book`
            return (
              <div key={hotel.id} className="flex h-full flex-col">
                <HotelCard hotel={hotel} />
                <Link to={isAuthenticated ? bookingPath : `/login?next=${encodeURIComponent(bookingPath)}`} className="ny-btn ny-btn-secondary mt-3 w-full">
                  Request a booking
                </Link>
              </div>
            )
          })}
        </div>
      ) : (
        <EmptyState title="Search the stay catalogue" subtitle="Enter a destination, property or area to see recorded stays and the details the catalogue actually provides." action={<Link to="/destinations" className="ny-btn ny-btn-secondary"><FiMapPin size={15} aria-hidden="true" />Browse destinations</Link>} />
      )}
    </div>
  )
}
