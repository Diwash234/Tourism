import { useForm } from "react-hook-form"
import { useState } from "react"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"

const Settings = () => {
  const { register, handleSubmit } = useForm()
  const { showToast } = useToast()
  const [saving, setSaving] = useState(false)

  const onSubmit = async (data) => {
    setSaving(true)
    try {
      await userApi.updateSettings(data)
      showToast("Settings saved", "success")
    } catch {
      showToast("Could not save settings", "error")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-6">
        <div>
          <h3 className="font-semibold mb-3">Preferences</h3>
          <div className="space-y-3">
            <label className="flex items-center justify-between text-sm">
              Email Notifications
              <input type="checkbox" defaultChecked {...register("emailNotifications")} className="h-5 w-5 accent-primary-500" />
            </label>
            <label className="flex items-center justify-between text-sm">
              Push Notifications
              <input type="checkbox" defaultChecked {...register("pushNotifications")} className="h-5 w-5 accent-primary-500" />
            </label>
            <label className="flex items-center justify-between text-sm">
              Risk Alert SMS
              <input type="checkbox" {...register("smsAlerts")} className="h-5 w-5 accent-primary-500" />
            </label>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Language & Region</h3>
          <select className="input-field" {...register("language")}>
            <option value="en">English</option>
            <option value="ne">Nepali</option>
            <option value="hi">Hindi</option>
            <option value="fr">French</option>
          </select>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Currency</h3>
          <select className="input-field" {...register("currency")}>
            <option value="USD">USD ($)</option>
            <option value="NPR">NPR (₨)</option>
            <option value="EUR">EUR (€)</option>
          </select>
        </div>

        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </form>
    </div>
  )
}

export default Settings