import { useEffect, useState } from "react"
import { FiUser, FiBell, FiLock, FiGlobe, FiMoon, FiSun, FiSave, FiArrowRight, FiCheckCircle } from "react-icons/fi"
import { Link } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import userApi from "../api/userApi"
import useTheme from "../context/ThemeContext"
import { useI18n, ALL_LANGS } from "../i18n"
import NotificationPreferences from "../components/NotificationPreferences"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import PageHeader from "../components/common/PageHeader"

const TABS = [
  { id: "account", label: "Account", icon: FiUser },
  { id: "notifications", label: "Notifications", icon: FiBell },
  { id: "privacy", label: "Privacy", icon: FiLock },
  { id: "language", label: "Language & appearance", icon: FiGlobe },
]

export default function Settings() {
  const { user, updateUser } = useAuth()
  const { showToast } = useToast()
  const { theme, toggleTheme } = useTheme()
  const { lang, setLang } = useI18n()
  const [activeTab, setActiveTab] = useState("account")
  const [account, setAccount] = useState({ first_name: "", last_name: "", phone_number: "" })
  const [passwords, setPasswords] = useState({ old_password: "", new_password: "", new_password_confirm: "" })
  const [savingAccount, setSavingAccount] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)
  const [languages, setLanguages] = useState([])
  const [languageId, setLanguageId] = useState("")
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    setAccount({ first_name: user?.first_name || "", last_name: user?.last_name || "", phone_number: user?.phone_number || "" })
    setLanguageId(user?.preferred_language?.id || user?.preferred_language || "")
    setLoaded(true)
  }, [user])

  useEffect(() => {
    userApi.getLanguages().then(({ data }) => setLanguages(data?.results || data || [])).catch(() => setLanguages([]))
  }, [])

  const saveAccount = async (event) => {
    event.preventDefault()
    setSavingAccount(true)
    try {
      const { data } = await userApi.updateProfile({ ...account, ...(languageId ? { preferred_language: Number(languageId) } : {}) })
      updateUser(data)
      showToast("Account settings saved.", "success")
    } catch (error) {
      showToast(error?.response?.data?.detail || "Could not save account settings.", "error")
    } finally { setSavingAccount(false) }
  }

  const changePassword = async (event) => {
    event.preventDefault()
    if (passwords.new_password !== passwords.new_password_confirm) {
      showToast("The new passwords do not match.", "error")
      return
    }
    setSavingPassword(true)
    try {
      await userApi.changePassword(passwords)
      setPasswords({ old_password: "", new_password: "", new_password_confirm: "" })
      showToast("Password changed successfully.", "success")
    } catch (error) {
      const data = error?.response?.data || {}
      const message = data.detail || Object.values(data).flat?.()[0] || "Could not change your password."
      showToast(String(message), "error")
    } finally { setSavingPassword(false) }
  }

  const selectLanguage = (code) => {
    setLang(code)
    try { localStorage.setItem("tourism_preferred_language", code) } catch { /* private mode */ }
    const match = languages.find((item) => item.code === code)
    if (match?.id) setLanguageId(match.id)
  }

  const currentLanguage = ALL_LANGS.find((item) => item.code === lang)

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="settings" />
      <PageHeader title="Settings" subtitle="Manage your account, notifications, privacy, language and appearance in one place." icon={FiUser} />

      <div className="grid gap-6 lg:grid-cols-[15rem_minmax(0,1fr)]">
        <nav className="ny-card h-fit p-2" aria-label="Settings sections">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" onClick={() => setActiveTab(id)} aria-current={activeTab === id ? "page" : undefined} className={`flex min-h-11 w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${activeTab === id ? "bg-[var(--ny-soft-green)] text-[var(--ny-green)]" : "text-[var(--ny-text-secondary)] hover:bg-[var(--ny-soft-green)]"}`}><Icon size={17} aria-hidden="true" />{label}</button>
          ))}
        </nav>

        <div className="min-w-0">
          {activeTab === "account" && (
            <div className="space-y-6">
              <form onSubmit={saveAccount} className="ny-card p-5 sm:p-6">
                <div className="mb-5 flex items-start justify-between gap-4"><div><h2 className="text-lg font-bold">Personal information</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">Keep the details used for your account and travel communications current.</p></div><FiSave className="mt-1 text-[var(--ny-green)]" aria-hidden="true" /></div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {[["first_name", "First name", "text"], ["last_name", "Last name", "text"], ["phone_number", "Phone", "tel"]].map(([key, label, type]) => <div key={key}><label htmlFor={`settings-${key}`} className="ny-field-label">{label}</label><input id={`settings-${key}`} type={type} value={account[key]} onChange={(event) => setAccount((prev) => ({ ...prev, [key]: event.target.value }))} className="w-full" /></div>)}
                  <div><label className="ny-field-label">Email</label><input value={user?.email || ""} readOnly className="w-full opacity-70" /></div>
                </div>
                <div className="mt-5 flex justify-end"><button type="submit" disabled={savingAccount || !loaded} className="ny-btn ny-btn-primary">{savingAccount ? "Saving…" : "Save account"}<FiSave size={15} aria-hidden="true" /></button></div>
              </form>

              <form onSubmit={changePassword} className="ny-card p-5 sm:p-6">
                <h2 className="text-lg font-bold">Change password</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">Use your current password to set a new one. Your password is sent only to the authenticated API.</p>
                <div className="mt-5 grid gap-4 sm:grid-cols-3">
                  {[["old_password","Current password"],["new_password","New password"],["new_password_confirm","Confirm new password"]].map(([key,label]) => <div key={key}><label htmlFor={`settings-${key}`} className="ny-field-label">{label}</label><input id={`settings-${key}`} type="password" minLength={key === "old_password" ? undefined : 8} required value={passwords[key]} onChange={(event) => setPasswords((prev) => ({ ...prev, [key]: event.target.value }))} className="w-full" autoComplete={key === "old_password" ? "current-password" : "new-password"} /></div>)}
                </div>
                <div className="mt-5 flex justify-end"><button type="submit" disabled={savingPassword} className="ny-btn ny-btn-primary">{savingPassword ? "Updating…" : "Change password"}<FiLock size={15} aria-hidden="true" /></button></div>
              </form>
            </div>
          )}

          {activeTab === "notifications" && <NotificationPreferences />}

          {activeTab === "privacy" && (
            <div className="space-y-6">
              <div className="ny-card p-5 sm:p-6"><h2 className="text-lg font-bold">Privacy & account data</h2><p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">Location sharing, family safety and other permissions are controlled by the feature that uses them. Review the privacy information before enabling optional sharing.</p><div className="mt-5 flex flex-wrap gap-3"><Link to="/privacy-policy" className="ny-btn ny-btn-secondary">Privacy policy <FiArrowRight size={15} /></Link><Link to="/cookie-policy" className="ny-btn ny-btn-secondary">Cookie choices <FiArrowRight size={15} /></Link></div></div>
              <div className="rounded-[var(--ny-radius-lg)] border border-[#E9B9B9] bg-[var(--ny-soft-red)] p-5 sm:p-6"><h2 className="text-base font-bold text-[var(--ny-danger)]">Account deletion</h2><p className="mt-2 text-sm leading-6 text-[var(--ny-danger)]/80">Account deletion is permanent and requires an explicit confirmation step. Do not delete the account just to sign out.</p><Link to="/data-deletion" className="ny-btn mt-4 border border-[var(--ny-danger)] bg-white text-[var(--ny-danger)] hover:bg-red-50">Review deletion options <FiArrowRight size={15} /></Link></div>
            </div>
          )}

          {activeTab === "language" && (
            <div className="space-y-6">
              <div className="ny-card p-5 sm:p-6"><div className="flex items-start justify-between gap-4"><div><h2 className="text-lg font-bold">Language</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">Change the interface language. Your selection is remembered in this browser.</p></div><FiGlobe className="text-[var(--ny-green)]" aria-hidden="true" /></div><div className="mt-5 grid gap-3 sm:grid-cols-3">{ALL_LANGS.map((item) => <button key={item.code} type="button" onClick={() => selectLanguage(item.code)} aria-pressed={lang === item.code} className={`rounded-xl border p-4 text-left transition ${lang === item.code ? "border-[var(--ny-green)] bg-[var(--ny-soft-green)]" : "border-[var(--ny-border)] hover:bg-[var(--ny-soft-green)]"}`}><span className="text-lg">{item.flag}</span><span className="mt-2 block text-sm font-bold">{item.label}</span><span className="block text-xs text-[var(--ny-text-muted)]">{item.native}</span></button>)}</div><p className="mt-4 text-xs text-[var(--ny-text-muted)]">Current language: {currentLanguage?.native || "English"}{languages.length ? " · Account preference can also be synced when a matching server language is available." : ""}</p></div>
              <div className="ny-card p-5 sm:p-6"><div className="flex items-center justify-between gap-4"><div><h2 className="text-lg font-bold">Appearance</h2><p className="mt-1 text-sm text-[var(--ny-text-secondary)]">Use a light or dark interface. The choice is stored locally and survives refreshes.</p></div><button type="button" onClick={toggleTheme} role="switch" aria-checked={theme === "dark"} aria-label="Toggle dark mode" className={`grid h-11 w-20 grid-cols-2 items-center rounded-full p-1 transition ${theme === "dark" ? "bg-[var(--ny-green)]" : "bg-slate-200"}`}><span className={`grid h-9 w-9 place-items-center rounded-full bg-white text-slate-700 shadow-sm transition ${theme === "dark" ? "translate-x-9" : ""}`}>{theme === "dark" ? <FiMoon size={16} /> : <FiSun size={16} />}</span></button></div></div>
            </div>
          )}
        </div>
      </div>

      <div className="ny-panel flex items-start gap-3 p-4 text-sm text-[var(--ny-text-secondary)]"><FiCheckCircle className="mt-0.5 shrink-0 text-[var(--ny-green)]" aria-hidden="true" /><p>Changes are saved through the existing authenticated APIs where supported; browser-only language and theme preferences are also persisted locally.</p></div>
    </div>
  )
}