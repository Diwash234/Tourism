import { Link } from "react-router-dom"
import { FiMapPin, FiStar, FiHeart } from "react-icons/fi"
import { motion } from "framer-motion"

const DestinationCard = ({ destination, onToggleFavorite, isFavorite }) => {
  const { id, name, location, image, rating, price } = destination

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="card-base overflow-hidden group"
    >
      <div className="relative h-48 overflow-hidden">
        <img
          src={image || "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <button
          onClick={() => onToggleFavorite?.(id)}
          className="absolute top-3 right-3 bg-white/90 p-2 rounded-full hover:bg-white"
        >
          <FiHeart className={isFavorite ? "text-primary-500 fill-primary-500" : "text-gray-600"} />
        </button>
      </div>
      <div className="p-4">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-dark truncate">{name}</h3>
          <div className="flex items-center gap-1 text-sm text-yellow-500">
            <FiStar className="fill-yellow-400" />
            {rating || "4.5"}
          </div>
        </div>
        <p className="text-sm text-gray-500 flex items-center gap-1 mb-3">
          <FiMapPin size={14} /> {location}
        </p>
        <div className="flex items-center justify-between">
          <span className="font-bold text-primary-500">${price || "--"}<span className="text-xs text-gray-400 font-normal"> /trip</span></span>
          <Link to={`/destinations/${id}`} className="text-sm font-semibold text-secondary-500 hover:underline">
            View Details
          </Link>
        </div>
      </div>
    </motion.div>
  )
}

export default DestinationCard