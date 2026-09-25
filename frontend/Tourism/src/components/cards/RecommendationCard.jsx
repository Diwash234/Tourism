import { Link } from "react-router-dom"
import { FiTrendingUp, FiMapPin } from "react-icons/fi"
import PlaceholderImage from "../common/PlaceholderImage"

const RecommendationCard = ({ item }) => {
  const rawScore = item.score ?? item.ml_score
  const matchScore = rawScore == null ? null : Math.round(Number(rawScore) * 100)

  return (
    <div className="card-base overflow-hidden p-5">
      <div className="flex items-center gap-2 text-forest-600 text-sm font-semibold">
        <FiTrendingUp />
        {matchScore == null ? "Suggested for you" : `${matchScore}% match`}
      </div>

      <PlaceholderImage src={item.cover_image_url} title={item.name || "Destination"} alt={item.name || "Destination"} className="mt-3 h-32 w-full rounded-xl" />

      <h3 className="font-bold text-lg mt-3">{item.name || "Unknown Destination"}</h3>

      <p className="text-gray-500 text-sm">{item.category || item.category_name}</p>

      <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
        <FiMapPin size={14} /> {item.city || item.district || "Location unavailable"}
      </p>

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