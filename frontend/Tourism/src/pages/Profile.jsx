import { useEffect, useState, useCallback, useRef } from "react"
import { motion } from "framer-motion"
import { useForm } from "react-hook-form"
import {
  FiUser, FiMail, FiPhone, FiGlobe, FiMapPin, FiHeart,
  FiBookOpen, FiAward, FiSettings, FiBell, FiTrash2,
  FiCamera, FiEdit3, FiClock, FiStar, FiNavigation,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import userApi from "../api/userApi"
import bookingApi from "../api/bookingApi"
import { favoriteApi } from "../services/api.js"
import MandalaBackground from "../components/branding/MandalaBackground"

// ─── Tab Configuration ───────────────────────────────────────────────────────
const TABS = [
  { id: "personal", label: "Personal Info", icon: FiUser },
  { id: "bookings", label: "Bookings", icon: FiBookOpen },
  { id: "reviews", label: "Reviews", icon: FiStar },
  { id: "loyalty", label: "Loyalty", icon: FiAward },
  { id: "notifications", label: "Notifications", icon: FiBell },
  { id: "settings", label: "Settings", icon: FiSettings },
]

// ─── Personal Info Tab ───────────────────────────────────────────────────────
const PersonalInfoTab = ({ user, onUpdate, loading }) => {
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm()

  useEffect(() => {
    if (user) reset(user)
  }, [user, reset])

  const onSubmit = async (data) => {
    await onUpdate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiUser size={12} /> First Name
          </label>
          <input className="input-field mt-1" {...register("first_name")} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiUser size={12} /> Last Name
          </label>
          <input className="input-field mt-1" {...register("last_name")} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiMail size={12} /> Email
          </label>
          <input className="input-field mt-1 bg-gray-50" disabled {...register("email")} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiPhone size={12} /> Phone
          </label>
          <input className="input-field mt-1" {...register("phone_number")} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiGlobe size={12} /> Country
          </label>
          <input className="input-field mt-1" {...register("country")} />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiMapPin size={12} /> City
          </label>
          <input className="input-field mt-1" {...register("city")} />
        </div>
      </div>
      <div>
        <label className="text-xs font-medium text-gray-500">Bio</label>
        <textarea rows={3} className="input-field mt-1" {...register("bio")} />
      </div>
      <button type="submit" className="btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : "Save Changes"}
      </button>
    </form>
  )
}

// ─── Booking History Tab ─────────────────────────────────────────────────────
const BookingsTab = ({ bookings, loading }) => {
  if (loading) return <Loader text="Loading bookings..." />
  if (!bookings.length) {
    return <EmptyState title="No bookings yet" subtitle="Your booking history will appear here." icon={FiBookOpen} />
  }

  return (
    <div className="space-y-4">
      {bookings.map((booking) => (
        <div key={booking.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
          <div>
            <p className="font-medium text-gray-900">{booking.destination_name || "Destination"}</p>
            <p className="text-sm text-gray-500">{booking.check_in} - {booking.check_out}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            booking.status === "confirmed" ? "bg-emerald-100 text-emerald-700" :
            booking.status === "pending" ? "bg-amber-100 text-amber-700" :
            "bg-gray-100 text-gray-700"
          }`}>
            {booking.status}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─── Reviews Tab ─────────────────────────────────────────────────────────────
const ReviewsTab = ({ reviews, loading }) => {
  if (loading) return <Loader text="Loading reviews..." />
  if (!reviews.length) {
    return <EmptyState title="No reviews yet" subtitle="Share your travel experiences." icon={FiStar} />
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <div key={review.id} className="p-4 bg-gray-50 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <p className="font-medium text-gray-900">{review.destination_name}</p>
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <FiStar
                  key={i}
                  size={14}
                  className={i < review.rating ? "text-amber-400 fill-amber-400" : "text-gray-300"}
                />
              ))}
            </div>
          </div>
          <p className="text-sm text-gray-600">{review.comment}</p>
          <p className="text-xs text-gray-400 mt-2">{new Date(review.created_at).toLocaleDateString()}</p>
        </div>
      ))}
    </div>
  )
}

// ─── Loyalty Tab ─────────────────────────────────────────────────────────────
const LoyaltyTab = ({ points, tier, stats }) => {
  const tiers = [
    { name: "Bronze", min: 0, color: "text-amber-700", bg: "bg-amber-50" },
    { name: "Silver", min: 1000, color: "text-gray-500", bg: "bg-gray-50" },
    { name: "Gold", min: 5000, color: "text-yellow-600", bg: "bg-yellow-50" },
    { name: "Platinum", min: 10000, color: "text-purple-600", bg: "bg-purple-50" },
  ]

  const currentTier = tiers.find((t) => points >= t.min) || tiers[0]
  const nextTier = tiers[tiers.indexOf(currentTier) + 1]

  return (
    <div className="space-y-6">
      {/* Points Card */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white">
        <p className="text-sm opacity-80">Available Points</p>
        <p className="text-4xl font-black mt-1">{points.toLocaleString()}</p>
        <p className="text-sm opacity-80 mt-2">{currentTier.name} Member</p>
      </div>

      {/* Progress to Next Tier */}
      {nextTier && (
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">{currentTier.name}</span>
            <span className="text-gray-600">{nextTier.name} ({nextTier.min.toLocaleString()} pts)</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${Math.min((points / nextTier.min) * 100, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-4 bg-gray-50 rounded-xl">
          <p className="text-2xl font-bold text-gray-900">{stats?.trips || 0}</p>
          <p className="text-xs text-gray-500">Trips</p>
        </div>
        <div className="text-center p-4 bg-gray-50 rounded-xl">
          <p className="text-2xl font-bold text-gray-900">{stats?.destinations || 0}</p>
          <p className="text-xs text-gray-500">Destinations</p>
        </div>
        <div className="text-center p-4 bg-gray-50 rounded-xl">
          <p className="text-2xl font-bold text-gray-900">{stats?.reviews || 0}</p>
          <p className="text-xs text-gray-500">Reviews</p>
        </div>
      </div>
    </div>
  )
}

// ─── Notifications Tab ───────────────────────────────────────────────────────
const NotificationsTab = ({ preferences, onUpdate }) => {
  const [prefs, setPrefs] = useState(preferences || {
    email: true,
    push: true,
    sms: false,
    marketing: false,
    booking_updates: true,
    travel_alerts: true,
  })

  const handleToggle = (key) => {
    const newPrefs = { ...prefs, [key]: !prefs[key] }
    setPrefs(newPrefs)
    onUpdate?.(newPrefs)
  }

  const items = [
    { key: "email", label: "Email Notifications", desc: "Receive updates via email" },
    { key: "push", label: "Push Notifications", desc: "Browser push notifications" },
    { key: "sms", label: "SMS Notifications", desc: "Text message alerts" },
    { key: "marketing", label: "Marketing", desc: "Promotions and offers" },
    { key: "booking_updates", label: "Booking Updates", desc: "Booking confirmations and changes" },
    { key: "travel_alerts", label: "Travel Alerts", desc: "Safety and weather alerts" },
  ]

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <label key={item.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors">
          <div>
            <p className="font-medium text-gray-900">{item.label}</p>
            <p className="text-sm text-gray-500">{item.desc}</p>
          </div>
          <div className="relative">
            <input
              type="checkbox"
              checked={prefs[item.key]}
              onChange={() => handleToggle(item.key)}
              className="sr-only"
            />
            <div className={`w-11 h-6 rounded-full transition-colors ${prefs[item.key] ? "bg-emerald-500" : "bg-gray-300"}`}>
              <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${prefs[item.key] ? "translate-x-5" : "translate-x-0.5"}`} />
            </div>
          </div>
        </label>
      ))}
    </div>
  )
}

// ─── Settings Tab ────────────────────────────────────────────────────────────
const SettingsTab = ({ onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  return (
    <div className="space-y-6">
      <div className="p-4 bg-gray-50 rounded-xl">
        <h4 className="font-medium text-gray-900 mb-2">Account Settings</h4>
        <p className="text-sm text-gray-500">Manage your account preferences and security settings.</p>
        <button className="mt-3 text-sm text-emerald-600 font-medium hover:underline">
          Change Password
        </button>
      </div>

      <div className="p-4 bg-red-50 rounded-xl border border-red-100">
        <h4 className="font-medium text-red-900 mb-2">Danger Zone</h4>
        <p className="text-sm text-red-700 mb-3">Once you delete your account, there is no going back.</p>
        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors flex items-center gap-2"
          >
            <FiTrash2 size={14} /> Delete Account
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <button
              onClick={onDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
            >
              Confirm Delete
            </button>
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Profile Page ───────────────────────────────────────────────────────
const Profile = () => {
  const { user, updateUser } = useAuth()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("personal")
  const [bookings, setBookings] = useState([])
  const [reviews, setReviews] = useState([])
  const [favorites, setFavorites] = useState([])
  const [loyaltyPoints, setLoyaltyPoints] = useState(2450)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  // Load data
  useEffect(() => {
    Promise.allSettled([
      userApi.getProfile(),
      bookingApi.getMyBookings(),
      favoriteApi.list(),
    ]).then(([profileRes, bookingRes, favRes]) => {
      if (bookingRes.status === "fulfilled") {
        setBookings(bookingRes.value.data.results || bookingRes.value.data || [])
      }
      if (favRes.status === "fulfilled") {
        setFavorites(favRes.value.data.results || favRes.value.data || [])
      }
      setLoading(false)
    })
  }, [])

  const handleUpdate = async (data) => {
    try {
      const { data: updated } = await userApi.updateProfile(data)
      updateUser(updated)
      showToast("Profile updated successfully", "success")
    } catch (err) {
      showToast(err?.response?.data?.message || "Update failed", "error")
    }
  }

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const { data: updated } = await userApi.uploadAvatar(file)
      updateUser(updated)
      showToast("Profile photo updated", "success")
    } catch {
      showToast("Could not upload photo", "error")
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteAccount = async () => {
    try {
      await userApi.deleteAccount()
      showToast("Account deleted", "success")
      // Redirect to home
      window.location.href = "/"
    } catch {
      showToast("Failed to delete account", "error")
    }
  }

  if (loading) return <Loader fullScreen text="Loading profile..." />

  const stats = {
    trips: bookings.length,
    destinations: new Set(bookings.map((b) => b.destination_name)).size,
    reviews: reviews.length,
  }

  return (
    <div className="ny-page mx-auto w-full max-w-5xl space-y-6">
      <PageHeader title="My Profile" icon={FiUser} />

      {/* Profile Header */}
      <div className="card-base overflow-hidden p-6 relative">
        <MandalaBackground className="w-72 h-72 -top-10 -right-10 opacity-60" />
        <div className="relative flex items-center gap-4">
          <div className="relative">
            <img
              src={user?.profile_picture || ""}
              alt="Profile"
              onError={(e) => { e.currentTarget.style.visibility = "hidden" }}
              className="h-20 w-20 rounded-full object-cover border-2 border-white shadow"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="absolute bottom-0 right-0 bg-emerald-600 text-white p-1.5 rounded-full hover:bg-emerald-700 transition-colors"
            >
              <FiCamera size={14} />
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900">{user?.first_name} {user?.last_name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            {uploading && <p className="text-xs text-emerald-600 mt-1">Uploading...</p>}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto gap-2 pb-2">
        {TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="card-base p-6">
        {activeTab === "personal" && <PersonalInfoTab user={user} onUpdate={handleUpdate} loading={loading} />}
        {activeTab === "bookings" && <BookingsTab bookings={bookings} loading={false} />}
        {activeTab === "reviews" && <ReviewsTab reviews={reviews} loading={false} />}
        {activeTab === "loyalty" && <LoyaltyTab points={loyaltyPoints} tier="gold" stats={stats} />}
        {activeTab === "notifications" && <NotificationsTab preferences={{}} onUpdate={() => showToast("Preferences saved", "success")} />}
        {activeTab === "settings" && <SettingsTab onDelete={handleDeleteAccount} />}
      </div>
    </div>
  )
}

export default Profile
