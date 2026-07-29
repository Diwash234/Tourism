import { Link } from "react-router-dom"
import { FiMapPin } from "react-icons/fi"

/**
 * NepalCultureCard
 * Deliberately shaped around the EXISTING Destination model fields
 * (name, short_description, city, cover_image_url, slug) rather than a
 * new backend model — see the chat notes on why Category + Destination
 * already covers "cultural experience" content. Pass a Destination
 * object tagged with a "Culture & Heritage" category.
 */
const NepalCultureCard = ({ destination }) => {
  const { name, short_description, city, cover_image_url, slug } = destination

  return (
    <div className="card-base overflow-hidden">
      <div className="h-44 overflow-hidden">
        <img
          src={cover_image_url || "https://images.unsplash.com/photo-1544967082-d9d25d867d66?w=600"}
          alt={name}
          className="w-full h-full object-cover"
        />
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
          className="inline-block mt-3 text-sm font-semibold text-himalaya-500 hover:text-himalaya-600"
        >
          Explore Culture →
        </Link>
      </div>
    </div>
  )
}

export default NepalCultureCard