import { useState, useEffect, useCallback } from "react"
import {
  FiStar,
  FiAward,
  FiGift,
  FiTrendingUp,
  FiCoffee,
  FiCamera,
  FiMap,
  FiUsers,
  FiCheckCircle,
  FiLock,
  FiZap,
} from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"

const TIERS = [
  { name: "Bronze", minPoints: 0, color: "text-amber-700", bg: "bg-amber-100" },
  { name: "Silver", minPoints: 500, color: "text-gray-500", bg: "bg-gray-200" },
  { name: "Gold", minPoints: 2000, color: "text-yellow-600", bg: "bg-yellow-100" },
  { name: "Platinum", minPoints: 5000, color: "text-purple-600", bg: "bg-purple-100" },
]

const BADGES = [
  { id: "first_booking", name: "First Booking", icon: FiCheckCircle, desc: "Complete your first booking" },
  { id: "explorer", name: "Explorer", icon: FiMap, desc: "Visit 5 different destinations" },
  { id: "photographer", name: "Photographer", icon: FiCamera, desc: "Upload 10 photos" },
  { id: "social", name: "Social Butterfly", icon: FiUsers, desc: "Share 3 trips with friends" },
  { id: "reviewer", name: "Reviewer", icon: FiStar, desc: "Write 5 reviews" },
  { id: "loyal", name: "Loyal Traveler", icon: FiAward, desc: "Earn 1000 points" },
]

const EARN_WAYS = [
  { label: "Make a booking", points: 100, icon: FiGift },
  { label: "Write a review", points: 50, icon: FiStar },
  { label: "Share a trip", points: 25, icon: FiUsers },
  { label: "Upload a photo", points: 15, icon: FiCamera },
  { label: "Daily check-in", points: 10, icon: FiZap },
]

const REWARDS = [
  { id: "coffee", label: "Free Coffee", cost: 200, icon: FiCoffee },
  { id: "discount10", label: "10% Discount", cost: 500, icon: FiGift },
  { id: "upgrade", label: "Room Upgrade", cost: 1000, icon: FiTrendingUp },
  { id: "tour", label: "Free Tour", cost: 2500, icon: FiMap },
]

/**
 * Loyalty and rewards component showing user's points, tier progress,
 * earned badges, ways to earn, and redeemable rewards.
 */
const LoyaltyRewards = () => {
  const showToast = useToast()
  const [loyalty, setLoyalty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [redeeming, setRedeeming] = useState(null)

  const fetchLoyalty = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axiosClient.get("/loyalty/status/")
      setLoyalty(data)
    } catch (err) {
      // 404 is fine — user hasn't enrolled yet
      if (err?.response?.status !== 404) {
        setError("Unable to load loyalty status. Please try again later.")
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLoyalty()
  }, [fetchLoyalty])

  const getCurrentTier = (points) => {
    let current = TIERS[0]
    for (const tier of TIERS) {
      if (points >= tier.minPoints) current = tier
    }
    return current
  }

  const getNextTier = (points) => {
    for (const tier of TIERS) {
      if (points < tier.minPoints) return tier
    }
    return null
  }

  const redeemReward = async (reward) => {
    if (!loyalty || loyalty.points < reward.cost) {
      showToast("Not enough points to redeem this reward.", "error")
      return
    }
    setRedeeming(reward.id)
    try {
      await axiosClient.post("/loyalty/redeem/", { reward_id: reward.id })
      showToast(`Successfully redeemed: ${reward.label}!`, "success")
      fetchLoyalty()
    } catch (err) {
      showToast(
        err?.response?.data?.message || "Failed to redeem reward. Please try again.",
        "error"
      )
    } finally {
      setRedeeming(null)
    }
  }

  if (loading) {
    return (
      <div className="ny-card p-5" role="status" aria-label="Loading loyalty rewards">
        <div className="ny-skeleton h-6 w-1/3 mb-4" />
        <div className="ny-skeleton h-20 w-full rounded-xl mb-4" />
        <div className="grid grid-cols-3 gap-3 mb-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="ny-skeleton h-16 rounded-xl" />
          ))}
        </div>
        <div className="ny-skeleton h-4 w-1/4 mb-2" />
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="ny-skeleton h-10 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="ny-card p-5" role="alert">
        <p className="text-sm text-ny-danger mb-3">{error}</p>
        <button onClick={fetchLoyalty} className="ny-btn ny-btn-secondary ny-btn-sm" type="button">
          Retry
        </button>
      </div>
    )
  }

  const points = loyalty?.points || 0
  const currentTier = getCurrentTier(points)
  const nextTier = getNextTier(points)
  const progress = nextTier
    ? ((points - currentTier.minPoints) / (nextTier.minPoints - currentTier.minPoints)) * 100
    : 100
  const earnedBadges = loyalty?.badges || []

  return (
    <div className="ny-card p-5">
      <h3 className="text-lg font-bold text-ny-text flex items-center gap-2 mb-4">
        <FiAward size={18} className="text-ny-green" />
        Loyalty & Rewards
      </h3>

      {/* Points and tier */}
      <div className="p-4 rounded-xl bg-gradient-to-br from-ny-green to-ny-green-dark text-white mb-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-sm opacity-80">Your Points</p>
            <p className="text-3xl font-bold">{points.toLocaleString()}</p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-bold ${currentTier.bg} ${currentTier.color}`}>
            {currentTier.name}
          </div>
        </div>
        {nextTier && (
          <div>
            <div className="flex items-center justify-between text-xs opacity-80 mb-1">
              <span>{currentTier.name}</span>
              <span>{nextTier.name} ({nextTier.minPoints - points} pts to go)</span>
            </div>
            <div className="h-2 rounded-full bg-white/20 overflow-hidden">
              <div
                className="h-full rounded-full bg-ny-gold transition-all duration-500"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Badges */}
      <div className="mb-4">
        <h4 className="text-sm font-bold text-ny-text mb-2">Badges</h4>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {BADGES.map((badge) => {
            const earned = earnedBadges.includes(badge.id)
            const Icon = badge.icon
            return (
              <div
                key={badge.id}
                className={`flex flex-col items-center gap-1 p-2 rounded-xl border ${
                  earned
                    ? "border-ny-green bg-ny-soft-green"
                    : "border-ny-border opacity-50"
                }`}
                title={badge.desc}
              >
                <Icon size={20} className={earned ? "text-ny-green" : "text-ny-text-muted"} />
                <span className="text-xs text-center font-medium text-ny-text">{badge.name}</span>
                {earned && <FiCheckCircle size={10} className="text-ny-green" />}
              </div>
            )
          })}
        </div>
      </div>

      {/* Ways to earn */}
      <div className="mb-4">
        <h4 className="text-sm font-bold text-ny-text mb-2">Ways to Earn</h4>
        <div className="space-y-2">
          {EARN_WAYS.map(({ label, points: pts, icon: Icon }) => (
            <div key={label} className="flex items-center gap-3 p-2 rounded-lg border border-ny-border">
              <Icon size={16} className="text-ny-green" />
              <span className="text-sm text-ny-text flex-1">{label}</span>
              <span className="text-xs font-bold text-ny-green">+{pts} pts</span>
            </div>
          ))}
        </div>
      </div>

      {/* Redeem rewards */}
      <div>
        <h4 className="text-sm font-bold text-ny-text mb-2">Redeem Rewards</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {REWARDS.map((reward) => {
            const Icon = reward.icon
            const canAfford = points >= reward.cost
            return (
              <div
                key={reward.id}
                className={`flex items-center gap-3 p-3 rounded-xl border ${
                  canAfford ? "border-ny-border" : "border-ny-border opacity-60"
                }`}
              >
                <Icon size={18} className={canAfford ? "text-ny-green" : "text-ny-text-muted"} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-ny-text">{reward.label}</p>
                  <p className="text-xs text-ny-text-muted">{reward.cost} points</p>
                </div>
                <button
                  onClick={() => redeemReward(reward)}
                  disabled={!canAfford || redeeming === reward.id}
                  className="ny-btn ny-btn-primary ny-btn-sm flex-shrink-0"
                  type="button"
                >
                  {redeeming === reward.id ? (
                    <span className="animate-spin inline-block w-3 h-3 border-2 border-white/30 border-t-white rounded-full" />
                  ) : canAfford ? (
                    "Redeem"
                  ) : (
                    <FiLock size={12} />
                  )}
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default LoyaltyRewards
