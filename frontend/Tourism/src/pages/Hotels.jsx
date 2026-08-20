import { useEffect, useState } from "react"
import { FiSearch } from "react-icons/fi"
import hotelService from "../services/hotelService"
import HotelCard from "../components/cards/HotelCard"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

const Hotels = () => {
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [sort, setSort] = useState("recommended")

  useEffect(() => {
    setLoading(true)

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
      .catch(() => setHotels([]))
      .finally(() => setLoading(false))
  }, [search, sort])


  return (
    <div className="space-y-6 fade-in theme-gold">

      <div>
        <h1 className="section-title mb-2">
          Hotels & Stays
        </h1>

        <p className="text-gray-500">
          From teahouses on the Annapurna trail to boutique stays in Kathmandu.
        </p>
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

        <Loader fullScreen={false}/>

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
          title="No hotels found"
          subtitle="Try a different search, or check back once hotels are imported."
        />

      )}

    </div>
  )
}

export default Hotels