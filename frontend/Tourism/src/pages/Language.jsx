import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import destinationApi from "../api/destinationApi"
import DestinationCard from "../components/cards/DestinationCard"
import SearchBar from "../components/common/SearchBar"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

const Language = () => {
  const [query, setQuery] = useState("")
  const [destinations, setDestinations] = useState([])
  const [districts, setDistricts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    setLoading(true)
    setError("")

    const params = query
      ? { search: query, q: query, limit: 50 }
      : { limit: 200 }

    destinationApi
      .getAll(params)
      .then(({ data }) => {
        const items = data.results || data || []

        if (query) {
          setDestinations(items)
          setDistricts([])
        } else {
          const map = new Map()
          items.forEach((destination) => {
            const city = (destination.city || destination.country || destination.name || "Unknown").trim()
            const key = city.toLowerCase()
            if (!map.has(key)) {
              map.set(key, {
                name: city,
                count: 1,
                cover_image_url: destination.cover_image_url,
                slug: destination.slug,
                example_destination: destination,
              })
            } else {
              const district = map.get(key)
              district.count += 1
            }
          })
          setDistricts(Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name)))
          setDestinations([])
        }
      })
      .catch(() => {
        setError("Failed to load destinations. Please try again.")
        setDestinations([])
        setDistricts([])
      })
      .finally(() => setLoading(false))
  }, [query])

  return (
    <div className="container-app py-10">
      <h1 className="section-title">District Search</h1>
      <p className="text-gray-500 mb-6">
        Search for destinations by district, city, or name. Results show destination
        images, location details, and quick access to destination pages.
      </p>

      <SearchBar
        className="mb-8"
        placeholder="Search districts, cities, or destination names..."
        onSearch={(q) => setQuery(q)}
      />

      {loading ? (
        <Loader />
      ) : error ? (
        <EmptyState title="Search failed" subtitle={error} />
      ) : query ? (
        destinations.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No destinations found"
            subtitle="Try a different district or destination name."
          />
        )
      ) : districts.length ? (
        <div>
          <div className="mb-6 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">All Districts</h2>
              <p className="text-gray-500 text-sm">
                Browse districts with destination images and details from every region.
              </p>
            </div>
            <div className="text-sm text-gray-500">{districts.length} districts</div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {districts.map((district) => (
              <Link
                key={district.name}
                to={`/destinations/${district.example_destination.slug}`}
                className="card-base overflow-hidden group block"
              >
                <div className="relative h-56 overflow-hidden">
                  <img
                    src={
                      district.cover_image_url ||
                      "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900"
                    }
                    alt={district.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-lg mb-2">{district.name}</h3>
                  <p className="text-sm text-gray-500 mb-3">
                    {district.count} destination{district.count === 1 ? "" : "s"}
                  </p>
                  <div className="text-primary-500 font-semibold">View highlights</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState
          title="No districts available"
          subtitle="Add destinations in the admin panel or refresh to try again."
        />
      )}
    </div>
  )
}

export default Language
