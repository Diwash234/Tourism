import { useForm } from "react-hook-form"
import { Link } from "react-router-dom"
import { useEffect, useState } from "react"
import { FiMail, FiKey, FiSmartphone, FiCheckCircle, FiArrowRight, FiRefreshCw } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"

const RESEND_COOLDOWN = 60 // seconds — matches the backend's per-account cooldown

// Tab 1: the original emailed reset link (POST /auth/forgot-password/)
const EmailLinkFlow = ({ showToast }) => {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authApi.forgotPassword(data)
      setSent(true)
    } catch (err) {
      showToast(err?.response?.data?.message || "Could not send reset link", "error")
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="text-center text-sm text-secondary-600 bg-secondary-500/10 rounded-xl p-4">
        Reset link sent! Please check your inbox (and the spam folder). It expires in 1 hour.
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="relative">
        <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="email" placeholder="Email" className="input-field pl-11" {...register("email", { required: true })} />
        {errors.email && <p className="text-xs text-red-500 mt-1">Email is required</p>}
      </div>
      <button type="submit" className="btn-primary w-full" disabled={loading}>
        {loading ? "Sending..." : "Send Reset Link"}
      </button>
    </form>
  )
}

// Tab 2: 6-digit one-time code (POST /auth/reset-password/otp/...)
// Step 1: enter email → "Send code". Step 2: code + new password → update.
const OtpFlow = () => {
  const [step, setStep] = useState("email") // email | code | done
  const [email, setEmail] = useState("")
  const [code, setCode] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(t)
  }, [cooldown])

  const requestCode = async () => {
    if (!email.trim()) { setError("Enter your email first.") ; return }
    setLoading(true); setError("")
    try {
      await authApi.resetPasswordOtpRequest(email.trim())
      setStep("code")
      setCooldown(RESEND_COOLDOWN)
    } catch (err) {
      setError(err?.response?.data?.message || "Could not send the code. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const submitReset = async (e) => {
    e.preventDefault()
    if (newPassword.length < 8) { setError("New password must be at least 8 characters.") ; return }
    if (newPassword !== confirm) { setError("New password and confirmation do not match.") ; return }
    setLoading(true); setError("")
    try {
      await authApi.resetPasswordOtpVerify({ email: email.trim(), code: code.trim(), new_password: newPassword })
      setStep("done")
    } catch (err) {
      const d = err?.response?.data
      setError(d?.code || d?.detail || (Array.isArray(d) ? d.map(String).join(" ") : "Could not update the password."))
    } finally {
      setLoading(false)
    }
  }

  if (step === "done") {
    return (
      <div className="text-center space-y-4">
        <FiCheckCircle size={40} className="mx-auto text-emerald-600 dark:text-emerald-400" />
        <p className="text-sm text-gray-700 dark:text-slate-200">
          Password updated! All your other sessions were signed out for safety.
        </p>
        <Link to="/login" className="btn-primary w-full inline-flex items-center justify-center gap-2">
          Log in with your new password <FiArrowRight size={16} />
        </Link>
      </div>
    )
  }

  if (step === "code") {
    return (
      <form onSubmit={submitReset} className="space-y-4">
        <p className="text-xs text-gray-500 dark:text-slate-300 bg-gray-50 dark:bg-slate-800 rounded-lg p-2.5">
          A 6-digit code was sent to <span className="font-semibold text-gray-800 dark:text-slate-100">{email}</span>'s
          phone (SMS) or email — whichever is on file. It expires in 10 minutes.
        </p>
        <div>
          <input
            type="text"
            inputMode="numeric"
            maxLength={6}
            placeholder="••••••"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="input-field text-center text-2xl tracking-[0.5em] font-bold"
            required
          />
        </div>
        <div className="text-center">
          <button
            type="button"
            onClick={requestCode}
            disabled={cooldown > 0 || loading}
            className="text-xs text-primary-500 font-semibold hover:underline disabled:text-gray-400 disabled:no-underline flex items-center gap-1 mx-auto"
          >
            <FiRefreshCw size={12} />
            {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
          </button>
        </div>
        <input type="password" placeholder="New password" className="input-field" value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" required minLength={8} />
        <input type="password" placeholder="Confirm new password" className="input-field" value={confirm}
          onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required minLength={8} />
        {error && <p className="text-xs text-rose-600">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={loading || code.length !== 6}>
          {loading ? "Updating..." : "Update Password"}
        </button>
        <button type="button" onClick={() => { setStep("email"); setCode(""); setError("") }}
          className="text-xs text-gray-500 dark:text-slate-300 hover:underline w-full text-center">
          ← Use a different email
        </button>
      </form>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500">
        No email access? We can send a one-time code to the phone or email on your account.
      </p>
      <div className="relative">
        <FiSmartphone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="email"
          placeholder="Email you signed up with"
          className="input-field pl-11"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      {error && <p className="text-xs text-rose-600">{error}</p>}
      <button type="button" onClick={requestCode} className="btn-primary w-full" disabled={loading}>
        {loading ? "Sending..." : "Send One-Time Code"}
      </button>
    </div>
  )
}

const ForgotPassword = () => {
  const { showToast } = useToast()
  const [tab, setTab] = useState("link") // link | otp

  return (
    <div className="min-h-[80svh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalSceneBackground />
      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-4 py-2 rounded-xl">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8"
      >
        <h1 className="text-2xl font-bold text-center mb-1">Forgot Password</h1>
        <p className="text-sm text-gray-500 text-center mb-4">
          Get a reset link by email, or use a one-time code
        </p>

        {/* method picker */}
        <div className="grid grid-cols-2 gap-1 bg-gray-100 dark:bg-slate-800 rounded-xl p-1 mb-5" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "link"}
            onClick={() => setTab("link")}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition-colors ${
              tab === "link" ? "bg-white dark:bg-slate-700 text-primary-600 dark:text-emerald-300 shadow-sm" : "text-gray-500 dark:text-slate-300 hover:text-gray-700 dark:hover:text-slate-100"
            }`}
          >
            <FiMail size={14} /> Email link
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "otp"}
            onClick={() => setTab("otp")}
            className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition-colors ${
              tab === "otp" ? "bg-white dark:bg-slate-700 text-primary-600 dark:text-emerald-300 shadow-sm" : "text-gray-500 dark:text-slate-300 hover:text-gray-700 dark:hover:text-slate-100"
            }`}
          >
            <FiKey size={14} /> One-time code
          </button>
        </div>

        {tab === "link" ? <EmailLinkFlow showToast={showToast} /> : <OtpFlow />}

        <p className="text-sm text-center text-gray-500 mt-6">
          Remembered your password?{" "}
          <Link to="/login" className="text-primary-500 font-semibold hover:underline">
            Login
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

export default ForgotPassword
