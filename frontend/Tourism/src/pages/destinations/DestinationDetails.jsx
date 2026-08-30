import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiStar, FiMapPin, FiHeart, FiPhoneCall, FiDollarSign,
  FiShield, FiHome, FiCoffee, FiShoppingBag, FiGlobe, FiClock,
  FiNavigation, FiLayers, FiMaximize2, FiChevronLeft, FiChevronRight,
  FiX, FiCalendar, FiActivity, FiAlertTriangle, FiCheckCircle,
  FiTruck, FiCompass, FiExternalLink, FiInfo, FiBookOpen, FiShare2, FiSun
} from "react-icons/fi"

import destinationApi from "../../api/destinationApi"
import emergencyApi from "../../api/emergencyApi"
import budgetApi from "../../api/budgetApi"
import userApi from "../../api/userApi"
import { formatCoords, hasValidCoords, placeLocationLabel } from "../../utils/placeUtils"
import { photoApi } from "../../services/api"
import usePublicConfig from "../../hooks/usePublicConfig"
import { CMSExtras } from "../../components/cms/CMSBlock"
import { getDestinationImageUrl } from "../../utils/imageUtils"

import MapView from "../../components/map/MapView"
import WeatherCard from "../../components/cards/WeatherCard"
import HotelCard from "../../components/cards/HotelCard"
import MapillaryImages from "../../components/map/MapillaryImages"
import Breadcrumbs from "../../components/common/Breadcrumbs"
import Loader from "../../components/common/Loader"
import useGeolocation from "../../hooks/useGeolocation"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import ReportErrorModal from "../../components/common/ReportErrorModal"
import { RISK_LEVELS } from "../../utils/constants"
import { formatCurrencyUSD, formatCurrencyNPR } from "../../utils/formatters"
import { FadeIn, HoverCard } from "../../components/common/MotionSystem"
import CircularGallery from "../../components/ui/CircularGallery"
import VisitorNoticeBanner from "../../components/common/VisitorNoticeBanner"

export default function DestinationDetails() {
  const { slug } = useParams()
  const navigate = useNavigate()

  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const { extras } = usePublicConfig().pageCMS("destination-detail", ["hero", "about", "gallery", "video", "map"])
  const [videoFile, setVideoFile] = useState(null)
  const [videoBusy, setVideoBusy] = useState(false)

  const [destination, setDestination] = useState(null)
  const [budget, setBudget] = useState(null)
  const [essentials, setEssentials] = useState(null)
  const [emergency, setEmergency] = useState(null)

  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteRecordId, setFavoriteRecordId] = useState(null)

  // Gallery & Image Category Filter
  const [activeImageIdx, setActiveImageIdx] = useState(0)
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [selectedImgCategory, setSelectedImgCategory] = useState("all")
  const [showOfflineKit, setShowOfflineKit] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)

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
      emergencyApi.forDestination(slug, { radius_km: 80, limit: 6 }),
      budgetApi.estimate({ destination: slug, travelers: 1, days: 3 }),
    ]).then(([destRes, essentialsRes, emergencyRes, budgetRes]) => {
      if (destRes.status === "fulfilled") {
        setDestination(destRes.value.data)
      }
      if (essentialsRes?.status === "fulfilled") {
        setEssentials(essentialsRes.value.data)
      }
      if (emergencyRes?.status === "fulfilled") {
        setEmergency(emergencyRes.value.data)
      }
      if (budgetRes.status === "fulfilled") {
        setBudget({
          total: budgetRes.value.data.total_budget_usd ?? budgetRes.value.data.total ?? null,
        })
      }
    }).finally(() => setLoading(false))
  }, [slug, position])

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
        if (favoriteRecordId) await userApi.removeFavorite(favoriteRecordId)
        setIsFavorite(false)
        setFavoriteRecordId(null)
        showToast("Removed from favorites", "info")
      } else {
        const { data } = await userApi.addFavorite(destination.id)
        setIsFavorite(true)
        setFavoriteRecordId(data.id)
        showToast("Saved to favorites ❤️", "success")
      }
    } catch {
      showToast("Could not update favorite", "error")
    }
  }

  if (loading) return <Loader fullScreen />

  // Inject JSON-LD structured data for SEO
  useEffect(() => {
    if (!destination) return
    const jsonLd = {
      "@context": "https://schema.org",
      "@type": "TouristAttraction",
      "name": destination.name,
      "description": destination.description || destination.short_description || "",
      "url": window.location.href,
      "geo": destination.latitude && destination.longitude ? {
        "@type": "GeoCoordinates",
        "latitude": destination.latitude,
        "longitude": destination.longitude,
      } : undefined,
      "address": {
        "@type": "PostalAddress",
        "addressLocality": destination.city || destination.district || "Nepal",
        "addressRegion": destination.province || "",
        "addressCountry": "NP",
      },
      "aggregateRating": destination.average_rating ? {
        "@type": "AggregateRating",
        "ratingValue": destination.average_rating,
        "reviewCount": destination.ratings_count || 1,
      } : undefined,
    }

    const script = document.createElement("script")
    script.type = "application/ld+json"
    script.id = "destination-jsonld"
    script.innerHTML = JSON.stringify(jsonLd)
    document.head.appendChild(script)

    return () => {
      const existing = document.getElementById("destination-jsonld")
      if (existing) existing.remove()
    }
  }, [destination])

  // Compile all images with metadata. The hero prefers the real-photo
  // resolver (category-aware), so SVG-postcard covers never show on the page.
  const allImages = []
  const heroUrl = getDestinationImageUrl(destination)
  if (heroUrl) {
    allImages.push({
      url: heroUrl,
      caption: destination.name,
      category: "hero",
      photographer: destination.gallery?.[0]?.photographer || "Not recorded",
      platform: destination.gallery?.[0]?.source_platform || destination.gallery?.[0]?.source || "Recorded destination media",
      license: destination.gallery?.[0]?.license_type || "Not recorded",
    })
  }

  if (destination.gallery && Array.isArray(destination.gallery)) {
    destination.gallery.forEach((g, idx) => {
      const url = g.image || g.external_url || g.display_url
      if (url && !allImages.some(img => img.url === url)) {
        allImages.push({
          url,
          caption: g.caption || `${destination.name} - View ${idx + 1}`,
          category: g.image_category || "recorded",
          photographer: g.photographer || g.attribution || "Not recorded",
          platform: g.source_platform || g.source || "Not recorded",
          license: g.license_type || "Not recorded",
        })
      }
    })
  }

  // Never substitute another destination's media. An explicit unavailable
  // state is rendered until an admin verifies destination-linked media.
  const verifiedImageCount = allImages.length
  if (!allImages.length) {
    allImages.push({
      url: null,
      caption: "Image unavailable",
      category: "unavailable",
      photographer: "No verified media",
      platform: "Destination media review required",
      license: "Not applicable",
    })
  }

  const activeImage = allImages[activeImageIdx] || allImages[0]
  const activeAlert = essentials?.active_alert
  const riskAnalysis = destination.risk_analysis
  const budgetEst = destination.budget_estimation
  const riskCategory = (riskAnalysis?.risk_category || activeAlert?.severity || "").toUpperCase()
  const level = RISK_LEVELS[riskCategory] || { label: "Not recorded", color: "bg-gray-100 text-gray-700" }

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      <Breadcrumbs items={[
        { label: "Destinations", to: "/destinations" },
        { label: destination.name, to: `/destinations/${destination.slug}` }
      ]} />

      {/* Top Header & Destination Identification */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-primary-800">
            <span className="bg-primary-50 px-3 py-1 rounded-full">{destination.category_name || "Destination"}</span>
            <span>•</span>
            <span className="text-gray-600">{placeLocationLabel({ municipality: destination.municipality, district: destination.district, province: destination.province })}</span>
            {destination.altitude && <span>• 🏔️ {destination.altitude}</span>}
          </div>

          <h1 className="text-3xl sm:text-5xl font-black text-gray-900 mt-2 tracking-tight">
            {destination.name}
          </h1>

          {destination.aliases && (
            <p className="text-xs text-primary-700 font-semibold mt-1">
              Also known as: <span className="text-gray-700 italic">{destination.aliases}</span>
            </p>
          )}

          <p className="text-gray-500 text-sm flex items-center gap-1.5 mt-1">
            <FiMapPin className="text-primary-600" />
            {placeLocationLabel(destination)}
          </p>
          {formatCoords(destination.latitude, destination.longitude) && (
            <p className="text-[11px] font-mono text-emerald-800 mt-1">{formatCoords(destination.latitude, destination.longitude)}</p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <Link
            to={`/compare?dest=${encodeURIComponent(destination.slug)}`}
            className="px-4 py-3 rounded-2xl bg-white hover:bg-primary-50 text-primary-900 border border-primary-200 font-bold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm transition-all"
          >
            ⚖️ Compare
          </Link>
          <button
            onClick={() => setShowReportModal(true)}
            className="px-4 py-3 rounded-2xl bg-white hover:bg-rose-50 text-rose-800 border border-rose-200 font-bold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm transition-all"
            title="Report wrong coordinates, routes, or outdated information"
          >
            <FiAlertTriangle size={15} className="text-rose-600" /> Report Issue
          </button>
          <button
            onClick={() => setShowOfflineKit(true)}
            className="px-4 py-3 rounded-2xl bg-white hover:bg-emerald-50 text-emerald-900 border border-emerald-200 font-bold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm transition-all"
          >
            📦 Offline Kit
          </button>
          <button
            onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)}
            className="px-5 py-3 rounded-2xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs sm:text-sm flex items-center gap-2 shadow-xl shadow-amber-400/25 transition-all hover:scale-105"
          >
            <FiNavigation size={16} /> GTA Route
          </button>
          <button
            onClick={toggleFavorite}
            className={`p-3 rounded-2xl border transition-all ${
              isFavorite
                ? "bg-rose-50 border-rose-300 text-rose-600 shadow-md"
                : "bg-white border-gray-200 text-gray-500 hover:border-rose-300"
            }`}
          >
            <FiHeart size={18} className={isFavorite ? "fill-rose-500 text-rose-500" : ""} />
          </button>
        </div>
      </div>

      {destination.notices?.length > 0 && <VisitorNoticeBanner notices={destination.notices} />}

      {/* Key Transit & Visiting Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
          <p className="text-[10px] font-black uppercase text-purple-700 flex items-center gap-1"><FiMapPin /> Nearest Major City</p>
          <p className="font-bold text-slate-900 mt-1">{destination.nearest_major_city || "Not recorded"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
          <p className="text-[10px] font-black uppercase text-purple-700 flex items-center gap-1"><FiTruck /> Nearest Airport</p>
          <p className="font-bold text-slate-900 mt-1">{destination.nearest_airport_name || "Not recorded"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
          <p className="text-[10px] font-black uppercase text-purple-700 flex items-center gap-1"><FiClock /> Recommended Stay</p>
          <p className="font-bold text-slate-900 mt-1">{destination.recommended_days ? `${destination.recommended_days} days` : "Not recorded"}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
          <p className="text-[10px] font-black uppercase text-purple-700 flex items-center gap-1"><FiSun /> Best Visiting Season</p>
          <p className="font-bold text-slate-900 mt-1">{destination.best_time_to_visit || "Not recorded"}</p>
        </div>
      </div>

      {/* CIRCULAR 3D PHOTO GALLERY + copyright pill */}
      <div className="space-y-4">
        <CircularGallery
          title={destination.name}
          images={allImages.map((img) => ({ url: img.url, alt: img.caption, caption: img.caption }))}
          autoRotate
          className="h-[460px] sm:h-[540px]"
        />
        <div className="flex items-center justify-between text-[11px] text-stone-500 px-1 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Lead photo: <b>{activeImage.photographer}</b>
            </span>
            <span className="text-stone-300">·</span>
            <span>{activeImage.platform}</span>
            <span className="text-stone-300">·</span>
            <span>{activeImage.license}</span>
          </div>
          <button
            onClick={() => verifiedImageCount && setLightboxOpen(true)}
            disabled={!verifiedImageCount}
            className="px-3 py-1 rounded-full border border-stone-200 hover:bg-stone-50 disabled:opacity-50 inline-flex items-center gap-1 text-xs"
          >
            {verifiedImageCount ? `Fullscreen lightbox (${verifiedImageCount} photos)` : "Image unavailable"}
          </button>
        </div>

      </div>

      <div className="card-base p-5 rounded-3xl border border-emerald-100 space-y-3">
        <h3 className="font-black text-gray-900">Community videos (25 MB max)</h3>
        <p className="text-xs text-gray-500">Logged-in travellers can submit a short clip of this place. Admin reviews it before it is public.</p>
        {(destination.videos || []).length > 0 && (
          <div className="grid sm:grid-cols-2 gap-3">
            {destination.videos.map((clip) => (
              <div key={clip.id} className="rounded-xl bg-slate-50 p-3 text-xs">
                <p className="font-bold">{clip.title || clip.caption || "Traveller video"} {clip.verification_status === "pending" && <span className="text-amber-700">pending review</span>}</p>
                {clip.display_url && <video src={clip.display_url} controls className="mt-2 w-full rounded-lg max-h-48" />}
              </div>
            ))}
          </div>
        )}
        {isAuthenticated && (
          <form className="flex flex-col sm:flex-row gap-2" onSubmit={async (e) => {
            e.preventDefault()
            if (!videoFile) return
            if (videoFile.size > 25 * 1024 * 1024) return showToast("Videos must be 25 MB or smaller.", "error")
            const form = new FormData()
            form.append("video_file", videoFile)
            form.append("title", videoFile.name)
            setVideoBusy(true)
            try {
              await photoApi.uploadVideo(destination.slug, form)
              showToast("Video submitted for review.", "success")
              setVideoFile(null)
              const { data } = await destinationApi.getById(destination.slug)
              setDestination(data)
            } catch (error) {
              showToast(error.response?.data?.detail || "Video upload failed.", "error")
            } finally { setVideoBusy(false) }
          }}>
            <input type="file" accept="video/*" onChange={(e) => setVideoFile(e.target.files?.[0] || null)} className="text-xs" />
            <button type="submit" disabled={!videoFile || videoBusy} className="rounded-xl bg-emerald-700 px-4 py-2 text-xs font-bold text-white disabled:opacity-40">{videoBusy ? "Uploading…" : "Upload video"}</button>
          </form>
        )}
      </div>

      {/* Quick Geographic Distances & Transit Metrics Box */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-3xl bg-gradient-to-r from-primary-800 via-primary-700 to-secondary-700 text-white shadow-xl">
        <div>
          <span className="text-[10px] uppercase font-bold text-primary-100">From Kathmandu</span>
          <p className="text-xl font-black mt-0.5">{destination.distance_from_kathmandu_km != null ? `${destination.distance_from_kathmandu_km} km` : "Not recorded"}</p>
          <span className="text-[11px] text-amber-300 font-semibold">{destination.approx_travel_time || "Travel time not recorded"}</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-primary-100">Nearest Major City</span>
          <p className="text-xl font-black mt-0.5">{destination.nearest_major_city || "Not recorded"}</p>
          <span className="text-[11px] text-primary-100 font-medium">{destination.distance_from_nearest_city_km != null ? `${destination.distance_from_nearest_city_km} km away` : "Distance not recorded"}</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-primary-100">Nearest Airport</span>
          <p className="text-xl font-black mt-0.5 truncate">{destination.nearest_airport_name?.split("(")[0] || "Not recorded"}</p>
          <span className="text-[11px] text-primary-100 font-medium">{destination.distance_from_nearest_airport_km != null ? `${destination.distance_from_nearest_airport_km} km` : "Distance not recorded"}</span>
        </div>
        <div>
          <span className="text-[10px] uppercase font-bold text-primary-100">Recommended Stay</span>
          <p className="text-xl font-black mt-0.5">{destination.recommended_days ? `${destination.recommended_days} Days` : "Not recorded"}</p>
          <span className="text-[11px] text-emerald-300 font-bold">{destination.best_time_to_visit || "Season not recorded"}</span>
        </div>
      </div>

      {/* Main Grid: Content & Strategic Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-8">
          {/* Section 1: About & Introduction */}
          <div className="card-base p-6 sm:p-8 space-y-4 shadow-xl border border-primary-100 rounded-3xl bg-white">
            <h2 className="text-2xl font-black text-gray-900 flex items-center gap-2">
              <FiCompass className="text-primary-700" /> About {destination.name}
            </h2>
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
              {destination.description || "Not recorded — we will update soon"}
            </p>

            {destination.tourism_importance && (
              <div className="p-4 rounded-2xl bg-primary-50/80 border border-primary-100 text-xs text-stone-900 font-medium leading-relaxed">
                🌟 <b>Tourism Importance:</b> {destination.tourism_importance}
              </div>
            )}
          </div>

          {/* Section 2: Historical, Cultural & Religious Background */}
          {(destination.history || destination.cultural_significance || destination.religious_significance) && (
            <div className="card-base p-6 sm:p-8 space-y-5 shadow-xl border border-primary-100 rounded-3xl bg-white">
              <h2 className="text-2xl font-black text-gray-900 flex items-center gap-2">
                🏛️ Cultural, Religious & Historical Heritage
              </h2>

              {destination.history && (
                <div className="space-y-1.5">
                  <h4 className="font-bold text-sm text-primary-900">Historical Origins & Heritage:</h4>
                  <p className="text-gray-700 text-xs sm:text-sm leading-relaxed whitespace-pre-line">
                    {destination.history}
                  </p>
                </div>
              )}

              {destination.cultural_significance && (
                <div className="space-y-1.5 pt-2 border-t">
                  <h4 className="font-bold text-sm text-primary-900">Cultural Customs & Traditions:</h4>
                  <p className="text-gray-700 text-xs sm:text-sm leading-relaxed">
                    {destination.cultural_significance}
                  </p>
                </div>
              )}

              {destination.religious_significance && (
                <div className="space-y-1.5 pt-2 border-t">
                  <h4 className="font-bold text-sm text-primary-900">Religious Significance & Sacred Lore:</h4>
                  <p className="text-gray-700 text-xs sm:text-sm leading-relaxed">
                    {destination.religious_significance}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Section 3: Things To Do & Recommended Activities */}
          <div className="card-base p-6 sm:p-8 space-y-4 shadow-xl border border-primary-100 rounded-3xl bg-white">
            <h2 className="text-2xl font-black text-gray-900 flex items-center gap-2">
              <FiActivity className="text-primary-700" /> Things To Do & Experiences
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {(destination.activities?.length > 0 ? destination.activities : []).map((act, i) => (
                <div key={i} className="p-4 rounded-2xl bg-primary-50/60 border border-primary-100 space-y-1.5 shadow-sm">
                  <div className="flex justify-between items-center">
                    <h4 className="font-bold text-xs sm:text-sm text-gray-900">{act.name}</h4>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-secondary-200 text-primary-900">
                      {act.difficulty_level || "Not recorded"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed">{act.description}</p>
                  <p className="text-[11px] text-primary-700 font-bold">⏱️ Duration: {act.estimated_duration || "Duration not recorded"}</p>
                </div>
              ))}
              {!(destination.activities?.length) && (
                <p className="text-sm text-slate-600 col-span-2">No recorded activities for this place yet. An administrator can add them from Destination Features.</p>
              )}
            </div>
          </div>

          {/* Section 4: Available Routes & Transportation Options */}
          <div className="card-base p-6 sm:p-8 space-y-4 shadow-xl border border-primary-100 rounded-3xl bg-white">
            <h2 className="text-2xl font-black text-gray-900 flex items-center gap-2">
              <FiTruck className="text-primary-700" /> Available Routes & Transportation
            </h2>

            <div className="space-y-3">
              {destination.transit_routes?.length > 0 ? destination.transit_routes.map((rt) => (
                <div key={rt.id} className="p-4 rounded-2xl bg-gray-50 border border-gray-200 space-y-2 text-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <h4 className="font-extrabold text-sm text-gray-900 flex items-center gap-1.5">
                      <FiNavigation className="text-primary-600" /> {rt.origin} ➔ {destination.name}
                    </h4>
                    <span className="text-emerald-700 font-black">
                      {rt.estimated_fare_npr != null ? `Est. Fare: NPR ${rt.estimated_fare_npr}` : "Fare unavailable"}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-gray-600">
                    <p>🚗 <b>Transit:</b> {rt.transport_mode || "Unavailable"}</p>
                    <p>⏱️ <b>Duration:</b> {rt.approx_duration || "Unavailable"}</p>
                    <p>📏 <b>Distance:</b> {rt.distance_km != null ? `${rt.distance_km} km` : "Unavailable"}</p>
                    <p>🛣️ <b>Condition:</b> {rt.road_condition || "Not recently verified"}</p>
                  </div>
                  {rt.key_stops && <p className="text-[11px] text-gray-500 pt-1 border-t">📍 <b>Key Stops:</b> {rt.key_stops}</p>}
                  <p className="text-[10px] text-gray-400">Source: {rt.route_source || "Database route record"}</p>
                </div>
              )) : (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
                  No verified destination-specific transit record is available. Use the GraphML navigation engine to calculate an approximate route from your current location.
                  <button onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)} className="block mt-3 rounded-xl bg-primary-700 px-4 py-2 text-xs font-bold text-white">
                    Calculate GraphML Route
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Section 5: Food, Cuisine & Safety Tips */}
          {(destination.food_cuisine_info || destination.travel_safety_tips) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {destination.food_cuisine_info && (
                <div className="card-base p-6 rounded-3xl border border-primary-100 shadow-lg bg-gradient-to-br from-white to-amber-50/30 space-y-2">
                  <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                    <FiCoffee className="text-amber-600" /> Food & Local Cuisine
                  </h3>
                  <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                    {destination.food_cuisine_info}
                  </p>
                </div>
              )}

              {destination.travel_safety_tips && (
                <div className="card-base p-6 rounded-3xl border border-primary-100 shadow-lg bg-gradient-to-br from-white to-rose-50/30 space-y-2">
                  <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                    <FiShield className="text-rose-600" /> Practical Travel & Safety Tips
                  </h3>
                  <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                    {destination.travel_safety_tips}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Section 6: Interactive Map & Street-Level Imagery */}
          <div className="card-base p-6 shadow-xl border border-primary-100 rounded-3xl space-y-4 bg-white">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                <FiMapPin className="text-primary-600" /> Interactive Location & Satellite Map
              </h3>
              <button
                onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)}
                className="text-xs font-bold text-primary-700 hover:text-primary-900 flex items-center gap-1"
              >
                <FiNavigation /> Open Tactical GTA Navigation ➔
              </button>
            </div>
            {hasValidCoords(destination.latitude, destination.longitude) ? (
            <div className="rounded-2xl overflow-hidden border border-gray-200">
              <MapView
                center={{ lat: Number(destination.latitude), lng: Number(destination.longitude) }}
                destination={{ lat: Number(destination.latitude), lng: Number(destination.longitude), name: destination.name }}
                height="400px"
              />
            </div>
            ) : (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                This record has no stored latitude/longitude, so a map pin cannot be shown honestly.
              </div>
            )}

            {/* Street-level Mapillary imagery (Google-Street-View style) */}
            {hasValidCoords(destination.latitude, destination.longitude) && (
              <div className="mt-3 rounded-2xl border border-gray-200 bg-white p-4">
                <MapillaryImages
                  latitude={Number(destination.latitude)}
                  longitude={Number(destination.longitude)}
                  radiusM={800}
                  limit={6}
                />
              </div>
            )}
          </div>

          {destination.marketplace_listings?.length > 0 && (
            <div className="card-base p-6 sm:p-8 space-y-4 shadow-xl border border-primary-100 rounded-3xl bg-white">
              <h2 className="text-2xl font-black text-gray-900">Packages & partner offers</h2>
              <p className="text-sm text-gray-600">Published by the admin desk and approved hotels or operators. Add them to a trip — we never collect card numbers here.</p>
              <div className="grid sm:grid-cols-2 gap-3">
                {destination.marketplace_listings.map((offer) => (
                  <Link key={offer.id} to={`/packages/${offer.slug}`} className="rounded-2xl border border-emerald-100 p-4 hover:bg-emerald-50">
                    <p className="text-[10px] font-black uppercase text-emerald-800">{offer.kind}</p>
                    <p className="font-bold text-slate-900">{offer.title}</p>
                    <p className="text-xs text-slate-500">{offer.partner_name}</p>
                    <p className="text-sm font-black mt-1">NPR {Number(offer.price_npr).toLocaleString()}</p>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Section 7: Verified Source Citations & References */}
          <div className="card-base p-6 sm:p-8 space-y-4 shadow-xl border border-primary-100 rounded-3xl bg-stone-50">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiBookOpen className="text-primary-700" /> Researched Source References & Citations
              </h3>
              <span className="px-2.5 py-0.5 rounded-full bg-primary-50 text-primary-800 text-[10px] font-black uppercase">
                Verified Sources
              </span>
            </div>

            <div className="space-y-2.5">
              {(destination.sources || []).map((src, i) => (
                <div key={i} className="p-3.5 rounded-2xl bg-white border border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900">{src.title}</span>
                      {src.is_verified && <span className="text-emerald-600 font-bold text-[10px]">✓ Verified Source</span>}
                    </div>
                    <span className="text-[11px] text-primary-700 font-medium">{src.source_type}</span>
                    {src.notes && <p className="text-[10px] text-gray-500 mt-0.5">{src.notes}</p>}
                  </div>
                  {src.source_url && (
                    <a
                      href={src.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 rounded-lg bg-gray-100 hover:bg-primary-50 text-primary-700 text-[11px] font-bold flex items-center gap-1 shrink-0"
                    >
                      Visit Source <FiExternalLink size={11} />
                    </a>
                  )}
                </div>
              ))}
              {!(destination.sources?.length) && (
                <p className="text-sm text-slate-600">No source citations are stored for this record yet.</p>
              )}
            </div>
          </div>
        </div>

        {/* Right 1 Column: Strategic Sidebar */}
        <div className="space-y-6">
          {/* Recorded budget only */}
          <div className="card-base p-6 border border-primary-100 rounded-3xl bg-gradient-to-br from-white to-primary-50/50 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiDollarSign className="text-emerald-600" /> Recorded budget
              </h3>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-extrabold uppercase">
                Stored amounts only
              </span>
            </div>
            {budgetEst ? (
              <div className="space-y-2 text-sm text-gray-700">
                <div className="flex justify-between"><span>Daily</span><b>{budgetEst.estimated_daily_budget != null ? `NPR ${budgetEst.estimated_daily_budget}` : "Not recorded"}</b></div>
                <div className="flex justify-between"><span>Trip</span><b>{budgetEst.estimated_trip_budget != null ? `NPR ${budgetEst.estimated_trip_budget}` : "Not recorded"}</b></div>
                <div className="flex justify-between"><span>Stay / night</span><b>{budgetEst.accommodation_per_night != null ? `NPR ${budgetEst.accommodation_per_night}` : "Not recorded"}</b></div>
                <div className="flex justify-between"><span>Meals / day</span><b>{budgetEst.food_cost_per_day != null ? `NPR ${budgetEst.food_cost_per_day}` : "Not recorded"}</b></div>
                <div className="flex justify-between"><span>Transit</span><b>{budgetEst.transport_cost != null ? `NPR ${budgetEst.transport_cost}` : "Not recorded"}</b></div>
                <div className="flex justify-between"><span>Entry fee</span><b>{destination.entry_fee ? `NPR ${destination.entry_fee}` : "Not recorded"}</b></div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">Not recorded — we will update soon. An administrator can add a budget row from the destination editor.</p>
            )}
          </div>

          {/* Safety & Risk Status */}
          <div className="card-base p-6 shadow-xl border border-primary-100 rounded-3xl bg-gradient-to-br from-white to-rose-50/40 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
                <FiShield className="text-primary-600" /> Safety & Risk Index
              </h3>
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${level.color}`}>
                {level.label} Risk
              </span>
            </div>

            <div className="space-y-2 text-xs text-gray-700">
              <div className="flex justify-between">
                <span>Tourism Risk Index:</span>
                <b className="text-primary-900">{riskAnalysis?.tourism_risk_index != null ? `${riskAnalysis.tourism_risk_index} / 100` : "Not recorded"}</b>
              </div>
              <div className="flex justify-between">
                <span>Risk category:</span>
                <b className="text-emerald-700">{riskAnalysis?.risk_category || "Not recorded"}</b>
              </div>
            </div>

            <p className="text-xs text-gray-500 bg-white p-3 rounded-xl border border-gray-100">
              {activeAlert?.title || activeAlert?.description || "No active alert is stored for this place."}
            </p>
          </div>

          {/* Emergency Helplines */}
          <div className="card-base p-6 shadow-xl border border-primary-100 rounded-3xl space-y-4">
            <h3 className="font-bold text-base text-gray-900 flex items-center gap-2">
              <FiPhoneCall className="text-rose-600" /> Emergency & Medical Contacts
            </h3>

            <div className="space-y-2 text-xs">
              {(emergency?.hospitals || []).slice(0, 2).map((row) => (
                <div key={row.id} className="p-3 rounded-xl bg-gray-50 border border-gray-100">
                  <p className="font-bold text-gray-800">{row.name}</p>
                  <p className="text-primary-700 font-semibold mt-0.5">{row.phone_number || "102"}</p>
                  {row.distance_km != null && <p className="text-[11px] text-slate-500">{row.distance_km} km · {formatCoords(row.latitude, row.longitude) || "coords not stored"}</p>}
                </div>
              ))}
              {(emergency?.police || []).slice(0, 1).map((row) => (
                <div key={row.id} className="p-3 rounded-xl bg-gray-50 border border-gray-100">
                  <p className="font-bold text-gray-800">{row.name}</p>
                  <p className="text-primary-700 font-semibold mt-0.5">{row.phone_number || "100"}</p>
                  {row.distance_km != null && <p className="text-[11px] text-slate-500">{row.distance_km} km</p>}
                </div>
              ))}
              {!(emergency?.hospitals?.length) && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-100 text-amber-900">
                  {destination.nearest_hospital_info || "No local hospital record is stored for this place. Use Ambulance 102."}
                </div>
              )}
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-950 font-bold text-center">
                National hotlines: Tourist Police 1144 · Police 100 · Ambulance 102
              </div>
            </div>

            <button
              onClick={() => navigate("/emergency")}
              className="w-full py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow transition-all"
            >
              Open Live Emergency Sentinel
            </button>
          </div>

          {/* Translation Button */}
          <button
            onClick={() => navigate(`/translation?place=${encodeURIComponent(destination.name)}`)}
            className="btn-outline w-full py-3 rounded-2xl flex items-center justify-center gap-2 font-semibold text-xs text-primary-800 border-primary-200 hover:bg-primary-50"
          >
            <FiGlobe size={15} /> Translate Destination Details
          </button>
        </div>
      </div>

      {extras?.length > 0 && <CMSExtras sections={extras} />}

      {/* OFFLINE TRAVEL KIT MODAL */}
      <AnimatePresence>
        {showOfflineKit && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-3xl w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-primary-100 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b pb-4">
                <div>
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-bold uppercase">
                    🎒 Offline Travel Kit & Safety Package
                  </span>
                  <h3 className="text-2xl font-black text-gray-900 mt-2">{destination.name}</h3>
                  <p className="text-xs text-gray-500">{placeLocationLabel(destination)} · Elevation: {destination.altitude || "Not recorded"}</p>
                </div>
                <button
                  onClick={() => setShowOfflineKit(false)}
                  className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700"
                >
                  <FiX size={20} />
                </button>
              </div>

              {/* Package Content */}
              <div className="space-y-4 text-xs text-gray-700">
                {/* 1. Essential Coordinates & Weather */}
                <div className="p-4 rounded-2xl bg-primary-50/70 border border-primary-100 space-y-2">
                  <h4 className="font-bold text-sm text-primary-900 flex items-center gap-1.5">
                    <FiMapPin /> GPS Location & Visiting Season
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    <div><b>GPS:</b> {formatCoords(destination.latitude, destination.longitude) || "Not recorded"}</div>
                    <div><b>Altitude:</b> {destination.altitude || "Not recorded"}</div>
                    <div><b>Best Months:</b> {destination.best_time_to_visit || "Not recorded"}</div>
                  </div>
                </div>

                {destination.notices?.length > 0 && (
                  <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 space-y-2">
                    <h4 className="font-bold text-sm text-amber-950">Desk notices for this place</h4>
                    {destination.notices.map((notice) => (
                      <p key={notice.id} className="text-xs"><b className="uppercase">{notice.kind}:</b> {notice.title}{notice.body ? ` — ${notice.body}` : ""}</p>
                    ))}
                  </div>
                )}

                {/* 2. 24/7 Emergency Helplines */}
                <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-100 space-y-2">
                  <h4 className="font-bold text-sm text-rose-900 flex items-center gap-1.5">
                    <FiShield /> 24/7 Emergency Numbers (Works without Internet)
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono">
                    <div className="bg-white p-2 rounded-xl border border-rose-200">
                      <span className="text-[10px] text-gray-500 block">Tourist Police</span>
                      <b className="text-rose-700 text-sm">1144</b>
                    </div>
                    <div className="bg-white p-2 rounded-xl border border-rose-200">
                      <span className="text-[10px] text-gray-500 block">Nepal Police</span>
                      <b className="text-rose-700 text-sm">100</b>
                    </div>
                    <div className="bg-white p-2 rounded-xl border border-rose-200">
                      <span className="text-[10px] text-gray-500 block">Ambulance</span>
                      <b className="text-rose-700 text-sm">102</b>
                    </div>
                    <div className="bg-white p-2 rounded-xl border border-rose-200">
                      <span className="text-[10px] text-gray-500 block">Local rescue</span>
                      <b className="text-rose-700 text-sm">{destination.nearest_hospital_info || "Not recorded"}</b>
                    </div>
                  </div>
                </div>

                {/* 3. Road Route & Transit Fares */}
                <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-100 space-y-2">
                  <h4 className="font-bold text-sm text-amber-900 flex items-center gap-1.5">
                    <FiTruck /> Road Transit & Approximate Fares
                  </h4>
                  <p><b>Distance from Kathmandu:</b> {destination.distance_from_kathmandu_km != null ? `${destination.distance_from_kathmandu_km} km` : "Not recorded"}</p>
                  <p><b>Recorded transit fare:</b> {destination.transit_routes?.[0]?.estimated_fare_npr != null ? `NPR ${destination.transit_routes[0].estimated_fare_npr} (${destination.transit_routes[0].transport_mode || "recorded route"})` : "No transit fare is stored for this place"}</p>
                </div>

                {/* 4. Useful Local Phrases */}
                <div className="p-4 rounded-2xl bg-stone-50 border border-slate-100 space-y-2">
                  <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1.5">
                    🗣️ Essential Nepali Phrases
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>• <b>Namaste:</b> Hello / Greetings</div>
                    <div>• <b>Dhanyabad:</b> Thank you</div>
                    <div>• <b>Kati ho?:</b> How much is this?</div>
                    <div>• <b>Sahayog garnuhos:</b> Please help me</div>
                    <div>• <b>Bato kata ho?:</b> Which way is the route?</div>
                    <div>• <b>Mitho chha:</b> It is delicious!</div>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex justify-between items-center border-t pt-4">
                <p className="text-[11px] text-gray-500 italic">Save or print this kit before leaving for remote areas with low cellular coverage.</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => window.print()}
                    className="px-5 py-2.5 rounded-xl bg-primary-700 hover:bg-primary-800 text-white font-bold text-xs flex items-center gap-1.5 shadow"
                  >
                    🖨️ Print / Save as PDF
                  </button>
                  <button
                    onClick={() => setShowOfflineKit(false)}
                    className="px-4 py-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-800 font-bold text-xs"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* FULLSCREEN LIGHTBOX MODAL */}
      <AnimatePresence>
        {lightboxOpen && (
          <div className="fixed inset-0 z-50 bg-black/95 flex flex-col justify-between p-4 sm:p-6 backdrop-blur-md">
            <div className="flex items-center justify-between text-white border-b border-white/10 pb-3">
              <div className="space-y-0.5">
                <span className="font-bold text-base text-amber-300">
                  {destination.name} · Photo {activeImageIdx + 1} of {allImages.length}
                </span>
                <p className="text-xs text-gray-400">
                  {activeImage.caption} · {activeImage.photographer} ({activeImage.platform})
                </p>
              </div>
              <button
                onClick={() => setLightboxOpen(false)}
                className="p-2 rounded-full bg-white/20 hover:bg-white/40 text-white transition-all"
              >
                <FiX size={24} />
              </button>
            </div>

            <div className="flex-1 flex items-center justify-center relative my-4">
              <img
                src={activeImage.url}
                alt={activeImage.caption}
                className="max-h-[78vh] max-w-full object-contain rounded-2xl shadow-2xl"
              />
              <button
                onClick={() => setActiveImageIdx((p) => (p === 0 ? allImages.length - 1 : p - 1))}
                className="absolute left-2 sm:left-6 p-4 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur transition-all"
              >
                <FiChevronLeft size={28} />
              </button>
              <button
                onClick={() => setActiveImageIdx((p) => (p === allImages.length - 1 ? 0 : p + 1))}
                className="absolute right-2 sm:right-6 p-4 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur transition-all"
              >
                <FiChevronRight size={28} />
              </button>
            </div>

            <div className="flex gap-2 overflow-x-auto justify-center pb-2">
              {allImages.map((img, i) => (
                <button
                  key={i}
                  onClick={() => setActiveImageIdx(i)}
                  className={`w-16 h-12 rounded-lg overflow-hidden shrink-0 border-2 ${
                    activeImageIdx === i ? "border-amber-400 scale-110" : "border-transparent opacity-50"
                  }`}
                >
                  <img src={img.url} alt={`Thumb ${i}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>
        )}
      </AnimatePresence>

      <ReportErrorModal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        destination={destination}
      />
    </div>
  )
}
