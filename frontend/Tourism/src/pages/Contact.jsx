import { useState } from "react"
import { Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { motion } from "framer-motion"
import { FiMail, FiPhone, FiMapPin, FiClock, FiShield } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
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

  const contactAddress = branding?.contact_address
  const contactEmail = branding?.contact_email
  const contactPhone = branding?.contact_phone
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
      showToast("Your message was sent for review.", "success")
      reset()
      setEvidence([])
    } catch (error) {
      showToast(error?.response?.data?.detail || "Could not send your message. Please try again.", "error")
    }
  }

  return (
    <div className="ny-page container-app section-space">
      <CMSPageIntro pageKey="contact" />
      <div className="grid grid-cols-1 items-start gap-8 md:grid-cols-2 lg:gap-12">
        <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
          <div>
            <span className="ny-kicker">Contact & help desk</span>
            <PageHeader
              title={<>Get in touch with {siteTitle}</>}
              subtitle="Have a destination, itinerary or trip question? Send a message and the review team will follow up through the contact details you provide."
            />
          </div>

          <div className="ny-panel space-y-4 p-6 text-sm text-[var(--ny-text-secondary)]">
            {contactEmail && (
              <p className="flex items-center gap-3 font-semibold">
                <FiMail className="shrink-0 text-lg text-[var(--ny-green)]" aria-hidden="true" />
                <span>Email: <a className="text-[var(--ny-green)] hover:underline" href={`mailto:${contactEmail}`}><b>{contactEmail}</b></a></span>
              </p>
            )}
            {contactPhone && (
              <p className="flex items-center gap-3 font-semibold">
                <FiPhone className="shrink-0 text-lg text-[var(--ny-green)]" aria-hidden="true" />
                <span>Phone: <a className="text-[var(--ny-green)] hover:underline" href={`tel:${contactPhone}`}><b>{contactPhone}</b></a></span>
              </p>
            )}
            {contactAddress && (
              <p className="flex items-center gap-3 font-semibold">
                <FiMapPin className="shrink-0 text-lg text-[var(--ny-green)]" aria-hidden="true" />
                <span>Address: <b className="text-[var(--ny-text)]">{contactAddress}</b></span>
              </p>
            )}
            {!contactEmail && !contactPhone && !contactAddress && (
              <p className="text-sm text-[var(--ny-text-secondary)]">No public contact details are configured right now. Use the form and the review team will see your message.</p>
            )}
            <p className="flex items-center gap-3 border-t border-[var(--ny-border)] pt-4 text-sm">
              <FiClock className="shrink-0 text-[var(--ny-green)]" aria-hidden="true" />
              <span>For urgent situations, use the <Link to="/emergency" className="font-semibold text-[var(--ny-green)] hover:underline">emergency page</Link>.</span>
            </p>
          </div>
        </motion.div>

        <motion.form
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          onSubmit={handleSubmit(onSubmit)}
          className="ny-panel space-y-4 p-6 sm:p-8"
          noValidate
        >
          <div>
            <p className="ny-kicker">Send a message</p>
            <h2 className="mt-2 flex items-center gap-2 text-xl font-bold">
              <FiShield className="text-[var(--ny-green)]" aria-hidden="true" /> How can we help?
            </h2>
            <p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">Required fields are marked with an asterisk. Please do not include passwords or sensitive travel documents.</p>
          </div>

          <div>
            <label htmlFor="contact-name" className="mb-1 block text-sm font-semibold">Full name *</label>
            <input id="contact-name" className="input-field" placeholder="Your full name" aria-invalid={Boolean(errors.name)} aria-describedby={errors.name ? "contact-name-error" : undefined} {...register("name", { required: true })} />
            {errors.name && <p id="contact-name-error" className="mt-1 text-sm text-rose-600">Name is required.</p>}
          </div>

          <div>
            <label htmlFor="contact-email" className="mb-1 block text-sm font-semibold">Email address *</label>
            <input id="contact-email" className="input-field" type="email" placeholder="you@example.com" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "contact-email-error" : undefined} {...register("email", { required: "Email is required", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email address" } })} />
            {errors.email && <p id="contact-email-error" className="mt-1 text-sm text-rose-600">{errors.email.message}</p>}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="contact-subject" className="mb-1 block text-sm font-semibold">Subject or place *</label>
              <input id="contact-subject" className="input-field" placeholder="What is this about?" aria-invalid={Boolean(errors.subject)} {...register("subject", { required: true })} />
              {errors.subject && <p className="mt-1 text-sm text-rose-600">Subject is required.</p>}
            </div>
            <div>
              <label htmlFor="contact-category" className="mb-1 block text-sm font-semibold">Category</label>
              <select id="contact-category" className="input-field" {...register("category")}>
                <option value="general">General support inquiry</option>
                <option value="correction">Correct information</option>
                <option value="emergency_service">Emergency service feedback</option>
                <option value="hotel_hospital">Hotel or hospital information</option>
                <option value="route_distance">Route or distance problem</option>
                <option value="risk_news">Risk or disaster news</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="contact-message" className="mb-1 block text-sm font-semibold">Message *</label>
            <textarea id="contact-message" rows={5} className="input-field" placeholder="Tell us what you need" aria-invalid={Boolean(errors.message)} aria-describedby={errors.message ? "contact-message-error" : undefined} {...register("message", { required: true })} />
            {errors.message && <p id="contact-message-error" className="mt-1 text-sm text-rose-600">Message is required.</p>}
          </div>

          <label className="block cursor-pointer rounded-[var(--ny-radius-md)] border-2 border-dashed border-[var(--ny-border)] p-4 text-center text-sm font-semibold text-[var(--ny-text-secondary)] transition hover:border-[var(--ny-green)] hover:bg-[var(--ny-soft-green)]">
            Attach evidence images or videos ({evidence.length}/8)
            <input className="sr-only" type="file" multiple accept="image/*,video/*" onChange={(event) => setEvidence(Array.from(event.target.files || []).slice(0, 8))} />
          </label>

          <button type="submit" className="ny-btn ny-btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? "Sending…" : "Send message"}
          </button>
          <p className="text-center text-sm text-[var(--ny-text-muted)]">Your message is sent for review. We will use the contact details you provide for any reply.</p>
        </motion.form>
      </div>
    </div>
  )
}

export default Contact
