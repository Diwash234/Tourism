import { useForm } from "react-hook-form"
import { motion } from "framer-motion"
import { FiMail, FiPhone, FiMapPin } from "react-icons/fi"
import useToast from "../hooks/useToast"

const SUPPORT_EMAIL = "support@tourists.app"

const Contact = () => {
  const { register, handleSubmit, reset, getValues, formState: { errors, isSubmitting } } = useForm()
  const { showToast } = useToast()

  // FIXED: this used to `await new Promise(r => setTimeout(r, 800))` and
  // always show "Message sent successfully!" — its own code comment
  // admitted no backend endpoint existed yet. I checked tourist/urls.py
  // fresh — there still isn't one (only unrelated emergency-contacts
  // routes). Claiming success when nothing was actually sent anywhere
  // is worse than no form at all, since the person thinks someone got
  // their message. Opens a pre-filled mailto: instead, which actually
  // reaches someone, and says so honestly.
  const onSubmit = async () => {
    const { name, email, message } = getValues()
    const subject = encodeURIComponent(`Message from ${name}`)
    const body = encodeURIComponent(`${message}\n\n— ${name} (${email})`)
    window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`
    showToast("Opening your email app to send this — no in-app contact endpoint exists yet.", "info")
    reset()
  }

  return (
    <div className="container-app py-16 grid grid-cols-1 md:grid-cols-2 gap-10 fade-in">
      <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
        <h1 className="section-title">Get in Touch</h1>
        <p className="text-gray-500 mb-8">Have questions about a destination or need support? Reach out to us.</p>
        <div className="space-y-4 text-sm text-gray-600">
          <p className="flex items-center gap-3"><FiMail className="text-himalaya-500" /> {SUPPORT_EMAIL}</p>
          <p className="flex items-center gap-3"><FiPhone className="text-himalaya-500" /> +977-000-0000</p>
          <p className="flex items-center gap-3"><FiMapPin className="text-himalaya-500" /> Pokhara, Gandaki, Nepal</p>
        </div>
      </motion.div>

      <motion.form
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        onSubmit={handleSubmit(onSubmit)}
        className="card-base p-6 space-y-4"
      >
        <div>
          <input className="input-field" placeholder="Your Name" {...register("name", { required: true })} />
          {errors.name && <p className="text-xs text-nepalred-500 mt-1">Name is required</p>}
        </div>
        <div>
          <input className="input-field" placeholder="Email Address" {...register("email", { required: true })} />
          {errors.email && <p className="text-xs text-nepalred-500 mt-1">Email is required</p>}
        </div>
        <div>
          <textarea rows={5} className="input-field" placeholder="Your Message" {...register("message", { required: true })} />
          {errors.message && <p className="text-xs text-nepalred-500 mt-1">Message is required</p>}
        </div>
        <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
          {isSubmitting ? "Opening..." : "Send Message"}
        </button>
        <p className="text-xs text-gray-400 text-center">
          Opens your email app — there's no in-app contact form backend yet.
        </p>
      </motion.form>
    </div>
  )
}

export default Contact