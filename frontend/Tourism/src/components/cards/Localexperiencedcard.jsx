import { Link } from "react-router-dom"
import { FiUsers, FiMapPin } from "react-icons/fi"

/**
 * LocalExperienceCard
 * Same pattern as NepalCultureCard: a Destination tagged with a
 * "Local Experience" category (homestays, cooking classes, farming,
 * festivals), not a separate backend model.
 */
const LocalExperienceCard = ({ destination }) => {
  const { name, short_description, city, cover_image_url, slug } = destination

  return (
    <div className="card-base overflow-hidden group">
      <div className="h-44 overflow-hidden relative">
        <img
          src={cover_image_url || "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600"}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <span className="absolute top-3 left-3 flex items-center gap-1 bg-forest-500 text-white text-xs font-semibold px-2.5 py-1 rounded-full">
          <FiUsers size={12} /> Community-led
        </span>
      </div>
      <div className="p-4">
        <h3 className="font-bold text-dark">{name}</h3>
        {short_description && (
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{short_description}</p>
        )}
        {city && (
          <p className="text-xs text-gray-400 flex items-center gap-1 mt-2">
            <FiMapPin size={12} /> {city}
          </p>
        )}
        <Link
          to={slug ? `/destinations/${slug}` : "#"}
          className="inline-block mt-3 text-sm font-semibold text-forest-600 hover:text-forest-700"
        >
          Join the Experience →
        </Link>
      </div>
    </div>
  )
}

export default LocalExperienceCard