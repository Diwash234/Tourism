import { useState, useEffect, useCallback } from "react"
import {
  FiMail,
  FiMessageSquare,
  FiSmartphone,
  FiGift,
  FiCalendar,
  FiSave,
  FiCheckCircle,
  FiAlertCircle,
} from "react-icons/fi"
import axiosClient from "../api/axiosClient"
import useToast from "../hooks/useToast"

/**
 * Notification preferences component with toggles for email, SMS, push,
 * marketing emails, and weekly digest. Saves via PATCH to
 * /api/v1/notification-preferences/.
 */
const NotificationPreferences = () => {
  const showToast = useToast()
  const [prefs, setPrefs] = useState({
    email_notifications: true,
    sms_notifications: false,
    push_notifications: true,
    marketing_emails: false,
    weekly_digest: true,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const fetchPreferences = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axiosClient.get("/notification-preferences/")
      if (data) {
        setPrefs({
          email_notifications: data.email_notifications ?? true,
          sms_notifications: data.sms_notifications ?? false,
          push_notifications: data.push_notifications ?? true,
          marketing_emails: data.marketing_emails ?? false,
          weekly_digest: data.weekly_digest ?? true,
        })
      }
    } catch (err) {
      // 404 is fine — user hasn't set preferences yet, use defaults
      if (err?.response?.status !== 404) {
        setError("Unable to load preferences. Please try again later.")
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => fetchPreferences(), 0)
    return () => clearTimeout(t)
  }, [fetchPreferences])

  const toggle = (key) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const savePreferences = async () => {
    setSaving(true)
    setError(null)
    try {
      await axiosClient.patch("/notification-preferences/", prefs)
      showToast("Notification preferences saved successfully.", "success")
    } catch (err) {
      const msg = err?.response?.data?.message || "Failed to save preferences. Please try again."
      setError(msg)
      showToast(msg, "error")
    } finally {
      setSaving(false)
    }
  }

  const ToggleSwitch = ({ enabled, onChange, label }) => (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={label}
      onClick={onChange}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        enabled ? "bg-ny-green" : "bg-gray-300"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  )

  if (loading) {
    return (
      <div className="ny-card p-5" role="status" aria-label="Loading preferences">
        <div className="ny-skeleton h-6 w-1/3 mb-4" />
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="ny-skeleton h-5 w-1/3" />
              <div className="ny-skeleton h-6 w-11 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const items = [
    { key: "email_notifications", icon: FiMail, label: "Email Notifications", desc: "Receive booking updates and alerts via email" },
    { key: "sms_notifications", icon: FiMessageSquare, label: "SMS Notifications", desc: "Get text messages for urgent updates" },
    { key: "push_notifications", icon: FiSmartphone, label: "Push Notifications", desc: "Browser and app push notifications" },
    { key: "marketing_emails", icon: FiGift, label: "Marketing Emails", desc: "Promotions, deals, and travel inspiration" },
    { key: "weekly_digest", icon: FiCalendar, label: "Weekly Digest", desc: "A weekly summary of your activity and recommendations" },
  ]

  return (
    <div className="ny-card p-5">
      <h3 className="text-lg font-bold text-ny-text mb-1">Notification Preferences</h3>
      <p className="text-sm text-ny-text-secondary mb-4">Choose how you want to stay informed.</p>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-ny-soft-red border border-red-200 mb-4" role="alert">
          <FiAlertCircle size={16} className="text-ny-danger flex-shrink-0" />
          <span className="text-sm text-ny-danger">{error}</span>
        </div>
      )}

      <div className="space-y-3">
        {items.map(({ key, icon: Icon, label, desc }) => (
          <div
            key={key}
            className="flex items-center justify-between p-3 rounded-xl border border-ny-border hover:border-ny-green/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-ny-soft-green flex items-center justify-center flex-shrink-0">
                <Icon size={16} className="text-ny-green" />
              </div>
              <div>
                <p className="text-sm font-semibold text-ny-text">{label}</p>
                <p className="text-xs text-ny-text-muted">{desc}</p>
              </div>
            </div>
            <ToggleSwitch
              enabled={prefs[key]}
              onChange={() => toggle(key)}
              label={label}
            />
          </div>
        ))}
      </div>

      <div className="mt-5 flex justify-end">
        <button
          onClick={savePreferences}
          disabled={saving}
          className="ny-btn ny-btn-primary"
          type="button"
        >
          {saving ? (
            <>
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
              Saving...
            </>
          ) : (
            <>
              <FiSave size={16} /> Save Preferences
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default NotificationPreferences
