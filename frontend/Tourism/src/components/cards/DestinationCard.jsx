import { Link } from "react-router-dom";
import { FiMapPin, FiStar, FiHeart } from "react-icons/fi";
import { motion } from "framer-motion";

const DestinationCard = ({
  destination,
  onToggleFavorite,
  isFavorite = false,
}) => {

  const {
    id,
    name,
    slug,
    city,
    country,
    cover_image_url,
    average_rating,
    entry_fee,
    short_description,
    distance_km,
  } = destination;


  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="card-base overflow-hidden group"
    >

      <div className="relative h-48 overflow-hidden">

        <img
          src={
            cover_image_url ||
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"
          }
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />


        <button
          onClick={() => onToggleFavorite?.(id)}
          className="absolute top-3 right-3 bg-white/90 p-2 rounded-full hover:bg-white"
        >

          <FiHeart
            className={
              isFavorite
                ? "text-red-500 fill-red-500"
                : "text-gray-600"
            }
          />

        </button>

      </div>



      <div className="p-4">

        <div className="flex items-start justify-between mb-1 gap-3">

          <div className="min-w-0">
            <h3 className="font-semibold text-dark truncate">{name}</h3>
            {distance_km != null && (
              <p className="text-xs text-gray-400 mt-1">{distance_km} km away</p>
            )}
          </div>


          <div className="flex items-center gap-1 text-sm text-yellow-500">

            <FiStar className="fill-yellow-400" />

            {average_rating || "0"}

          </div>

        </div>



        <p className="text-sm text-gray-500 flex items-center gap-1 mb-3">

          <FiMapPin size={14}/>

          {city}, {country}

        </p>



        <div className="flex justify-between items-center">


          <span className="font-bold text-primary-500">

            NPR {entry_fee || 0}

          </span>



          <Link
            to={`/destinations/${slug}`}
            className="text-sm font-semibold text-secondary-500 hover:underline"
          >

            View Details

          </Link>


        </div>


      </div>


    </motion.div>
  );
};


export default DestinationCard;
