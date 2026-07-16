import { Link } from "react-router-dom"
import { FiTrendingUp } from "react-icons/fi"

const RecommendationCard = ({ item }) => (
  <div className="card-base overflow-hidden flex flex-col sm:flex-row">
    <img
      src={item.image || "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=400"}
      alt={item.name}
      className="sm:w-40 h-40 sm:h-auto object-cover"
    />
    <div className="p-4 flex-1 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-secondary-500 mb-1">
          <FiTrendingUp /> {item.matchScore || 90}% match
        </div>
        <h4 className="font-semibold">{item.name}</h4>
        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{item.reason}</p>
      </div>
      <Link to={`/destinations/${item.id}`} className="text-sm font-semibold text-primary-500 hover:underline mt-2">
        Explore
      </Link>
    </div>
  </div>
)

export default RecommendationCard