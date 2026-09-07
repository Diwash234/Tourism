import { useState } from "react"
import { useForm } from "react-hook-form"
import { motion } from "framer-motion"
import { FiMail, FiPhone, FiMapPin, FiClock, FiShield } from "react-icons/fi"
import useToast from "../hooks/useToast"
import adminApi from "../api/adminApi"
import usePublicConfig from "../hooks/usePublicConfig"

const Contact = () => {
  const { branding } = usePublicConfig()
  const { showToast } = useToast()
  const [evidence, setEvidence] = useState([])

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm()

  const contactAddress = branding?.contact_address || "Pokhara, Gandaki, Nepal"
  const contactEmail = branding?.contact_email || "support@tourists.app"
  const contactPhone = branding?.contact_phone || "+977-000-0000"
  const siteTitle = (branding?.site_title || "Nepal Yatra").replace(/Digital Nepal Tourism Platform/g, "Nepal Yatra")

  const onSubmit = async () => {
    const { name, email, message, subject, category } = getValues()
    try {
      const body = new FormData()
      body.append("name", name || "")
      body.append("email", email || "")
      body.append("subject", subject || `Message from ${name || "visitor"}`)
      body.append("message", message)
      body.append("category", category || "correction")
      evidence.forEach((file) => body.append("evidence", file))
      await adminApi.sendFeedback(body)
      showToast("Your report and evidence were sent to the admin review queue.", "success")
      reset()
      setEvidence([])
    } catch (e) {
      showToast(e?.response?.data?.detail || "Could not send message. Please try again.", "error")
    }
  }

  return (
    <div className="container-app py-16 grid grid-cols-1 md:grid-cols-2 gap-10 fade-in theme-indigo">
      <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
        <div>
          <span className="px-3.5 py-1 rounded-full bg-emerald-100 text-[#1D5146] text-xs font-black uppercase tracking-wider">
            Official Contact & Help Desk
          </span>
          <h1 className="section-title mt-2">Get in Touch with {siteTitle}</h1>
          <p className="text-gray-500 text-sm">
            Have questions about a destination, itinerary, or need customer support? Reach out to our team directly or send us feedback.
          </p>
        </div>

        <div className="space-y-4 text-sm text-gray-700 p-6 rounded-3xl bg-white border border-slate-200 shadow-sm">
          <p className="flex items-center gap-3 font-semibold">
            <FiMail className="text-[#102A2E] text-lg shrink-0" />
            <span>Official Email: <b>{contactEmail}</b></span>
          </p>

          <p className="flex items-center gap-3 font-semibold">
            <FiPhone className="text-[#102A2E] text-lg shrink-0" />
            <span>Support Phone: <b>{contactPhone}</b></span>
          </p>

          <p className="flex items-center gap-3 font-semibold">
            <FiMapPin className="text-[#102A2E] text-lg shrink-0" />
            <span>Address: <b>{contactAddress}</b></span>
          </p>

          <p className="flex items-center gap-3 text-xs text-gray-500 pt-2 border-t">
            <FiClock className="text-[#102A2E] shrink-0" />
            <span>Desk Hours: <b>24/7 Traveler Help Desk & Admin Sentinel</b></span>
          </p>
        </div>
      </motion.div>

      <motion.form
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        onSubmit={handleSubmit(onSubmit)}
        className="card-base p-6 sm:p-8 space-y-4 bg-white border border-slate-200 shadow-xl rounded-3xl"
      >
        <h3 className="font-extrabold text-lg text-slate-900 flex items-center gap-2">
          <FiShield className="text-[#102A2E]" /> Send Message to Admin Desk
        </h3>

        <div>
          <input
            className="input-field text-xs"
            placeholder="Your Full Name *"
            {...register("name", { required: true })}
          />
          {errors.name && <p className="text-xs text-rose-500 mt-1">Name is required</p>}
        </div>

        <div>
          <input
            className="input-field text-xs"
            placeholder="Email Address *"
            {...register("email", { required: true })}
          />
          {errors.email && <p className="text-xs text-rose-500 mt-1">Email is required</p>}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            className="input-field text-xs"
            placeholder="Subject / Place Name *"
            {...register("subject", { required: true })}
          />
          <select className="input-field text-xs" {...register("category")}>
            <option value="general">General Support Inquiry</option>
            <option value="correction">Correct wrong information</option>
            <option value="emergency_service">Emergency service feedback</option>
            <option value="hotel_hospital">Hotel / Hospital information</option>
            <option value="route_distance">Route or distance problem</option>
            <option value="risk_news">Risk / disaster news</option>
          </select>
        </div>

        <div>
          <textarea
            rows={4}
            className="input-field text-xs"
            placeholder="Your Detailed Message / Question *"
            {...register("message", { required: true })}
          />
          {errors.message && <p className="text-xs text-rose-500 mt-1">Message is required</p>}
        </div>

        <label className="block rounded-2xl border-2 border-dashed border-gray-200 p-4 text-center text-xs font-bold text-gray-500 cursor-pointer hover:border-[#2E6B5A]">
          📎 Attach Evidence images/videos ({evidence.length}/8)
          <input
            hidden
            type="file"
            multiple
            accept="image/*,video/*"
            onChange={(e) => setEvidence(Array.from(e.target.files).slice(0, 8))}
          />
        </label>

        <button type="submit" className="btn-primary w-full py-3" disabled={isSubmitting}>
          {isSubmitting ? "Sending..." : "Send Message to Admin"}
        </button>

        <p className="text-[11px] text-gray-400 text-center">
          Submitted directly to the Admin support & feedback queue.
        </p>
      </motion.form>
    </div>
  )
}

export default Contact
