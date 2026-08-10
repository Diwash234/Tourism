import { Link } from "react-router-dom"
import {
  FiMapPin,
  FiStar,
  FiHeart,
  FiThermometer,
  FiDollarSign,
} from "react-icons/fi"
import { motion } from "framer-motion"
import PlaceholderImage from "../common/PlaceholderImage"

const RISK_STYLES = {
  low: {
    label: "Low Risk",
    dot: "bg-forest-500",
    className: "text-green-600",
  },
  moderate: {
    label: "Moderate Risk",
    dot: "bg-saffron-500",
    className: "text-yellow-600",
  },
  high: {
    label: "High Risk",
    dot: "bg-nepalred-500",
    className: "text-red-600",
  },
}


// Category based color themes
const CATEGORY_THEMES = {
  mountains: {
    card: "bg-white border-gray-200",
    badge: "bg-gray-100 text-gray-700",
    icon: "text-gray-600",
  },

  lakes: {
    card: "bg-blue-50 border-blue-200",
    badge: "bg-blue-500 text-white",
    icon: "text-blue-500",
  },

  forest: {
    card: "bg-green-50 border-green-200",
    badge: "bg-green-600 text-white",
    icon: "text-green-600",
  },

  wildlife: {
    card: "bg-green-50 border-green-200",
    badge: "bg-green-600 text-white",
    icon: "text-green-600",
  },

  hotels: {
    card: "bg-yellow-50 border-yellow-200",
    badge: "bg-yellow-500 text-white",
    icon: "text-yellow-600",
  },

  heritage: {
    card: "bg-orange-50 border-orange-200",
    badge: "bg-orange-600 text-white",
    icon: "text-orange-600",
  },

  adventure: {
    card: "bg-orange-50 border-orange-300",
    badge: "bg-orange-500 text-white",
    icon: "text-orange-600",
  },
}


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
    distance_km,
    category,
    weather,
    budget_estimate,
    risk_level,
    recommended_season,
  } = destination


  const risk =
    RISK_STYLES[risk_level] ||
    RISK_STYLES.low


  const categoryKey =
  typeof category === "string"
    ? category.toLowerCase()
    : "mountains";


  const theme =
    CATEGORY_THEMES[categoryKey] ||
    CATEGORY_THEMES.mountains



  return (

    <motion.div

      whileHover={{
        y:-8,
        scale:1.02
      }}

      transition={{
        duration:0.3
      }}

      className={`
        overflow-hidden 
        rounded-2xl
        border
        shadow-sm
        hover:shadow-xl
        transition-all
        ${theme.card}
      `}

    >


      {/* IMAGE */}

      <div className="relative h-48 overflow-hidden">

        {
          cover_image_url ?

          (

          <img
            src={cover_image_url}
            alt={name}
            className="
            w-full
            h-full
            object-cover
            group-hover:scale-110
            transition-transform
            duration-500
            "
          />

          )

          :

          (

          <PlaceholderImage
            seed={id}
            className="w-full h-full"
          />

          )

        }



        <div className="
        absolute inset-0 
        bg-gradient-to-t 
        from-black/50 
        to-transparent
        "/>



        {/* FAVORITE */}

        <button

          onClick={() =>
            onToggleFavorite?.(id)
          }

          className="
          absolute
          top-3
          right-3
          bg-white/90
          p-2
          rounded-full
          hover:bg-white
          "

        >

          <FiHeart

            className={
              isFavorite
              ?
              "text-red-500 fill-red-500"
              :
              "text-gray-600"
            }

          />

        </button>



        {/* RATING */}

        <div className="
        absolute
        top-3
        left-3
        flex
        items-center
        gap-1
        bg-white/90
        px-3
        py-1
        rounded-full
        text-sm
        font-semibold
        ">

          <FiStar
            size={14}
            className="
            fill-yellow-500
            text-yellow-500
            "
          />

          {average_rating || "0"}

        </div>



        {/* CATEGORY */}

        
          {typeof category === "string" && (
  <span
    className={`
      absolute
      bottom-3
      left-3
      px-3
      py-1
      rounded-full
      text-xs
      font-semibold
      capitalize
      ${theme.badge}
    `}
  >
    {category}
  </span>
)}

        


      </div>




      {/* CONTENT */}


      <div className="p-4">


        <h3 className="
        font-bold
        text-dark
        text-lg
        truncate
        ">

          {name}

        </h3>



        <p className="
        text-sm
        text-gray-500
        flex
        items-center
        gap-1
        mt-1
        ">

          <FiMapPin size={14}/>

          {city}

          {
          country &&
          `, ${country}`
          }


          {
          distance_km != null &&
          (
          <span>
          · {distance_km} km
          </span>
          )
          }


        </p>




        <div className="
        flex
        flex-wrap
        gap-4
        my-4
        text-sm
        ">


        {
        weather &&

        <span className="flex items-center gap-1">

          <FiThermometer
          className={theme.icon}
          />

          {weather.temp_c}°C

        </span>

        }



        <span className="
        flex
        items-center
        gap-1
        font-semibold
        text-green-700
        ">

          <FiDollarSign/>

          {
          budget_estimate
          ?
          `$${budget_estimate}`
          :
          `NPR ${entry_fee || 0}`
          }


        </span>




        <span className={`
        flex
        items-center
        gap-1
        ${risk.className}
        `}>

          <span
          className={`
          w-2
          h-2
          rounded-full
          ${risk.dot}
          `}
          />

          {risk.label}

        </span>


        </div>



        {
        recommended_season &&

        <p className="
        text-xs
        text-gray-500
        mb-3
        ">

        Recommended:
        <span className="font-semibold">
        {" "}
        {recommended_season}
        </span>

        </p>

        }




        {
        slug ?

        (

        <Link

        to={`/destinations/${slug}`}

        className="
        block
        text-center
        bg-himalaya-500
        hover:bg-himalaya-600
        text-white
        py-2.5
        rounded-xl
        text-sm
        font-semibold
        "

        >

        Explore Now

        </Link>

        )

        :

        (

        <button

        disabled

        className="
        w-full
        bg-gray-100
        text-gray-400
        py-2.5
        rounded-xl
        "

        >

        Details unavailable

        </button>

        )

        }


      </div>


    </motion.div>

  )
}


export default DestinationCard