import { useEffect, useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import {
  FiMapPin,
  FiHeart,
  FiUpload,
  FiSearch,
  FiImage,
  FiTrendingUp,
  FiX,
  FiCalendar,
  FiDollarSign,
  FiCompass,
  FiSettings,
  FiStar,
  FiShield,
  FiPlus,
  FiEdit3,
  FiCheckCircle,
  FiClock,
  FiSliders,
  FiTag,
  FiAlertTriangle,
  FiZap,
  FiRefreshCw,
  FiShare2,
} from "react-icons/fi"

import useAuth from "../hooks/useAuth"
import useGeolocation from "../hooks/useGeolocation"
import usePublicConfig from "../hooks/usePublicConfig"
import useToast from "../hooks/useToast"

import weatherApi from "../api/weatherApi"
import recommendationApi from "../api/recommendationApi"
import alertApi from "../api/alertApi"
import budgetApi from "../api/budgetApi"
import userApi from "../api/userApi"
import emergencyApi from "../api/emergencyApi"
import itineraryApi from "../api/itineraryApi"
import bookingApi from "../api/bookingApi"
import axiosClient from "../api/axiosClient"

import { destinationApi, photoApi } from "../services/api"
import { displayName, unwrapFavoriteDestination } from "../utils/placeUtils"

import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"

import BudgetCard from "../components/cards/BudgetCard"
import AlertCard from "../components/cards/AlertCard"
import RecommendationCard from "../components/cards/RecommendationCard"
import DestinationCard from "../components/cards/DestinationCard"
import WeatherCard from "../components/cards/WeatherCard"
import SafetyOverview from "../components/cards/SafetyOverview"
import HotelCard from "../components/cards/HotelCard"
import NepalExperienceSection from "../components/dashboard/NepalExperienceSection"
import NepalHighlights from "../components/dashboard/NepalHighlights"
import NationalSymbols from "../components/dashboard/NationalSymbols"
import VisitorNoticeBanner from "../components/common/VisitorNoticeBanner"
import hotelService from "../services/hotelService"
import UserFeedbackModal from "../components/user/UserFeedbackModal"
import ReportErrorModal from "../components/common/ReportErrorModal"
import AddExpenseModal from "../components/user/AddExpenseModal"

function unwrapList(response) {
  return response?.data?.results || response?.data?.items || response?.data || []
}

function scoreFromAlerts(alerts = []) {
  const penalty = alerts.reduce((sum, a) => {
    const level = (a.level || a.severity || "").toLowerCase()
    return sum + (level === "high" ? 15 : level === "moderate" ? 8 : 4)
  }, 0)
  return Math.max(40, 100 - penalty)
}

const Dashboard = () => {
  const { user } = useAuth()
  const { pages, section, notices = [] } = usePublicConfig()
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get("tab") || "overview"
  const setActiveTab = (tab) => setSearchParams(tab === "overview" ? {} : { tab })

  const dashboardPage = pages?.find((page) => page.key === "dashboard")
  const managed = Boolean(dashboardPage?.sections?.length)
  const block = (key) => section("dashboard", key)
  const showBlock = (key) => !managed || Boolean(block(key))

  const [phoneBannerDismissed, setPhoneBannerDismissed] = useState(false)
  const { position } = useGeolocation()
  const navigate = useNavigate()

  // Dashboard Data State
  const [weather, setWeather] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [alerts, setAlerts] = useState([])
  const [budget, setBudget] = useState(null)
  const [favorites, setFavorites] = useState([])
  const [destinations, setDestinations] = useState([])
  const [hotels, setHotels] = useState([])
  const [nearbySafety, setNearbySafety] = useState(null)
  const [travelPlans, setTravelPlans] = useState([])
  const [userBookings, setUserBookings] = useState([])
  const [userReports, setUserReports] = useState([])
  const [loading, setLoading] = useState(true)

  // AI Replanner state
  const [selectedPlanForModify, setSelectedPlanForModify] = useState(null)
  const [modifyingPlan, setModifyingPlan] = useState(false)

  // Hero / Search state
  const [heroQuery, setHeroQuery] = useState("")
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showReportErrorModal, setShowReportErrorModal] = useState(false)
  const [showAddExpenseModal, setShowAddExpenseModal] = useState(false)
  const [reportTargetDest, setReportTargetDest] = useState(null)

  // Preferences Form State
  const [preferencesForm, setPreferencesForm] = useState({
    travel_style: "nature",
    pace: "moderate",
    interests: ["trekking", "culture", "photography"],
    preferred_transport: "bus",
    group_type: "solo",
    dietary_needs: "none",
    max_budget_npr: 50000,
  })
  const [savingPrefs, setSavingPrefs] = useState(false)

  // Community Photo Upload State
  const [query, setQuery] = useState("")
  const [results, setResults] = useState([])
  const [selected, setSelected] = useState(null)
  const [file, setFile] = useState(null)
  const [caption, setCaption] = useState("")
  const [status, setStatus] = useState("")
  const [myPhotos, setMyPhotos] = useState([])

  const loadDashboardData = async () => {
    try {
      const [
        recRes,
        alertRes,
        budgetRes,
        favRes,
        destRes,
        hotelRes,
        plansRes,
        bookingsRes,
        reportsRes,
      ] = await Promise.allSettled([
        recommendationApi.getPersonalized(),
        alertApi.getAlerts({ limit: 4 }),
        budgetApi.getSummary(),
        userApi.getFavorites(),
        destinationApi.list({ limit: 6, featured: true }),
        hotelService.recommended({ limit: 4 }),
        itineraryApi.listPlans(),
        bookingApi.getMyBookings(),
        axiosClient.get("/reports/submit/").catch(() => ({ data: [] })),
      ])

      if (recRes.status === "fulfilled") setRecommendations(unwrapList(recRes.value))
      if (alertRes.status === "fulfilled") setAlerts(unwrapList(alertRes.value))
      if (favRes.status === "fulfilled") setFavorites(unwrapList(favRes.value))
      if (destRes.status === "fulfilled") setDestinations(unwrapList(destRes.value))
      if (hotelRes.status === "fulfilled") setHotels(unwrapList(hotelRes.value))
      if (plansRes.status === "fulfilled") setTravelPlans(unwrapList(plansRes.value))
      if (bookingsRes.status === "fulfilled") setUserBookings(unwrapList(bookingsRes.value))
      if (reportsRes.status === "fulfilled") setUserReports(unwrapList(reportsRes.value))

      if (budgetRes.status === "fulfilled") {
        setBudget({
          total: budgetRes.value?.data?.total_amount ?? 0,
          spent: budgetRes.value?.data?.total_amount ?? 0,
          entryCount: budgetRes.value?.data?.entry_count ?? 0,
          byCategory: budgetRes.value?.data?.by_category ?? [],
        })
      }

      // Load preferences from local storage or profile if present
      const savedPrefs = localStorage.getItem("nepal_yatra_user_preferences")
      if (savedPrefs) {
        try {
          setPreferencesForm(JSON.parse(savedPrefs))
        } catch {}
      }
    } catch (error) {
      console.log("Dashboard data load error:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  useEffect(() => {
    if (!position) return

    weatherApi
      .getCurrentWeather({ lat: position.lat, lng: position.lng })
      .then((res) => setWeather(res.data))
      .catch(() => setWeather(null))

    emergencyApi
      .nearby(position.lat, position.lng, { radius_km: 25, limit: 4 })
      .then(({ data }) => setNearbySafety(data))
      .catch(() => setNearbySafety(null))
  }, [position])

  const handleHeroSearch = (e) => {
    e.preventDefault()
    if (!heroQuery.trim()) return
    navigate(`/destinations?q=${encodeURIComponent(heroQuery)}`)
  }

  // AI Itinerary Modification Actions ("Make cheaper", "Add culture", etc.)
  const handleModifyItinerary = async (actionPrompt, plan = null) => {
    const targetPlan = plan || selectedPlanForModify || travelPlans[0]
    if (!targetPlan) {
      showToast("No active itinerary selected to modify. Create one in Trip Planner first!", "info")
      navigate("/trip-planner")
      return
    }

    setModifyingPlan(true)
    try {
      const { data } = await axiosClient.post("/ml/itinerary/modify/", {
        plan_id: targetPlan.id,
        action: actionPrompt,
        itinerary: targetPlan.itinerary_data || targetPlan,
      })

      showToast(`AI Modified Itinerary: "${actionPrompt}" applied!`, "success")
      loadDashboardData()
    } catch (err) {
      showToast(err.response?.data?.detail || "AI modification failed.", "error")
    } finally {
      setModifyingPlan(false)
    }
  }

  // Save User Preference Profile
  const handleSavePreferences = async (e) => {
    e.preventDefault()
    setSavingPrefs(true)
    try {
      localStorage.setItem("nepal_yatra_user_preferences", JSON.stringify(preferencesForm))
      await userApi.updateProfile({
        bio: `${preferencesForm.travel_style.toUpperCase()} traveler • ${preferencesForm.pace} pace • Budget NPR ${preferencesForm.max_budget_npr.toLocaleString()}`,
      })
      showToast("Travel Preference Profile updated successfully!", "success")
    } catch (err) {
      showToast("Preferences saved locally!", "info")
    } finally {
      setSavingPrefs(false)
    }
  }

  // Community Photo Upload handlers
  const runSearch = async (term) => {
    if (!term.trim()) return
    try {
      const { data } = await destinationApi.search(term)
      setResults(data.results || data || [])
    } catch (err) {
      console.log(err)
    }
  }

  const selectDestination = async (place) => {
    setSelected(place)
    try {
      const { data } = await photoApi.get(place.slug)
      setMyPhotos(data.photos || [])
    } catch (err) {
      console.log(err)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selected || !file) return

    const formData = new FormData()
    formData.append("image", file)
    formData.append("caption", caption)

    try {
      setStatus("Uploading photo...")
      await photoApi.upload(selected.slug, formData)
      setStatus("Photo uploaded successfully! It will automatically become the cover photo if it becomes popular.")
      const { data } = await photoApi.get(selected.slug)
      setMyPhotos(data.photos || [])
      setFile(null)
      setCaption("")
      showToast("Photo uploaded to destination gallery!", "success")
    } catch (err) {
      setStatus(err.response?.status === 401 ? "Please login first." : "Upload failed.")
      showToast("Upload failed. Please check permissions.", "error")
    }
  }

  if (loading) {
    return <Loader fullScreen={false} />
  }

  const totalSpentNpr = budget?.spent ?? 0
  const activeBookingsCount = userBookings.filter((b) => b.status !== "cancelled").length

  return (
    <div className="space-y-8 fade-in">
      {/* 1. National Symbols Branding */}
      {showBlock("national-symbols") && <NationalSymbols />}

      {/* 2. Welcome Banner & Persona Header */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-[#0B3D91] to-slate-950 text-white p-6 md:p-10 border border-slate-800 shadow-2xl">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_20%_20%,white,transparent_40%)]" />
        <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black uppercase tracking-wider shadow">
                Nepal Yatra Explorer
              </span>
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold">
                ✓ GPS Location Active
              </span>
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
              Namaste, {displayName(user)} 👋
            </h1>
            <p className="text-slate-200 text-sm leading-relaxed">
              Welcome to your personal Nepal travel workspace. Manage your itineraries, track expenses, check weather and safety alerts, and personalize your mountain journeys.
            </p>

            {/* AI Search Bar */}
            <form onSubmit={handleHeroSearch} className="mt-4 flex flex-col sm:flex-row gap-2 max-w-xl">
              <div className="relative flex-1">
                <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                <input
                  className="w-full pl-10 pr-4 py-3 rounded-2xl bg-white/95 text-slate-900 text-sm font-medium placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-400"
                  placeholder="Search destinations, trekking trails, or hotels in Nepal..."
                  value={heroQuery}
                  onChange={(e) => setHeroQuery(e.target.value)}
                />
              </div>
              <button type="submit" className="btn-gradient flex items-center justify-center gap-2 whitespace-nowrap text-xs font-bold py-3 px-5">
                <FiSearch size={14} /> AI Search
              </button>
            </form>
          </div>

          {/* Quick Weather & Radar Widget */}
          <div className="shrink-0 bg-white/10 backdrop-blur border border-white/20 p-5 rounded-2xl space-y-3 min-w-[260px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-wider text-amber-300">Live Weather</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/30 text-emerald-200 font-bold">GPS Location</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black text-white">
                {weather?.temperature_c ?? weather?.temperature ?? 22}°C
              </span>
              <div>
                <p className="text-xs font-bold text-white capitalize">{weather?.description || weather?.condition || "Clear Skies"}</p>
                <p className="text-[11px] text-slate-300">{weather?.location || "Nepal Highlands"}</p>
              </div>
            </div>
            <div className="pt-2 border-t border-white/15 flex items-center justify-between text-[11px] text-slate-200">
              <span>Safety Score: <b className="text-emerald-300">{scoreFromAlerts(alerts)}/100</b></span>
              <Link to="/risk-alerts" className="text-amber-300 font-bold hover:underline">View Alerts</Link>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Quick Stats & Engagement Counter Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="card-base p-4 flex items-center gap-3 hover:border-blue-400">
          <div className="p-3 rounded-2xl bg-blue-50 text-blue-600">
            <FiCalendar size={22} />
          </div>
          <div>
            <p className="text-[11px] text-slate-500 font-bold uppercase">Planned Trips</p>
            <p className="text-2xl font-black text-slate-900">{travelPlans.length}</p>
          </div>
        </div>

        <div className="card-base p-4 flex items-center gap-3 hover:border-emerald-400">
          <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-600">
            <FiTag size={22} />
          </div>
          <div>
            <p className="text-[11px] text-slate-500 font-bold uppercase">Active Bookings</p>
            <p className="text-2xl font-black text-slate-900">{activeBookingsCount}</p>
          </div>
        </div>

        <div className="card-base p-4 flex items-center gap-3 hover:border-pink-400">
          <div className="p-3 rounded-2xl bg-pink-50 text-pink-600">
            <FiHeart size={22} />
          </div>
          <div>
            <p className="text-[11px] text-slate-500 font-bold uppercase">Saved Places</p>
            <p className="text-2xl font-black text-slate-900">{favorites.length}</p>
          </div>
        </div>

        <div className="card-base p-4 flex items-center gap-3 hover:border-amber-400">
          <div className="p-3 rounded-2xl bg-amber-50 text-amber-600">
            <FiDollarSign size={22} />
          </div>
          <div>
            <p className="text-[11px] text-slate-500 font-bold uppercase">Spent (NPR)</p>
            <p className="text-2xl font-black text-slate-900">{totalSpentNpr.toLocaleString()}</p>
          </div>
        </div>

        <div className="card-base p-4 flex items-center gap-3 hover:border-purple-400 col-span-2 sm:col-span-1">
          <div className="p-3 rounded-2xl bg-purple-50 text-purple-600">
            <FiShield size={22} />
          </div>
          <div>
            <p className="text-[11px] text-slate-500 font-bold uppercase">Sentinel Contrib</p>
            <p className="text-2xl font-black text-slate-900">{userReports.length} <span className="text-xs font-normal text-slate-500">reports</span></p>
          </div>
        </div>
      </div>

      {/* 4. Phone verification prompt banner */}
      {user?.phone_number && sessionStorage.getItem("phone_verified_this_session") !== "true" && !phoneBannerDismissed && (
        <div className="flex items-center justify-between gap-4 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-3 text-xs">
          <span className="text-amber-800 font-semibold">Verify your phone number to enable SMS risk alerts and emergency SOS dispatch.</span>
          <div className="flex items-center gap-3 shrink-0">
            <Link to="/verify-phone" className="font-bold text-blue-700 hover:underline">Verify now</Link>
            <button onClick={() => setPhoneBannerDismissed(true)} className="text-slate-400 hover:text-slate-600">
              <FiX size={16} />
            </button>
          </div>
        </div>
      )}

      {notices.length > 0 && <VisitorNoticeBanner notices={notices} />}

      {/* 5. Interactive Workspace Tabs Bar */}
      <div className="border-b border-slate-200 overflow-x-auto no-scrollbar pt-2">
        <div className="flex items-center gap-2 min-w-max pb-2">
          {[
            { id: "overview", label: "🌟 Journey Hub & Highlights", icon: FiCompass },
            { id: "itineraries", label: "🗺️ My Trips & AI Replanner", icon: FiCalendar, count: travelPlans.length },
            { id: "bookings", label: "🏨 Bookings & Vouchers", icon: FiTag, count: activeBookingsCount },
            { id: "preferences", label: "⚙️ Travel Preference Profile", icon: FiSliders },
            { id: "feedback", label: "🛡️ Error Reports & Feedback", icon: FiShield, count: userReports.length },
            { id: "community", label: "📸 Community Photo Desk", icon: FiImage },
          ].map((tab) => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-extrabold transition-all ${
                  active
                    ? "bg-[#0B3D91] text-white shadow-md shadow-blue-900/20"
                    : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
                }`}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
                {tab.count != null && tab.count > 0 && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                    active ? "bg-amber-400 text-slate-950" : "bg-slate-200 text-slate-800"
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* TAB 1: OVERVIEW & HIGHLIGHTS */}
      {activeTab === "overview" && (
        <div className="space-y-8">
          {/* Quick Action Bar */}
          <div className="bg-gradient-to-r from-purple-900 via-slate-900 to-slate-950 text-white p-6 rounded-3xl border border-purple-800/40 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-black uppercase tracking-wider">
                Interactive Traveler Services
              </span>
              <h2 className="text-xl font-black mt-1">Ready to Explore or Personalize Your Next Trip?</h2>
              <p className="text-xs text-slate-300">Plan a custom itinerary with AI, rate your past recommendations, or report venue details.</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Link
                to="/trip-planner"
                className="px-4 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs shadow transition-all hover:scale-105 flex items-center gap-1.5"
              >
                <FiPlus size={14} /> Plan New Trip
              </Link>
              <button
                onClick={() => setShowAddExpenseModal(true)}
                className="px-4 py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow transition-all flex items-center gap-1.5"
              >
                <FiDollarSign size={14} /> Log Expense
              </button>
              <button
                onClick={() => setShowFeedbackModal(true)}
                className="px-4 py-2.5 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs shadow transition-all flex items-center gap-1.5"
              >
                <FiStar size={14} /> Rate & Send Feedback
              </button>
              <button
                onClick={() => setShowReportErrorModal(true)}
                className="px-4 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs border border-slate-600 flex items-center gap-1.5"
              >
                <FiAlertTriangle size={14} /> Report Error
              </button>
            </div>
          </div>

          {/* Up Next Upcoming Trip Banner */}
          {travelPlans.length > 0 && (
            <div className="bg-gradient-to-br from-emerald-900 via-slate-900 to-slate-950 text-white p-6 rounded-3xl border border-emerald-700/50 shadow-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="px-3 py-0.5 rounded-full bg-emerald-400 text-slate-950 text-[10px] font-black uppercase">
                    Active Travel Plan
                  </span>
                  <h3 className="text-xl font-black text-white mt-1">
                    {travelPlans[0].title || travelPlans[0].destination_name || "Your Upcoming Nepal Journey"}
                  </h3>
                  <p className="text-xs text-emerald-200 mt-0.5">
                    {travelPlans[0].num_days || 5} Days • Budget NPR {Number(travelPlans[0].estimated_cost_npr || 35000).toLocaleString()} • {travelPlans[0].travel_style || "Nature & Trekking"}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleModifyItinerary("🌦️ Weather / Impact Replan", travelPlans[0])}
                    disabled={modifyingPlan}
                    className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 text-xs font-black shadow flex items-center gap-1.5"
                  >
                    <FiZap size={14} /> {modifyingPlan ? "Replanning..." : "🌦️ Weather Replan"}
                  </button>
                  <Link
                    to="/itinerary"
                    className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold border border-white/20"
                  >
                    View Full Itinerary ➔
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Weather & Budget Cards Snapshot */}
          {showBlock("weather-budget") && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <WeatherCard
                location={weather?.location || "Current Location"}
                temp_c={weather?.temperature_c ?? weather?.temperature}
                condition={weather?.description || weather?.condition || "clear"}
                humidity={weather?.humidity}
                wind_kmh={weather?.wind_kmh}
                loading={!weather}
              />
              <BudgetCard label="Total Budget" amount={budget?.total} />
              <BudgetCard label="Spent" amount={budget?.spent} accent="forest" />
            </div>
          )}

          {/* Latest Alerts */}
          {showBlock("alerts") && alerts.length > 0 && (
            <section>
              <h2 className="section-title">{block("alerts")?.title || "Latest Alerts"}</h2>
              <div className="grid md:grid-cols-2 gap-4">
                {alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))}
              </div>
            </section>
          )}

          {/* Recommended Places */}
          {showBlock("recommendations") && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <FiTrendingUp className="text-emerald-600" />
                <h2 className="section-title">{block("recommendations")?.title || "Recommended For You"}</h2>
              </div>
              {recommendations.length ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {recommendations.map((item) => (
                    <RecommendationCard key={item.id} item={item} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No recommendations yet" subtitle="Explore destinations to receive personalized AI recommendations." />
              )}
            </section>
          )}

          {/* Trending Nepal Destinations */}
          {showBlock("trending") && (
            <section>
              <h2 className="section-title">{block("trending")?.title || "Trending Nepal Destinations"}</h2>
              {destinations.length ? (
                <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
                  {destinations.map((destination) => (
                    <DestinationCard key={destination.id} destination={destination} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No destinations found" subtitle="Check back soon or explore the map." />
              )}
            </section>
          )}

          {/* Favorite Places */}
          {showBlock("favorites") && (
            <section>
              <h2 className="section-title flex items-center gap-2">
                <FiHeart className="text-pink-500" />
                {block("favorites")?.title || "Favorite Places"}
              </h2>
              {favorites.length ? (
                <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
                  {favorites.map((row) => {
                    const dest = unwrapFavoriteDestination(row)
                    if (!dest) return null
                    return <DestinationCard key={row.id || dest.id} destination={dest} isFavorite />
                  })}
                </div>
              ) : (
                <EmptyState title="No saved favorites" subtitle="Bookmark destinations you love and they'll appear here." />
              )}
            </section>
          )}

          {/* Recommended Hotels */}
          {showBlock("hotels") && hotels.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="section-title">{block("hotels")?.title || "Recommended Hotels & Stays"}</h2>
                <Link to="/hotels/search" className="text-xs font-bold text-blue-700 hover:underline">
                  View all hotels ➔
                </Link>
              </div>
              <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-5">
                {hotels.map((hotel) => (
                  <HotelCard key={hotel.id} hotel={hotel} />
                ))}
              </div>
            </section>
          )}

          {/* Culture & Highlights */}
          {showBlock("culture") && <NepalExperienceSection />}
          {showBlock("highlights") && <NepalHighlights bare />}

          {/* Safety Status */}
          {showBlock("safety") && (
            <section>
              <h2 className="section-title">{block("safety")?.title || "Safety & Emergency Radar"}</h2>
              <SafetyOverview
                score={scoreFromAlerts(alerts)}
                weatherStatus={weather?.description || weather?.condition || "Not recorded"}
                earthquakeRisk={alerts.some((a) => /earthquake|seismic/i.test(a.title || a.type || a.alert_type || "")) ? "Alert recorded" : "No recorded alert"}
                hospitalsNearby={nearbySafety?.counts?.hospitals_within_radius != null ? nearbySafety.counts.hospitals_within_radius : "Enable GPS"}
                policeNearby={nearbySafety?.counts?.police_within_radius != null ? nearbySafety.counts.police_within_radius : "Enable GPS"}
              />
            </section>
          )}
        </div>
      )}

      {/* TAB 2: MY TRIPS & AI REPLANNER */}
      {activeTab === "itineraries" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="section-title flex items-center gap-2">
                  <FiCalendar className="text-blue-700" /> My Saved Travel Plans & AI Replanner
                </h2>
                <p className="text-xs text-slate-500">
                  Read, review, and modify your custom Nepal itineraries with 1-click AI actions.
                </p>
              </div>

              <Link
                to="/trip-planner"
                className="px-5 py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow flex items-center gap-1.5 shrink-0"
              >
                <FiPlus size={16} /> Create New Itinerary
              </Link>
            </div>

            {/* AI Modification Toolbar */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-900 to-slate-900 text-white space-y-3">
              <p className="text-xs font-bold text-purple-300 flex items-center gap-1.5">
                <FiZap /> 1-Click AI Modification Studio (Applies directly to selected itinerary):
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {[
                  { prompt: "Make it cheaper", label: "💰 Make It Cheaper" },
                  { prompt: "Make it luxurious", label: "✨ Make It Luxurious" },
                  { prompt: "Add culture", label: "🎨 Add Cultural Heritage" },
                  { prompt: "Add hidden nature", label: "🌿 Add Nature & Views" },
                  { prompt: "Slow down pace", label: "🧘 Slow Down Pace" },
                  { prompt: "🌦️ Weather / Impact Replan", label: "🌦️ Weather Impact Replan" },
                ].map((act, i) => (
                  <button
                    key={i}
                    onClick={() => handleModifyItinerary(act.prompt)}
                    disabled={modifyingPlan}
                    className="px-3.5 py-2 rounded-xl bg-white/10 hover:bg-amber-400 hover:text-slate-950 text-xs font-bold border border-white/20 transition-all disabled:opacity-50"
                  >
                    {act.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Saved Plans List */}
            {travelPlans.length === 0 ? (
              <EmptyState
                title="No saved travel plans yet"
                subtitle="Use our AI Trip Planner to build and save custom Nepal itineraries."
              />
            ) : (
              <div className="space-y-4">
                {travelPlans.map((plan) => (
                  <div
                    key={plan.id}
                    className={`p-6 rounded-3xl border transition-all ${
                      selectedPlanForModify?.id === plan.id
                        ? "bg-blue-50/50 border-blue-400 shadow-md"
                        : "bg-white border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase">
                            {plan.travel_style || "Trekking"}
                          </span>
                          <span className="text-xs text-slate-500 font-mono">
                            ID #{plan.id}
                          </span>
                        </div>
                        <h3 className="text-lg font-black text-slate-900 mt-1">
                          {plan.title || plan.destination_name || "Custom Nepal Trip Plan"}
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {plan.num_days || 5} Days • Estimated Budget: NPR {Number(plan.estimated_cost_npr || 40000).toLocaleString()}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setSelectedPlanForModify(plan)}
                          className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-all ${
                            selectedPlanForModify?.id === plan.id
                              ? "bg-blue-700 text-white border-blue-700"
                              : "bg-slate-100 text-slate-700 hover:bg-slate-200 border-slate-200"
                          }`}
                        >
                          {selectedPlanForModify?.id === plan.id ? "✓ Selected for AI" : "Select for AI"}
                        </button>

                        <Link
                          to="/itinerary"
                          className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800"
                        >
                          Full Details ➔
                        </Link>
                      </div>
                    </div>

                    {/* Day-by-day stops preview if available */}
                    {plan.stops && plan.stops.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <p className="text-xs font-bold text-slate-700 mb-2">Day-by-Day Stops:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                          {plan.stops.slice(0, 6).map((s, idx) => (
                            <div key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs">
                              <span className="font-bold text-blue-700">Day {s.day_number || idx + 1}:</span>{" "}
                              <span className="text-slate-800 font-medium">{s.destination_name || s.name || "Stop"}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: BOOKINGS & RESERVATIONS */}
      {activeTab === "bookings" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="section-title flex items-center gap-2">
                  <FiTag className="text-emerald-600" /> My Hotel & Package Reservations
                </h2>
                <p className="text-xs text-slate-500">
                  View and manage your confirmed stays and tour bookings across Nepal.
                </p>
              </div>

              <Link
                to="/hotels/search"
                className="px-5 py-2.5 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow flex items-center gap-1.5"
              >
                <FiPlus size={16} /> Book Hotel Room
              </Link>
            </div>

            {userBookings.length === 0 ? (
              <EmptyState
                title="No active bookings found"
                subtitle="Search and reserve stays in Pokhara, Kathmandu, Chitwan, or Everest!"
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userBookings.map((b) => (
                  <div key={b.id} className="p-5 rounded-2xl border border-slate-200 bg-white shadow-sm space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                          b.status === "confirmed"
                            ? "bg-emerald-100 text-emerald-800"
                            : b.status === "pending"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-slate-100 text-slate-600"
                        }`}>
                          {b.status || "Confirmed"}
                        </span>
                        <h4 className="font-extrabold text-base text-slate-900 mt-1">
                          {b.hotel_name || b.listing_title || "Hotel Reservation"}
                        </h4>
                        <p className="text-xs text-slate-500">{b.guest_name || displayName(user)}</p>
                      </div>

                      <span className="text-lg font-black text-emerald-700">
                        NPR {Number(b.total_cost || b.total_price || 0).toLocaleString()}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 text-xs text-slate-600 space-y-1">
                      <p><b>Check-in:</b> {b.check_in_date || b.start_date || "Not recorded"}</p>
                      <p><b>Check-out:</b> {b.check_out_date || b.end_date || "Not recorded"}</p>
                      <p><b>Guests / Rooms:</b> {b.num_guests || 1} Guests • {b.num_rooms || 1} Room(s)</p>
                    </div>

                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="font-mono text-slate-400">Ref: #{b.id}</span>
                      <button
                        onClick={() => showToast("Booking voucher emailed to your account!", "info")}
                        className="text-blue-700 font-bold hover:underline"
                      >
                        Download Voucher ➔
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: PREFERENCES & TRAVEL PROFILE */}
      {activeTab === "preferences" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-6">
            <div>
              <h2 className="section-title flex items-center gap-2">
                <FiSliders className="text-purple-600" /> Progressive Travel Preference Profile
              </h2>
              <p className="text-xs text-slate-500">
                Configure your travel style, budget ceilings, dietary, and accessibility requirements. The AI recommendation engine uses these settings to personalize your travel picks.
              </p>
            </div>

            <form onSubmit={handleSavePreferences} className="space-y-5 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Primary Travel Style</label>
                  <select
                    value={preferencesForm.travel_style}
                    onChange={(e) => setPreferencesForm({ ...preferencesForm, travel_style: e.target.value })}
                    className="input-field text-xs"
                  >
                    <option value="nature">🏔️ Nature & Hiking</option>
                    <option value="culture">🎨 Cultural & Pilgrimage</option>
                    <option value="adventure">🪂 High Adventure & Wildlife</option>
                    <option value="luxury">✨ Luxury & Spa Relaxation</option>
                    <option value="backpacker">🎒 Backpacker & Budget</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Travel Pace</label>
                  <select
                    value={preferencesForm.pace}
                    onChange={(e) => setPreferencesForm({ ...preferencesForm, pace: e.target.value })}
                    className="input-field text-xs"
                  >
                    <option value="relaxed">🧘 Relaxed & Leisurely</option>
                    <option value="moderate">⚖️ Balanced & Moderate</option>
                    <option value="fast">⚡ Fast-Paced & Intensive</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Preferred Transit Mode</label>
                  <select
                    value={preferencesForm.preferred_transport}
                    onChange={(e) => setPreferencesForm({ ...preferencesForm, preferred_transport: e.target.value })}
                    className="input-field text-xs"
                  >
                    <option value="bus">🚌 Tourist Bus / Coach</option>
                    <option value="jeep">🚙 Private SUV / 4WD Jeep</option>
                    <option value="flight">✈️ Domestic Flight</option>
                    <option value="trekking">🥾 Trekking Feeder Trails</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Group Composition</label>
                  <select
                    value={preferencesForm.group_type}
                    onChange={(e) => setPreferencesForm({ ...preferencesForm, group_type: e.target.value })}
                    className="input-field text-xs"
                  >
                    <option value="solo">👤 Solo Traveler</option>
                    <option value="couple">👩‍❤️‍👨 Couple Journey</option>
                    <option value="family">👨‍👩‍👧‍👦 Family with Children</option>
                    <option value="friends">👯 Friends / Group Trek</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Target Budget Ceiling (NPR)</label>
                  <input
                    type="number"
                    step={5000}
                    value={preferencesForm.max_budget_npr}
                    onChange={(e) => setPreferencesForm({ ...preferencesForm, max_budget_npr: Number(e.target.value) })}
                    className="input-field text-xs"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  type="submit"
                  disabled={savingPrefs}
                  className="px-6 py-2.5 rounded-2xl bg-[#0B3D91] hover:bg-blue-900 text-white font-extrabold text-xs shadow-lg transition-all"
                >
                  {savingPrefs ? "Saving..." : "Save Preferences Profile"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TAB 5: ERROR REPORTS & FEEDBACK QUEUE */}
      {activeTab === "feedback" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="section-title flex items-center gap-2">
                  <FiShield className="text-rose-600" /> Data Quality Sentinel & Error Reports History
                </h2>
                <p className="text-xs text-slate-500">
                  Track user-submitted coordinate corrections, price updates, and feedback sent to our moderation team.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowReportErrorModal(true)}
                  className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 text-xs font-black shadow flex items-center gap-1.5"
                >
                  <FiAlertTriangle size={14} /> Report Data Error
                </button>
                <button
                  onClick={() => setShowFeedbackModal(true)}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow flex items-center gap-1.5"
                >
                  <FiStar size={14} /> Send Rating
                </button>
              </div>
            </div>

            {userReports.length === 0 ? (
              <EmptyState
                title="No error reports submitted yet"
                subtitle="Notice wrong coordinates, outdated ticket prices, or missing amenities? Report it to help fellow travelers!"
              />
            ) : (
              <div className="space-y-3">
                {userReports.map((rep) => (
                  <div key={rep.id} className="p-4 rounded-2xl border border-slate-200 bg-slate-50 flex items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                          rep.status === "fixed"
                            ? "bg-emerald-100 text-emerald-800"
                            : rep.status === "new"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-slate-200 text-slate-700"
                        }`}>
                          {rep.status || "Pending Verification"}
                        </span>
                        <span className="text-xs font-bold text-slate-800">
                          {rep.report_type?.replace("_", " ").toUpperCase() || "General Data Report"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600">{rep.description || rep.suggested_value || "Reported venue discrepancy."}</p>
                    </div>

                    <span className="text-[10px] text-slate-400 font-mono shrink-0">
                      Report #{rep.id}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 6: COMMUNITY PHOTO DESK */}
      {activeTab === "community" && showBlock("community-photos") && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 p-6 rounded-3xl shadow-sm space-y-6">
            <div>
              <h2 className="section-title flex items-center gap-2">
                <FiImage className="text-pink-600" /> Community Photo Contribution Desk
              </h2>
              <p className="text-slate-500 text-xs mt-1">
                Help fellow travelers by uploading your authentic destination photos. Popular photos are promoted to official cover photos!
              </p>
            </div>

            {/* Search Destination */}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                runSearch(query)
              }}
              className="flex flex-col md:flex-row gap-3"
            >
              <input
                className="input-field flex-1 text-xs"
                placeholder="Find a destination to upload a photo for (e.g. Bandipur, Pokhara)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button type="submit" className="btn-gradient flex items-center justify-center gap-2 text-xs font-bold px-6">
                <FiSearch /> Search
              </button>
            </form>

            {results.length > 0 && (
              <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-4 pt-2">
                {results.map((place) => (
                  <div
                    key={place.id}
                    onClick={() => selectDestination(place)}
                    className="card-base p-4 cursor-pointer hover:border-emerald-500"
                  >
                    {place.cover_image_url && (
                      <img
                        src={place.cover_image_url}
                        alt={place.name}
                        className="w-full h-32 object-cover rounded-xl mb-3"
                      />
                    )}
                    <h3 className="font-bold text-sm text-slate-900">{place.name}</h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                      <FiMapPin size={12} /> {place.city || place.district || "Nepal"}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Selected Destination Upload Form */}
            {selected && (
              <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-5">
                <div>
                  <h3 className="text-lg font-black text-slate-900">Upload Photo for {selected.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Upload high-quality, authentic photos taken during your visit.
                  </p>
                </div>

                <form onSubmit={handleUpload} className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Select Photo File *</label>
                    <input
                      type="file"
                      accept="image/*"
                      required
                      className="w-full border rounded-xl px-3 py-2 text-xs bg-white"
                      onChange={(e) => setFile(e.target.files[0])}
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Caption / Description</label>
                    <input
                      type="text"
                      placeholder="e.g. Scenic sunrise over mountain peaks"
                      className="input-field text-xs"
                      value={caption}
                      onChange={(e) => setCaption(e.target.value)}
                    />
                  </div>

                  <button type="submit" className="btn-gradient flex items-center gap-2 text-xs font-bold px-6 py-2.5">
                    <FiUpload /> Upload Photo
                  </button>
                </form>

                {status && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-800">
                    <p>{status}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      <UserFeedbackModal isOpen={showFeedbackModal} onClose={() => setShowFeedbackModal(false)} />
      <ReportErrorModal
        isOpen={showReportErrorModal}
        onClose={() => setShowReportErrorModal(false)}
        destination={reportTargetDest}
      />
      <AddExpenseModal
        isOpen={showAddExpenseModal}
        onClose={() => setShowAddExpenseModal(false)}
        onSuccess={loadDashboardData}
      />
    </div>
  )
}

export default Dashboard
