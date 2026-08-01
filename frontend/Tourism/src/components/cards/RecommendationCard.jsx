import { Link } from "react-router-dom"
import { FiTrendingUp, FiMapPin } from "react-icons/fi"

const RecommendationCard = ({ item }) => {
  const matchScore = Math.round((item.score || 0) * 100)

  return (
    <div className="card-base p-5">
      <div className="flex items-center gap-2 text-forest-600 text-sm font-semibold">
        <FiTrendingUp />
        {matchScore}% match
      </div>

      <h3 className="font-bold text-lg mt-3">{item.name || "Unknown Destination"}</h3>

      <p className="text-gray-500 text-sm">{item.category}</p>

      <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
        <FiMapPin size={14} /> {item.city || "Nepal"}
      </p>

      {/* FIXED: was `to={`/destinations/${item.name}`}` — linking by the
          destination's NAME (e.g. "Pokhara Lakeside") instead of its
          slug. DestinationDetails.jsx fetches by slug, so this always
          produced a broken URL that would 404. */}
      {item.slug ? (
        <Link to={`/destinations/${item.slug}`} className="text-himalaya-500 mt-3 block font-semibold text-sm hover:underline">
          Explore Destination
        </Link>
      ) : (
        <span className="text-gray-300 mt-3 block text-sm">Details unavailable</span>
      )}
    </div>
  )
}

export default RecommendationCard