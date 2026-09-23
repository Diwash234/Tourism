import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
<<<<<<< HEAD
import { FiMail, FiLock, FiUser, FiLogIn, FiAlertCircle, FiHelpCircle, FiSend } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import authApi from "../../api/authApi"
=======
import { FiMail, FiLock, FiUser, FiLogIn } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
>>>>>>> origin/arena/01a07999-tourism
import safeNextPath from "../../utils/safeNextPath"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"
import CrazyButton from "../../components/ui/CrazyButton"
import LightRays from "../../components/ui/LightRays"

export default function UserLogin() {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
<<<<<<< HEAD
  // Specific failure reason from the backend (Round 21): the old UI only
  // showed one vague toast for every failure ("No active account…").
  const [loginError, setLoginError] = useState(null) // { code, detail }
  // Verify / activate account (no login required)
  const [verifyEmail, setVerifyEmail] = useState("")
  const [verifyBusy, setVerifyBusy] = useState(false)
  const [verifyMsg, setVerifyMsg] = useState(null) // { text, ok }
  const [showVerifyBox, setShowVerifyBox] = useState(false)

  const sendVerification = async () => {
    const email = (verifyEmail || "").trim()
    if (!email) {
      setVerifyMsg({ text: "Enter your email, then press 'Send link'.", ok: false })
      return
    }
    // Keep the email in the box until the request succeeds, so a failed
    // send (throttled, network…) doesn't cost the user their input.
    setVerifyBusy(true)
    setVerifyMsg(null)
    try {
      const { data } = await authApi.resendVerification(email)
      setVerifyEmail("")
      setVerifyMsg({ text: data.message || "Verification link sent — check your inbox.", ok: true })
    } catch (err) {
      const d = err?.response?.data
      setVerifyMsg({ text: d?.detail || d?.message || "Could not send the verification email. Please try again.", ok: false })
    } finally {
      setVerifyBusy(false)
    }
  }

  const onSubmit = async (data) => {
    setLoading(true)
    setLoginError(null)
    try {
      const userData = await login(data)
      showToast(`Welcome back, ${userData?.first_name || userData?.email || "traveller"}!`, "success")
      if (userData?.is_verified === false) {
        showToast("Your email is not verified yet — check your inbox, or resend the link below.", "warning")
      }
      const next = safeNextPath(new URLSearchParams(location.search).get("next"))
      navigate(location.state?.from?.pathname || next || "/dashboard")
    } catch (err) {
      const d = err?.response?.data
      const code = d?.code || ""
      const detail = d?.detail || (typeof d === "string" && d ? d : "Invalid email or password. Please check and try again.")
      setLoginError({ code, detail })
      // Offer the verify option whenever the account exists but is
      // unverified / needs activation.
      if (code === "account_deactivated" || /verify/i.test(detail)) {
        setShowVerifyBox(true)
      }
=======

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const userData = await login(data)
      showToast(`Welcome back, ${userData?.first_name || userData?.email || "traveller"}!`, "success")
      const next = safeNextPath(new URLSearchParams(location.search).get("next"))
      navigate(location.state?.from?.pathname || next || "/dashboard")
    } catch (err) {
      showToast(err?.response?.data?.detail || "Invalid email or password", "error")
>>>>>>> origin/arena/01a07999-tourism
    } finally { setLoading(false) }
  }

  return (
    <AuthShell portal="tourist" title="Welcome back">
      <div className="absolute inset-0 -z-0 overflow-hidden rounded-[2rem]">
        <LightRays color="#1f6b4d" accent="#b8862f" intensity={0.22} speed={24} />
      </div>

      <p className="relative z-10 mb-4 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-900">
        Traveller portal. Sign in with your email, or continue with Google or GitHub.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 relative z-10">
        <div className="relative">
          <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            type="email"
            placeholder="Email address"
            autoComplete="email"
            data-testid="login-email"
            className="input-field pl-11"
            {...register("email", { required: "Email is required" })}
          />
          {errors.email && <p className="text-xs text-rose-600 mt-1">{errors.email.message}</p>}
        </div>

        <div className="relative">
          <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            type="password"
            placeholder="Password"
            autoComplete="current-password"
            data-testid="login-password"
            className="input-field pl-11"
            {...register("password", { required: "Password is required" })}
          />
          {errors.password && <p className="text-xs text-rose-600 mt-1">{errors.password.message}</p>}
        </div>

<<<<<<< HEAD
        {loginError && (
          <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-800">
            <div className="flex items-start gap-2">
              <FiAlertCircle className="mt-0.5 shrink-0" size={16} />
              <div>
                <p className="font-medium">{loginError.detail}</p>
                {loginError.code === "email_not_found" && (
                  <p className="mt-1 text-xs">
                    No account with this email yet?{" "}
                    <Link to="/register" className="font-bold underline">Create one here</Link>.
                  </p>
                )}
                {loginError.code === "wrong_password" && (
                  <p className="mt-1 text-xs">
                    You can also <Link to="/forgot-password" className="font-bold underline">reset your password</Link>.
                  </p>
                )}
                {loginError.code === "account_deactivated" && (
                  <p className="mt-1 text-xs">Support can reactivate your account — contact info is in the footer.</p>
                )}
              </div>
            </div>
          </div>
        )}

=======
>>>>>>> origin/arena/01a07999-tourism
        <div className="flex items-center justify-between text-xs text-stone-500">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" className="rounded accent-primary-600" /> Remember me
          </label>
          <Link to="/forgot-password" className="text-primary-700 hover:underline font-medium">Forgot password?</Link>
        </div>

        <motion.div whileTap={{ scale: 0.98 }}>
          <CrazyButton type="submit" disabled={loading} data-testid="login-submit" className="w-full py-3 text-base">
            {loading ? "Signing in..." : "Sign In"}
            {!loading && <FiLogIn />}
          </CrazyButton>
        </motion.div>
      </form>

<<<<<<< HEAD
      {/* Verify / activate account — the "activate account" option that
          was missing: resend the verification link without logging in. */}
      <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3 relative z-10">
        <button
          type="button"
          onClick={() => setShowVerifyBox(v => !v)}
          className="flex w-full items-center gap-2 text-left text-sm font-bold text-amber-800"
        >
          <FiHelpCircle size={15} className="shrink-0" />
          {showVerifyBox ? "Hide verification help" : "Didn't get a verification email? Activate account"}
        </button>
        {showVerifyBox && (
          <div className="mt-2">
            <p className="text-xs text-amber-700 leading-relaxed">
              Signed up but the email never arrived (or the link expired)? Enter your
              email and we'll send a fresh verification link.
            </p>
            <div className="mt-2 flex gap-2">
              <input
                type="email"
                value={verifyEmail}
                onChange={(e) => setVerifyEmail(e.target.value)}
                placeholder="Email you signed up with"
                className="flex-1 rounded-lg border border-amber-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
              <button
                type="button"
                onClick={sendVerification}
                disabled={verifyBusy}
                className="flex items-center gap-1.5 rounded-lg bg-amber-600 px-3 py-2 text-sm font-bold text-white hover:bg-amber-700 disabled:opacity-50"
              >
                <FiSend size={14} />
                {verifyBusy ? "Sending…" : "Send link"}
              </button>
            </div>
            {verifyMsg && (
              <p className={`mt-2 text-xs font-medium ${verifyMsg.ok ? "text-emerald-700" : "text-rose-700"}`}>
                {verifyMsg.text}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="my-5 flex items-center gap-3 text-xs text-stone-400 relative z-10">
        <div className="flex-1 h-px bg-stone-200" /> or <div className="flex-1 h-px bg-stone-200" />
      </div>
      {/* this page has its own "or" divider above → hide the component's */}
      <div className="relative z-10"><SocialLoginButtons showDivider={false} /></div>
=======
      <div className="my-5 flex items-center gap-3 text-xs text-stone-400 relative z-10">
        <div className="flex-1 h-px bg-stone-200" /> or <div className="flex-1 h-px bg-stone-200" />
      </div>
      <div className="relative z-10"><SocialLoginButtons /></div>
>>>>>>> origin/arena/01a07999-tourism

      <p className="text-sm text-center text-stone-500 mt-6 relative z-10">
        New to Nepal Tourism?{" "}
        <Link to="/register" className="text-primary-700 font-bold hover:underline">Create an account</Link>
      </p>

      <div className="mt-4 pt-4 border-t border-stone-100 text-center text-xs text-stone-400 space-x-3 relative z-10">
        <Link to="/staff/login" className="hover:text-secondary-600 inline-flex items-center gap-1">
          <FiUser size={12} /> Staff login
        </Link>
        <Link to="/admin/login" className="hover:text-stone-700">Admin login</Link>
      </div>
    </AuthShell>
  )
}
