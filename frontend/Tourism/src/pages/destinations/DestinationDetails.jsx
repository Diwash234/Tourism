import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { FiStar, FiMapPin, FiHeart, FiGlobe, FiPhoneCall, FiDollarSign, FiBookOpen } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import alertApi from "../../api/alertApi"
import budgetApi from "../../api/budgetApi"
import userApi from "../../api/userApi"
import MapView from "../../components/map/MapView"
import Loader from "../../components/common/Loader"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import { RISK_LEVELS } from "../../utils/constants"
import { formatCurrency } from "../../utils/helpers"
import { getDestinationById } from "../../data/nepalDestinations"

const DestinationDetails = () => {
  const { id } = useParams()
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [destination, setDestination] = useState(null)
  const [risk, setRisk] = useState(null)
  const [budget, setBudget] = useState(null)
  const [isFavorite, setIsFavorite] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([
      destinationApi.getById(id),
      alertApi.getRiskStatus(id),
      budgetApi.estimate({ destinationId: id, travelers: 1, days: 3 }),
    ]).then(([destRes, riskRes, budgetRes]) => {
      if (destRes.status === "fulfilled" && destRes.value.data) {
        setDestination(destRes.value.data)
      } else {
        setDestination(getDestinationById(id) || null)
      }
      if (riskRes.status === "fulfilled") setRisk(riskRes.value.data)
      if (budgetRes.status === "fulfilled") {
        setBudget(budgetRes.value.data)
      } else {
        const fallback = getDestinationById(id)
        if (fallback) setBudget({ total: fallback.price })
      }
      setLoading(false)
    })
  }, [id])

  const toggleFavorite = async () => {
    if (!isAuthenticated) return showToast("Please login to save favorites", "info")
    try {
      if (isFavorite) {
        await userApi.removeFavorite(id)
      } else {
        await userApi.addFavorite(id)
      }
      setIsFavorite(!isFavorite)
    } catch {
      showToast("Could not update favorite", "error")
    }
  }

  if (loading) return <Loader fullScreen />
  if (!destination) {
    return <div className="container-app py-16 text-center text-gray-400">Destination not found.</div>
  }

  const level = RISK_LEVELS[risk?.level?.toUpperCase()] || RISK_LEVELS.LOW

  return (
    <div className="container-app py-10">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-8 rounded-xl2 overflow-hidden">
        <img
          src={destination.image || "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900"}
          alt={destination.name}
          className="lg:col-span-2 h-80 w-full object-cover"
        />
        <div className="grid grid-rows-2 gap-3">
          <img
            src={destination.gallery?.[0] || "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=500"}
            className="h-full w-full object-cover"
            alt="gallery-1"
          />
          <img
            src={destination.gallery?.[1] || "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=500"}
            className="h-full w-full object-cover"
            alt="gallery-2"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div>
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold">{destination.name}</h1>
              <button onClick={toggleFavorite} className="p-2 rounded-full border border-gray-200 hover:bg-gray-50">
                <FiHeart className={isFavorite ? "text-primary-500 fill-primary-500" : "text-gray-500"} />
              </button>
            </div>
            <p className="text-gray-500 flex items-center gap-1 mt-1"><FiMapPin size={14} /> {destination.location}</p>
            <div className="flex items-center gap-1 text-yellow-500 mt-2">
              <FiStar className="fill-yellow-400" /> {destination.rating || "4.5"} rating
            </div>
          </div>

          <div>
            <h2 className="font-semibold text-lg mb-2">About this place</h2>
            <p className="text-gray-600 text-sm leading-relaxed">{destination.description || "No description available yet."}</p>
            {destination.localLanguage && (
              <span className="inline-block mt-3 text-xs font-medium text-secondary-600 bg-secondary-500/10 rounded-full px-3 py-1">
                Local language: {destination.localLanguage}
              </span>
            )}
          </div>

          {(destination.isHeritage || destination.heritageSites?.length) && (
            <div>
              <h2 className="font-semibold text-lg mb-2 flex items-center gap-2">
                <FiBookOpen className="text-primary-500" /> Local Heritage & Culture
              </h2>
              <p className="text-gray-600 text-sm leading-relaxed mb-4">
                {destination.heritageDescription ||
                  "This destination is home to historic sites and cultural traditions passed down through generations."}
              </p>
              {destination.heritageSites?.length ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {destination.heritageSites.map((site, idx) => (
                    <div key={idx} className="rounded-xl overflow-hidden group relative">
                      <img
                        src={site.image || "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400"}
                        alt={site.name}
                        className="h-28 w-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-2">
                        <p className="text-white text-xs font-medium">{site.name}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400",
                    "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=400",
                    "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?w=400",
                  ].map((src, idx) => (
                    <img key={idx} src={src} alt="heritage" className="h-28 w-full object-cover rounded-xl" />
                  ))}
                </div>
              )}
            </div>
          )}

          {destination.videoUrl && (
            <div>
              <h2 className="font-semibold text-lg mb-2">Video</h2>
              <video controls className="w-full rounded-xl2" src={destination.videoUrl} />
            </div>
          )}

          <div>
            <h2 className="font-semibold text-lg mb-2">Location & Nearby Attractions</h2>
            <MapView
              center={destination.coordinates}
              destination={{ ...destination.coordinates, name: destination.name }}
              nearbyAttractions={destination.nearbyAttractions || []}
              height="380px"
            />
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-base p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><FiGlobe /> Safety Status</h3>
            <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full ${level.color}`}>
              {level.label} Risk
            </span>
            <p className="text-sm text-gray-500 mt-2">{risk?.summary || "No active risk advisories for this location."}</p>
          </div>

          <div className="card-base p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><FiDollarSign /> Budget Estimate</h3>
            <p className="text-2xl font-bold text-primary-500">{formatCurrency(budget?.total)}</p>
            <p className="text-xs text-gray-400">Estimated for 1 traveler, 3 days</p>
          </div>

          <div className="card-base p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><FiPhoneCall /> Emergency Contacts</h3>
            <p className="text-sm text-gray-500">Police: 100 · Ambulance: 102 · Fire: 101</p>
          </div>

          <Link to="/translation" className="btn-outline w-full text-center block">Translate Page</Link>
        </div>
      </div>
    </div>
  )
}

export default DestinationDetails