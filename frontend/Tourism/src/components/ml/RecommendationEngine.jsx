import { useEffect, useState } from "react"
import { FiCompass, FiMapPin, FiArrowRight } from "react-icons/fi"
import { Link } from "react-router-dom"
import destinationApi from "../../api/destinationApi"
import { hasValidCoords } from "../../utils/placeUtils"

export default function RecommendationEngine() {
  const [items, setItems] = useState([])
  const [error, setError] = useState("")

  useEffect(() => {
    destinationApi.getDestinations({ featured: true, page_size: 4, limit: 4 })
      .then(({ data }) => {
        const list = data.results || data || []
        const recorded = (Array.isArray(list) ? list : []).filter((row) => row?.name && hasValidCoords(row.latitude, row.longitude))
        if (recorded.length) {
          setItems(recorded.slice(0, 4))
          return
        }
        return destinationApi.getDestinations({ page_size: 4, limit: 4 })
          .then(({ data: fallback }) => {
            const rows = fallback.results || fallback || []
            setItems((Array.isArray(rows) ? rows : []).filter((row) => row?.name).slice(0, 4))
          })
      })
      .catch(() => {
        setItems([])
        setError("Recorded destinations are unavailable right now.")
      })
  }, [])

  return (
    <div className="card-base p-6 space-y-4 bg-gradient-to-br from-white to-purple-50/50 border border-purple-100 rounded-3xl shadow-xl">
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
            <FiCompass className="text-purple-600" /> Recorded destination picks
          </h3>
          <p className="text-xs text-gray-500">Live featured destinations from the database. No invented match scores.</p>
        </div>
      </div>

      {!items.length && (
        <p className="text-xs text-slate-500">{error || "No recorded destinations with coordinates are available yet."}</p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.map((rec) => (
          <div key={rec.slug || rec.id} className="p-4 rounded-2xl bg-white border border-purple-100 hover:border-purple-300 transition-all space-y-1.5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-400 flex items-center gap-1">
                <FiMapPin /> {rec.city || rec.district || "Not recorded"}
              </span>
            </div>
            <h4 className="font-bold text-gray-900 text-sm">{rec.name}</h4>
            <p className="text-[11px] text-gray-500">{rec.short_description || rec.district || "Recorded destination"}</p>
            {rec.slug && (
              <Link to={`/destinations/${rec.slug}`} className="text-xs font-bold text-purple-700 hover:text-purple-900 flex items-center gap-1 pt-1">
                Explore Destination <FiArrowRight size={12} />
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
