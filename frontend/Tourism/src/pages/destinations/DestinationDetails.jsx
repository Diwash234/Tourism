import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  FiStar, FiMapPin, FiHeart, FiPhoneCall, FiDollarSign,
  FiShield, FiHome, FiCoffee, FiShoppingBag, FiGlobe,
} from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import budgetApi from "../../api/budgetApi"
import userApi from "../../api/userApi"

import MapView from "../../components/map/MapView"
import WeatherCard from "../../components/cards/WeatherCard"
import HotelCard from "../../components/cards/HotelCard"
import PlaceholderImage from "../../components/common/PlaceholderImage"
import Loader from "../../components/common/Loader"
import useGeolocation from "../../hooks/useGeolocation"

import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

import { RISK_LEVELS } from "../../utils/constants"
import { formatCurrency } from "../../utils/helpers"

const DestinationDetails = () => {
  const { slug } = useParams()
  const navigate = useNavigate()

  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()

  const [destination, setDestination] = useState(null)
  const [budget, setBudget] = useState(null)
  const [essentials, setEssentials] = useState(null)

  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteRecordId, setFavoriteRecordId] = useState(null)

  const [loading, setLoading] = useState(true)
  const { position } = useGeolocation()

  useEffect(() => {
    setLoading(true)

    const params = {}
    if (position) {
      params.latitude = position.lat
      params.longitude = position.lng
    }

    Promise.allSettled([
      destinationApi.getById(slug, params),
      destinationApi.getEssentials(slug, params),
      // FIXED: was `budgetApi.estimate({ destinationId: slug, ... })` —
      // `destinationId` isn't a field the backend's
      // BudgetPredictionRequestSerializer recognizes at all (it's
      // `destination`), so this always silently estimated for a generic
      // trip instead of this specific place.
      budgetApi.estimate({ destination: slug, travelers: 1, days: 3 }),
    ]).then(([destRes, essentialsRes, budgetRes]) => {
      if (destRes.status === "fulfilled") {
        setDestination(destRes.value.data)
      }
      if (essentialsRes?.status === "fulfilled") {
        setEssentials(essentialsRes.value.data)
      }
      if (budgetRes.status === "fulfilled") {
        // FIXED: the ML response field is `total_budget_usd`, not
        // `total` — this always rendered "$0" before.
        setBudget({
          total: budgetRes.value.data.total_budget_usd ?? budgetRes.value.data.total ?? 0,
        })
      }
    }).finally(() => setLoading(false))
  }, [slug, position])

  // Once we know the destination's real numeric id, check whether it's
  // already in the user's favorites so the heart icon isn't wrong on
  // load, and so we have the FAVORITE RECORD's id ready for un-favoriting.
  useEffect(() => {
    if (!isAuthenticated || !destination?.id) return
    userApi.getFavorites()
      .then(({ data }) => {
        const list = data.results || data || []
        const match = list.find((f) => f.destination === destination.id)
        if (match) {
          setIsFavorite(true)
          setFavoriteRecordId(match.id)
        }
      })
      .catch(() => {})
  }, [isAuthenticated, destination?.id])

  const toggleFavorite = async () => {
    if (!isAuthenticated) {
      return showToast("Please login to save favorites", "info")
    }
    if (!destination?.id) return

    try {
      if (isFavorite) {
        // FIXED: was `userApi.removeFavorite(slug)` — two bugs at once.
        // removeFavorite needs the FAVORITE RECORD's id, not the
        // destination's id, AND `slug` (a string) was being sent where
        // a destination's numeric id was expected either way.
        if (favoriteRecordId) await userApi.removeFavorite(favoriteRecordId)
        setIsFavorite(false)
        setFavoriteRecordId(null)
      } else {
        // FIXED: was `userApi.addFavorite(slug)` — the backend's
        // Favorite.destination is a ForeignKey expecting the numeric id,
        // not the slug string, so this always failed silently.
        const { data } = await userApi.addFavorite(destination.id)
        setIsFavorite(true)
        setFavoriteRecordId(data.id)
      }
    } catch {
      showToast("Could not update favorite", "error")
    }
  }

  if (loading) return <Loader fullScreen />

  if (!destination) {
    return (
      <div className="container-app py-16 text-center text-gray-400">
        Destination not found.
      </div>
    )
  }

  // FIXED: `risk` was fetched from a commented-out, nonexistent
  // `alertApi.getRiskStatus(slug)` call — meaning Safety Status ALWAYS
  // showed the generic "LOW / No active risk advisory" fallback,
  // regardless of real conditions. essentials.active_alert is real,
  // destination-specific data that was already being fetched by the
  // /essentials/ call and simply never read.
  const activeAlert = essentials?.active_alert
  const level = RISK_LEVELS[activeAlert?.severity?.toUpperCase()] || RISK_LEVELS.LOW

  return (
    <div className="container-app py-10 fade-in">
      {/* Images */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-8 rounded-xl2 overflow-hidden">
        {destination.cover_image_url ? (
          <img
            src={destination.cover_image_url}
            alt={destination.name}
            className="lg:col-span-2 h-80 w-full object-cover"
          />
        ) : (
          <PlaceholderImage seed={destination.id} className="lg:col-span-2 h-80 w-full" iconSize={40} />
        )}
        <div className="grid grid-rows-2 gap-3">
          {destination.gallery?.[0]?.image || destination.gallery?.[0]?.external_url ? (
            <img
              src={destination.gallery[0].image || destination.gallery[0].external_url}
              alt="gallery"
              className="h-full w-full object-cover"
            />
          ) : (
            <PlaceholderImage seed={destination.id + 1} className="h-full w-full" />
          )}
          {destination.gallery?.[1]?.image || destination.gallery?.[1]?.external_url ? (
            <img
              src={destination.gallery[1].image || destination.gallery[1].external_url}
              alt="gallery"
              className="h-full w-full object-cover"
            />
          ) : (
            <PlaceholderImage seed={destination.id + 2} className="h-full w-full" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Title */}
          <div>
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold">{destination.name}</h1>
              <button onClick={toggleFavorite} className="p-2 rounded-full border hover:border-nepalred-300 transition-colors">
                <FiHeart className={isFavorite ? "text-nepalred-500 fill-nepalred-500" : "text-gray-500"} />
              </button>
            </div>

            <p className="text-gray-500 flex gap-1 mt-2 items-center">
              <FiMapPin size={14} />
              {destination.address}, {destination.city}, {destination.country}
            </p>

            <div className="flex items-center gap-1 text-saffron-600 mt-2">
              <FiStar className="fill-saffron-500" />
              {destination.average_rating || "4.5"} rating
            </div>
          </div>

          {/* Description */}
          <div>
            <h2 className="font-semibold text-lg mb-2">About this place</h2>
            <p className="text-gray-600 text-sm">{destination.description || "No description available"}</p>
          </div>

          {/* Video */}
          {destination.videos?.length > 0 && (
            <div>
              <h2 className="font-semibold text-lg mb-2">Video</h2>
              <video controls className="w-full rounded-xl" src={destination.videos[0].video || destination.videos[0].url} />
            </div>
          )}

          {/* NEW: Weather — data was already fetched via /essentials/,
              never displayed */}
          {essentials?.weather && (
            <div>
              <h2 className="font-semibold text-lg mb-3">Weather Right Now</h2>
              <WeatherCard
                location={destination.city}
                temp_c={essentials.weather.temperature_c ?? essentials.weather.temperature}
                condition={essentials.weather.description || essentials.weather.condition || "clear"}
                humidity={essentials.weather.humidity}
                wind_kmh={essentials.weather.wind_kmh}
              />
            </div>
          )}

          {/* NEW: Hotels near this destination — same /essentials/ data,
              never rendered before */}
          {essentials?.hotels?.length > 0 && (
            <div>
              <h2 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <FiHome className="text-himalaya-500" /> Where to Stay
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {essentials.hotels.map((hotel) => (
                  <HotelCard key={hotel.id} hotel={hotel} destinationName={destination.name} />
                ))}
              </div>
            </div>
          )}

          {/* NEW: Restaurants & shops nearby */}
          {(essentials?.restaurants?.length > 0 || essentials?.shops?.length > 0) && (
            <div>
              <h2 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <FiCoffee className="text-saffron-600" /> Nearby Restaurants & Shops
              </h2>
              <div className="grid sm:grid-cols-2 gap-3">
                {[...(essentials.restaurants || []), ...(essentials.shops || [])].slice(0, 6).map((place, i) => (
                  <div key={i} className="card-base p-4 flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-gray-50 text-gray-400 shrink-0">
                      <FiShoppingBag size={16} />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate">{place.name || "Unnamed place"}</p>
                      <p className="text-xs text-gray-400 truncate">{place.address || place.vicinity || ""}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Map */}
          <div>
            <h2 className="font-semibold text-lg mb-2">Location</h2>
            <MapView
              center={{ lat: Number(destination.latitude), lng: Number(destination.longitude) }}
              destination={{ lat: Number(destination.latitude), lng: Number(destination.longitude), name: destination.name }}
              nearbyAttractions={[]}
              height="380px"
            />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card-base p-5">
            <h3 className="font-semibold mb-3 flex gap-2 items-center">
              <FiShield /> Safety Status
            </h3>
            <span className={`${level.color} px-3 py-1 rounded-full text-xs`}>
              {level.label} Risk
            </span>
            <p className="text-sm text-gray-500 mt-2">
              {activeAlert?.title || activeAlert?.description || "No active risk advisory"}
            </p>
          </motion.div>

          <div className="card-base p-5">
            <h3 className="font-semibold mb-3 flex gap-2 items-center">
              <FiDollarSign /> Budget Estimate
            </h3>
            <p className="text-2xl font-bold text-himalaya-500">
              {formatCurrency(budget?.total || 0)}
            </p>
            <p className="text-xs text-gray-400">Estimated for 1 traveler, 3 days</p>
          </div>

          <div className="card-base p-5">
            <h3 className="font-semibold mb-3 flex gap-2 items-center">
              <FiPhoneCall /> Emergency Contacts
            </h3>
            {/* FIXED: this used to be a hardcoded generic string
                ("Police:100 · Ambulance:102 · Fire:101") regardless of
                which destination you were viewing. essentials.
                emergency_helplines is real, location-specific data from
                the SAME /essentials/ call, just never used. */}
            {essentials?.emergency_helplines?.length > 0 ? (
              <ul className="space-y-2 text-sm text-gray-600">
                {essentials.emergency_helplines.slice(0, 4).map((c) => (
                  <li key={c.id} className="flex justify-between">
                    <span className="truncate">{c.name}</span>
                    <a href={`tel:${c.phone_number}`} className="text-himalaya-500 font-medium shrink-0 ml-2">
                      {c.phone_number}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">Police: 100 · Ambulance: 102 · Fire: 101</p>
            )}
          </div>

          <button
            onClick={() => navigate(`/translation?place=${encodeURIComponent(destination.name)}`)}
            className="btn-outline w-full flex items-center justify-center gap-2"
          >
            <FiGlobe size={14} /> Translate Page
          </button>
        </div>
      </div>
    </div>
  )
}

export default DestinationDetails