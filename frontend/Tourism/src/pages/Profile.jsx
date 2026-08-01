import { useForm } from "react-hook-form"
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { FiCamera, FiUser, FiMail, FiPhone, FiGlobe, FiFileText, FiMapPin, FiHeart, FiBookOpen, FiAward } from "react-icons/fi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import userApi from "../api/userApi"
import bookingApi from "../api/bookingApi"
import { favoriteApi } from "../services/api.js"
import Loader from "../components/common/Loader"
import MandalaBackground from "../components/branding/MandalaBackground"

// NEW: "traveler stats, badges, travel points" from the brief. There is
// no backend model for any of this (checked tourist/models.py — no
// badge/achievement/points table exists). Rather than invent fake
// numbers, these stats are DERIVED from real data the app already
// fetches elsewhere (visit history, favorites, bookings), and badges are
// simple client-side milestones computed from those real counts — never
// presented as a stored "points" total that doesn't actually exist.
function computeBadges({ placesVisited, districtsExplored, favoritesSaved }) {
  const badges = []
  if (placesVisited >= 1) badges.push({ label: "First Steps", desc: "Visited your first destination" })
  if (placesVisited >= 5) badges.push({ label: "Explorer", desc: "Visited 5+ destinations" })
  if (districtsExplored >= 3) badges.push({ label: "Wanderer", desc: "Explored 3+ different cities" })
  if (favoritesSaved >= 5) badges.push({ label: "Curator", desc: "Saved 5+ favorite places" })
  return badges
}

const Profile = () => {
  const { user, setUser } = useAuth()
  const { showToast } = useToast()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm()
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  const [stats, setStats] = useState({ placesVisited: 0, districtsExplored: 0, favoritesSaved: 0, bookingsMade: 0 })

  useEffect(() => {
    userApi
      .getProfile()
      .then(({ data }) => reset(data))
      .catch(() => reset(user || {}))
      .finally(() => setLoading(false))

    Promise.allSettled([
      userApi.getHistory(),
      favoriteApi.list(),
      bookingApi.getMyBookings(),
    ]).then(([historyRes, favRes, bookingRes]) => {
      const history = historyRes.status === "fulfilled" ? (historyRes.value.data.results || historyRes.value.data || []) : []
      const favorites = favRes.status === "fulfilled" ? (favRes.value.data.results || favRes.value.data || []) : []
      const bookings = bookingRes.status === "fulfilled" ? (bookingRes.value.data.results || bookingRes.value.data || []) : []

      const cities = new Set(history.map((h) => h.destination_detail?.city).filter(Boolean))

      setStats({
        placesVisited: history.length,
        districtsExplored: cities.size,
        favoritesSaved: favorites.length,
        bookingsMade: bookings.length,
      })
    })
  }, [])

  const onSubmit = async (data) => {
    try {
      const { data: updated } = await userApi.updateProfile(data)
      setUser(updated)
      showToast("Profile updated successfully", "success")
    } catch (err) {
      showToast(err?.response?.data?.message || "Update failed", "error")
    }
  }

  const handleAvatarClick = () => fileInputRef.current?.click()

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const { data: updated } = await userApi.uploadAvatar(file)
      setUser(updated)
      showToast("Profile photo updated", "success")
    } catch {
      showToast("Could not upload photo", "error")
    } finally {
      setUploading(false)
    }
  }

  if (loading) return <Loader />

  const badges = computeBadges(stats)

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-3xl fade-in space-y-6">
      <h1 className="section-title">My Profile</h1>

      <div className="card-base p-6 relative overflow-hidden">
        <MandalaBackground className="w-72 h-72 -top-10 -right-10 opacity-60" />

        <div className="relative flex items-center gap-4 mb-6">
          <div className="relative">
            <img
              src={user?.profile_picture || "https://api.dicebear.com/7.x/initials/svg?seed=" + (user?.first_name || "User")}
              alt="avatar"
              className="h-20 w-20 rounded-full object-cover border"
            />
            <button
              type="button"
              onClick={handleAvatarClick}
              disabled={uploading}
              className="absolute bottom-0 right-0 bg-himalaya-500 text-white p-1.5 rounded-full hover:bg-himalaya-600 transition-colors"
              title="Change profile photo"
            >
              <FiCamera size={14} />
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
          </div>
          <div>
            <p className="font-semibold">{user?.first_name} {user?.last_name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            {uploading && <p className="text-xs text-himalaya-500 mt-1">Uploading...</p>}
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="relative grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiUser size={12} /> First Name</label>
            <input className="input-field mt-1" {...register("first_name")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiUser size={12} /> Last Name</label>
            <input className="input-field mt-1" {...register("last_name")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiMail size={12} /> Email</label>
            <input className="input-field mt-1 bg-gray-50" disabled {...register("email")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiPhone size={12} /> Phone</label>
            <input className="input-field mt-1" {...register("phone_number")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiGlobe size={12} /> Country</label>
            <input className="input-field mt-1" {...register("country")} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-medium text-gray-500 flex items-center gap-1"><FiFileText size={12} /> Bio</label>
            <textarea rows={3} className="input-field mt-1" {...register("bio")} />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>

      {/* NEW: Travel Stats — real counts derived from history/favorites/bookings */}
      <div className="card-base p-6 relative overflow-hidden">
        <MandalaBackground className="w-64 h-64 -bottom-16 -left-16 opacity-40" />
        <h2 className="font-semibold mb-4 relative">Travel Stats</h2>
        <div className="relative grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="mx-auto mb-1 w-10 h-10 rounded-full bg-himalaya-50 text-himalaya-500 flex items-center justify-center"><FiMapPin size={18} /></div>
            <p className="text-xl font-bold">{stats.placesVisited}</p>
            <p className="text-xs text-gray-400">Places Visited</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-1 w-10 h-10 rounded-full bg-forest-50 text-forest-500 flex items-center justify-center"><FiGlobe size={18} /></div>
            <p className="text-xl font-bold">{stats.districtsExplored}</p>
            <p className="text-xs text-gray-400">Cities Explored</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-1 w-10 h-10 rounded-full bg-nepalred-50 text-nepalred-500 flex items-center justify-center"><FiHeart size={18} /></div>
            <p className="text-xl font-bold">{stats.favoritesSaved}</p>
            <p className="text-xs text-gray-400">Favorites Saved</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-1 w-10 h-10 rounded-full bg-saffron-50 text-saffron-600 flex items-center justify-center"><FiBookOpen size={18} /></div>
            <p className="text-xl font-bold">{stats.bookingsMade}</p>
            <p className="text-xs text-gray-400">Bookings Made</p>
          </div>
        </div>

        {badges.length > 0 && (
          <div className="relative mt-6 pt-6 border-t border-gray-100">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1.5"><FiAward className="text-saffron-500" /> Badges</h3>
            <div className="flex flex-wrap gap-2">
              {badges.map((b) => (
                <span key={b.label} title={b.desc} className="text-xs font-medium bg-saffron-50 text-saffron-700 px-3 py-1.5 rounded-full">
                  🏅 {b.label}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default Profile