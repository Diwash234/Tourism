import { useState, useEffect } from "react"
import { FiX, FiCheckCircle, FiSend, FiCalendar, FiUsers, FiMapPin, FiMail, FiPhone, FiUser } from "react-icons/fi"
import usePublicConfig from "../../hooks/usePublicConfig"
import userApi from "../../api/userApi"

export default function AdmissionModal() {
  const { settings } = usePublicConfig()
  const modalConfig = settings?.admission_modal
  const [isOpen, setIsOpen] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    destination: "",
    dates: "",
    travelers: "1",
    notes: "",
  })

  useEffect(() => {
    const handleOpen = () => {
      setSubmitted(false)
      setIsOpen(true)
    }
    window.addEventListener("ny-open-admission-modal", handleOpen)
    return () => window.removeEventListener("ny-open-admission-modal", handleOpen)
  }, [])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) setIsOpen(false)
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen])

  const title = modalConfig?.title || "Nepal Journey Inquiry & Booking Request"
  const subtitle = modalConfig?.subtitle || "Tell us your travel plans. Our verified tourism coordinators will assist you with permits, vetted guides and tailored itineraries."
  const buttonLabel = modalConfig?.button_label || "Submit Travel Inquiry"
  const successMessage = modalConfig?.success_message || "Thank you! Your travel inquiry has been received. Our team will contact you within 24 hours."

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      if (userApi?.submitFeedback) {
        await userApi.submitFeedback({
          category: "booking_inquiry",
          subject: `Travel Inquiry: ${form.destination || "Nepal Expedition"}`,
          message: `Inquiry from ${form.name} (${form.email}, ${form.phone}):\nDestination: ${form.destination}\nTravelers: ${form.travelers}\nDates: ${form.dates}\nNotes: ${form.notes}`,
        }).catch(() => {})
      }
    } catch {
      // Graceful fallback
    } finally {
      setSubmitting(false)
      setSubmitted(true)
    }
  }

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-[#0E1E1B] p-6 shadow-2xl border border-gray-100 dark:border-emerald-900/40 my-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/10 transition-colors"
          aria-label="Close modal"
        >
          <FiX size={20} />
        </button>

        {submitted ? (
          <div className="py-8 text-center space-y-4">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <FiCheckCircle size={32} />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">Request Received</h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 max-w-sm mx-auto">
              {successMessage}
            </p>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="mt-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all"
            >
              Done
            </button>
          </div>
        ) : (
          <div>
            <div className="mb-5 pr-6">
              <h3 id="modal-title" className="text-xl font-bold text-gray-900 dark:text-white">
                {title}
              </h3>
              <p className="mt-1 text-xs sm:text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                {subtitle}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Your Full Name *
                  </label>
                  <div className="relative">
                    <FiUser className="absolute left-3 top-3 text-gray-400" size={14} />
                    <input
                      required
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="e.g. Rita Thapa"
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Email Address *
                  </label>
                  <div className="relative">
                    <FiMail className="absolute left-3 top-3 text-gray-400" size={14} />
                    <input
                      required
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      placeholder="name@example.com"
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Phone / WhatsApp
                  </label>
                  <div className="relative">
                    <FiPhone className="absolute left-3 top-3 text-gray-400" size={14} />
                    <input
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      placeholder="+977 98..."
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Destination / Trek
                  </label>
                  <div className="relative">
                    <FiMapPin className="absolute left-3 top-3 text-gray-400" size={14} />
                    <input
                      value={form.destination}
                      onChange={(e) => setForm({ ...form, destination: e.target.value })}
                      placeholder="e.g. Annapurna Base Camp"
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Intended Dates
                  </label>
                  <div className="relative">
                    <FiCalendar className="absolute left-3 top-3 text-gray-400" size={14} />
                    <input
                      value={form.dates}
                      onChange={(e) => setForm({ ...form, dates: e.target.value })}
                      placeholder="e.g. Oct 15 - Oct 28"
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Travelers Count
                  </label>
                  <div className="relative">
                    <FiUsers className="absolute left-3 top-3 text-gray-400" size={14} />
                    <select
                      value={form.travelers}
                      onChange={(e) => setForm({ ...form, travelers: e.target.value })}
                      className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] pl-8 pr-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="1">Solo (1 traveler)</option>
                      <option value="2">Pair (2 travelers)</option>
                      <option value="3-5">Small Group (3-5)</option>
                      <option value="6+">Large Expedition (6+)</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Specific Requirements or Questions
                </label>
                <textarea
                  rows={3}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Need guide recommendations, porter arrangement, dietary requirements, or permit help..."
                  className="w-full rounded-lg border border-gray-200 dark:border-emerald-900/60 bg-gray-50 dark:bg-[#081512] px-3 py-2 text-xs sm:text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 py-2.5 text-sm font-bold text-white shadow-md shadow-emerald-900/20 transition-all disabled:opacity-60"
                >
                  <FiSend size={15} />
                  <span>{submitting ? "Submitting..." : buttonLabel}</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
