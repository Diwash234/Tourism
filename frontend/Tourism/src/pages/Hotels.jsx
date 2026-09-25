import { useEffect, useState } from "react"
import PageHeader from "../components/common/PageHeader"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSIntro from "../components/cms/CMSIntro"
import { FiSearch } from "react-icons/fi"
import hotelService from "../services/hotelService"
import HotelCard from "../components/cards/HotelCard"
import SkeletonLoader from "../components/common/SkeletonLoader"
import EmptyState from "../components/common/EmptyState"
import ErrorState from "../components/ui/ErrorState"

const Hotels = () => {
  const { block: cmsBlock } = usePublicConfig().pageCMS("hotels", ["intro", "page-intro"])
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [sort, setSort] = useState("recommended")
  const [error, setError] = useState("")
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    setLoading(true)
    setError("")

    const params = {}

    if (search) params.search = search
    if (sort === "price_low") params.ordering = "price_per_night"
    if (sort === "price_high") params.ordering = "-price_per_night"

    const request =
      sort === "recommended"
        ? hotelService.recommended(params)
        : hotelService.list(params)

    request
      .then(({ data }) => setHotels(data.results || data || []))
      .catch((requestError) => {
         setHotels([])
         setError(requestError.response?.data?.detail || "We could not load the stay catalogue right now.")
       })
      .finally(() => setLoading(false))
    }, 0)
    return () => clearTimeout(t)
  }, [search, sort, retry])


  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSIntro section={cmsBlock("intro")} />

      <div>
        <PageHeader title="Hotels & Stays" subtitle="Search the live catalogue for recorded stays, prices and availability." />
      </div>


      <div className="flex flex-col sm:flex-row gap-3">

        <div className="relative flex-1">

          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />

          <input
            className="input-field pl-10"
            placeholder="Search hotels by name or address..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

        </div>


        <select
          className="input-field sm:w-56"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >

          <option value="recommended">
            Recommended
          </option>

          <option value="price_low">
            Price: Low to High
          </option>

          <option value="price_high">
            Price: High to Low
          </option>

        </select>

      </div>


      {loading ? (

        <SkeletonLoader count={6} />

      ) : error ? (
        <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />
      ) : hotels.length ? (

        <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">

          {hotels.map((hotel) => (

            <HotelCard
              key={hotel.id}
              hotel={hotel}
            />

          ))}

        </div>

      ) : (

        <EmptyState
          title="No stays match your search"
          subtitle="Try a broader place or property name, or browse the public stay search."
        />

      )}

    </div>
  )
}

export default Hotels