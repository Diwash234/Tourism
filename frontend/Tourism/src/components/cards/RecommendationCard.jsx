import { Link } from "react-router-dom"
import { FiTrendingUp, FiMapPin } from "react-icons/fi"
import PlaceholderImage from "../common/PlaceholderImage"

const RecommendationCard = ({ item }) => {
  const matchScore = Math.round(((item.score || item.ml_score || 0)) * 100)

  return (
    <div className="card-base p-5">
      <div className="flex items-center gap-2 text-forest-600 text-sm font-semibold">
        <FiTrendingUp />
        {matchScore}% match
      </div>

      {item.cover_image_url ? (
        <img src={item.cover_image_url} alt={item.name} className="w-full h-32 object-cover rounded-xl mt-3" />
      ) : (
        <PlaceholderImage seed={item.id || item.name} className="w-full h-32 rounded-xl mt-3" />
      )}

      <h3 className="font-bold text-lg mt-3">{item.name || "Unknown Destination"}</h3>

      <p className="text-gray-500 text-sm">{item.category || item.category_name}</p>

      <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
        <FiMapPin size={14} /> {item.city || "Nepal"}
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