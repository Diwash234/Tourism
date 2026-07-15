import { useEffect, useState } from "react"
import { FiSun, FiCloud, FiCloudRain, FiMapPin, FiHeart } from "react-icons/fi"
import useAuth from "../hooks/useAuth"
import useGeolocation from "../hooks/useGeolocation"
import weatherApi from "../api/weatherApi"
import recommendationApi from "../api/recommendationApi"
import alertApi from "../api/alertApi"
import budgetApi from "../api/budgetApi"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import BudgetCard from "../components/cards/BudgetCard"
import AlertCard from "../components/cards/AlertCard"
import RecommendationCard from "../components/cards/RecommendationCard"
import DestinationCard from "../components/cards/DestinationCard"

const weatherIcons = { clear: FiSun, clouds: FiCloud, rain: FiCloudRain }

const Dashboard = () => {
  const { user } = useAuth()
  const { position } = useGeolocation()
  const [weather, setWeather] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [alerts, setAlerts] = useState([])
  const [budget, setBudget] = useState(null)
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadAll = async () => {
      try {
        const [recRes, alertRes, budgetRes, favRes] = await Promise.allSettled([
          recommendationApi.getPersonalized(),
          alertApi.getAlerts({ limit: 4 }),
          budgetApi.getSummary(),
          userApi.getFavorites(),
        ])
        if (recRes.status === "fulfilled") setRecommendations(recRes.value.data.items || recRes.value.data || [])
        if (alertRes.status === "fulfilled") setAlerts(alertRes.value.data.items || alertRes.value.data || [])
        if (budgetRes.status === "fulfilled") setBudget(budgetRes.value.data)
        if (favRes.status === "fulfilled") setFavorites(favRes.value.data.items || favRes.value.data || [])
      } finally {
        setLoading(false)
      }
    }
    loadAll()
  }, [])

  useEffect(() => {
    if (position) {
      weatherApi
        .getCurrentWeather({ lat: position.lat, lng: position.lng })
        .then(({ data }) => setWeather(data))
        .catch(() => setWeather(null))
    }
  }, [position])

  const WeatherIcon = weatherIcons[weather?.condition?.toLowerCase()] || FiSun

  if (loading) return <Loader fullScreen={false} />

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.name || "Traveler"} 👋</h1>
        <p className="text-gray-500 text-sm">Here is what is happening with your trips today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-base p-5 md:col-span-1 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <FiMapPin size={14} /> {weather?.location || "Current Location"}
            </p>
            <p className="text-3xl font-bold mt-1">{weather?.temperature ?? "--"}°</p>
            <p className="text-sm text-gray-400 capitalize">{weather?.condition || "Fetching weather..."}</p>
          </div>
          <WeatherIcon size={42} className="text-primary-500" />
        </div>

        <BudgetCard label="Total Budget" amount={budget?.total} />
        <BudgetCard label="Spent So Far" amount={budget?.spent} accent="secondary" />
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">Latest Alerts</h2>
        </div>
        {alerts.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {alerts.map((a) => <AlertCard key={a.id} alert={a} />)}
          </div>
        ) : (
          <EmptyState title="No alerts right now" subtitle="You will be notified of any safety updates." />
        )}
      </div>

      <div>
        <h2 className="font-semibold text-lg mb-4">Recommended For You</h2>
        {recommendations.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((r) => <RecommendationCard key={r.id} item={r} />)}
          </div>
        ) : (
          <EmptyState title="No recommendations yet" subtitle="Explore destinations to get personalized picks." />
        )}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg flex items-center gap-2"><FiHeart className="text-primary-500" /> Favorite Places</h2>
        </div>
        {favorites.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {favorites.map((d) => <DestinationCard key={d.id} destination={d} isFavorite />)}
          </div>
        ) : (
          <EmptyState title="No favorites yet" subtitle="Tap the heart icon on any destination to save it." />
        )}
      </div>
    </div>
  )
}

export default Dashboard