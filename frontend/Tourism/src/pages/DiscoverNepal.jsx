import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import PageHeader from "../components/common/PageHeader"

const DiscoverNepal = () => {
  const [destinations, setDestinations] = useState([])

  useEffect(() => {
    // Fetch Nepal destinations or set up initial data
    const NepaliDestinations = [
      { id: 1, name: "Kathmandu", slug: "kathmandu", category_name: "Capital", district: "Kathmandu" },
      { id: 2, name: "Pokhara", slug: "pokhara", category_name: "Lake City", district: "Kaski" },
      { id: 3, name: "Chitwan", slug: "chitwan", category_name: "National Park", district: "Chitwan" },
      { id: 4, name: "Lumbini", slug: "lumbini", category_name: "Birthplace", district: "Rupandehi" },
      { id: 5, name: "Everest Region", slug: "everest-region", category_name: "Mountains", district: "Solukhumbu" },
    ]
    setDestinations(NepaliDestinations)
  }, [])

  return (
    <div className="container-app py-8">
      <PageHeader eyebrow="Nepal" title="Discover Nepal" subtitle="Explore the best destinations in the Himalayas" />
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-[var(--ny-green)] mb-6">Discover Nepal</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {destinations.map((dest) => (
            <div
              key={dest.id}
              className="card-base border border-slate-200 bg-white p-4 hover:shadow-md transition-shadow"
            >
              <h3 className="text-xl font-bold mb-2">{dest.name}</h3>
              <p className="text-[var(--ny-text-secondary)] text-sm">{dest.category_name}</p>
              <Link to={`/destinations/${dest.slug}`} className="text-[var(--ny-green)] font-medium mt-2 block">
                View details
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DiscoverNepal