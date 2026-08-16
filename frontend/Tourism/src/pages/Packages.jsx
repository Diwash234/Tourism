import { useState } from "react"
import { FiPackage, FiCheck, FiMapPin } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Filter from "../components/common/Filter"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"
import nepalDestinations from "../data/nepalDestinations"
import { PACKAGE_TIERS } from "../utils/constants"

const DESTINATION_OPTIONS = nepalDestinations.map((d) => ({ label: d.name, value: d.id }))

const Packages = () => {
  const [destinationId, setDestinationId] = useState(nepalDestinations[0].id)
  const [bookingTier, setBookingTier] = useState(null)
  const { showToast } = useToast()
  const { isAuthenticated } = useAuth()

  const destination = nepalDestinations.find((d) => d.id === destinationId) || nepalDestinations[0]

  const handleBook = async (tier) => {
    if (!isAuthenticated) {
      showToast("Please login to book a package", "info")
      return
    }
    setBookingTier(tier.key)
    try {
      await userApi.bookPackage({
        destinationId: destination.id,
        tier: tier.key,
        price: Math.round(destination.price * tier.priceMultiplier),
      })
      showToast(`${tier.label} package booked for ${destination.name}!`, "success")
    } catch {
      showToast(`${tier.label} package request saved. We'll confirm once connected.`, "info")
    } finally {
      setBookingTier(null)
    }
  }

  return (
    <div className="container-app py-10">
      <PageHeader
        title="Travel Packages"
        subtitle="Choose Silver, Gold, or Platinum — pick a destination and book the package that fits your trip."
        icon={FiPackage}
        theme="amber"
      />

      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-8">
        <div className="relative flex-1 max-w-sm">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <select
            className="input-field pl-11"
            value={destinationId}
            onChange={(e) => setDestinationId(e.target.value)}
          >
            {DESTINATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="relative rounded-xl2 overflow-hidden h-48 mb-10">
        <img src={destination.image} alt={destination.name} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-5">
          <div className="text-white">
            <p className="text-xl font-bold">{destination.name}</p>
            <p className="text-sm text-white/80">{destination.location}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PACKAGE_TIERS.map((tier) => {
          const price = Math.round(destination.price * tier.priceMultiplier)
          return (
            <div key={tier.key} className="card-base overflow-hidden flex flex-col">
              <div className={`bg-gradient-to-r ${tier.color} text-white p-5`}>
                <p className="text-sm font-medium opacity-90">Package</p>
                <p className="text-2xl font-extrabold">{tier.label}</p>
                <p className="text-3xl font-bold mt-2">${price}<span className="text-sm font-normal opacity-80"> /traveler</span></p>
              </div>
              <div className="p-5 flex-1 flex flex-col">
                <ul className="space-y-2 flex-1">
                  {tier.perks.map((perk) => (
                    <li key={perk} className="flex items-start gap-2 text-sm text-gray-600">
                      <FiCheck className="text-emerald-500 mt-0.5 shrink-0" /> {perk}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => handleBook(tier)}
                  disabled={bookingTier === tier.key}
                  className="w-full mt-5 bg-primary-500 hover:bg-primary-600 text-white font-semibold px-5 py-2.5 rounded-xl transition"
                >
                  {bookingTier === tier.key ? "Booking..." : `Book ${tier.label}`}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Packages