import { useForm } from "react-hook-form"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FiBell, FiGlobe, FiDollarSign, FiInfo } from "react-icons/fi"
import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"

/**
 * IMPORTANT — read before extending this page:
 * I checked the backend's UserProfileSerializer field list directly
 * (tourist/serializers.py) and it only has: email, first_name,
 * last_name, phone_number, profile_picture, bio, preferred_language,
 * latitude/longitude, country, city. There is NO field anywhere for
 * email/push/SMS notification preferences or a currency preference.
 *
 * The previous version of this page had checkboxes and a currency
 * dropdown that submitted successfully (toast said "Settings saved")
 * but silently saved NOTHING — those fields don't exist on the backend
 * at all, so they were dropped. That's worse than a visible bug: it
 * actively told users their preferences were saved when they weren't.
 *
 * Fix applied: only `preferred_language` (a real, backend field) is
 * actually submitted. Everything else is shown with an honest "not
 * saved yet" label rather than faking persistence. See the backend
 * notes in chat for what a NotificationPreference model would need.
 */
const Settings = () => {
  const { register, handleSubmit, reset } = useForm()
  const { user, setUser } = useAuth()
  const { showToast } = useToast()
  const [saving, setSaving] = useState(false)
  const [languages, setLanguages] = useState([])

  useEffect(() => {
    userApi.getLanguages()
      .then(({ data }) => setLanguages(data.results || data || []))
      .catch(() => setLanguages([]))

    if (user?.preferred_language) {
      reset({ preferred_language: user.preferred_language })
    }
  }, [user])

  const onSubmit = async (data) => {
    setSaving(true)
    try {
      // Only the real field goes to the backend — see note above.
      const { data: updated } = await userApi.updateSettings({
        preferred_language: data.preferred_language || null,
      })
      setUser(updated)
      showToast("Language preference saved", "success")
    } catch {
      showToast("Could not save settings", "error")
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl fade-in">
      <h1 className="section-title">Settings</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-6">

        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FiGlobe className="text-himalaya-500" /> Language
          </h3>
          <select className="input-field" {...register("preferred_language")}>
            <option value="">Select a language</option>
            {languages.map((lang) => (
              <option key={lang.id} value={lang.id}>{lang.name}</option>
            ))}
          </select>
        </div>

        <div className="border border-dashed border-gray-200 rounded-xl p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2 text-gray-500">
            <FiBell size={16} /> Notification Preferences
            <span className="flex items-center gap-1 text-[11px] font-normal text-saffron-600 bg-saffron-50 px-2 py-0.5 rounded-full ml-auto">
              <FiInfo size={11} /> Not saved yet
            </span>
          </h3>
          <div className="space-y-3 opacity-60">
            <label className="flex items-center justify-between text-sm">
              Email Notifications
              <input type="checkbox" defaultChecked disabled className="h-5 w-5 accent-himalaya-500" />
            </label>
            <label className="flex items-center justify-between text-sm">
              Push Notifications
              <input type="checkbox" defaultChecked disabled className="h-5 w-5 accent-himalaya-500" />
            </label>
            <label className="flex items-center justify-between text-sm">
              Risk Alert SMS
              <input type="checkbox" disabled className="h-5 w-5 accent-himalaya-500" />
            </label>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            These preferences aren't stored on the backend yet — see the notes in chat for what's needed to enable them.
          </p>
        </div>

        <div className="border border-dashed border-gray-200 rounded-xl p-4 opacity-60">
          <h3 className="font-semibold mb-3 flex items-center gap-2 text-gray-500">
            <FiDollarSign size={16} /> Currency
            <span className="flex items-center gap-1 text-[11px] font-normal text-saffron-600 bg-saffron-50 px-2 py-0.5 rounded-full ml-auto">
              <FiInfo size={11} /> Not saved yet
            </span>
          </h3>
          <select className="input-field" disabled>
            <option>USD ($)</option>
            <option>NPR (₨)</option>
            <option>EUR (€)</option>
          </select>
        </div>

        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? "Saving..." : "Save Language"}
        </button>
      </form>
    </motion.div>
  )
}

export default Settings