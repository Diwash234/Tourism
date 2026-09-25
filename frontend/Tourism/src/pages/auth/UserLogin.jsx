import { useState } from "react"
import { useForm } from "react-hook-form"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { FiAlertCircle, FiHelpCircle, FiLock, FiLogIn, FiMail, FiSend, FiUser } from "react-icons/fi"
import CMSPageIntro from "../../components/cms/CMSPageIntro"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import authApi from "../../api/authApi"
import safeNextPath from "../../utils/safeNextPath"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"

export default function UserLogin() {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [loginError, setLoginError] = useState(null)
  const [verifyEmail, setVerifyEmail] = useState("")
  const [verifyBusy, setVerifyBusy] = useState(false)
  const [verifyMsg, setVerifyMsg] = useState(null)
  const [showVerifyBox, setShowVerifyBox] = useState(false)

  const sendVerification = async () => {
    const email = verifyEmail.trim()
    if (!email) { setVerifyMsg({ text: "Enter your email first.", ok: false }); return }
    setVerifyBusy(true); setVerifyMsg(null)
    try {
      const { data } = await authApi.resendVerification(email)
      setVerifyEmail("")
      setVerifyMsg({ text: data.message || "Verification link sent — check your inbox.", ok: true })
    } catch (error) {
      setVerifyMsg({ text: error.response?.data?.detail || "Could not send the verification email.", ok: false })
    } finally { setVerifyBusy(false) }
  }

  const onSubmit = async (data) => {
    setLoading(true); setLoginError(null)
    try {
      const userData = await login(data)
      showToast(`Welcome back, ${userData?.first_name || userData?.email || "traveller"}.`, "success")
      if (userData?.is_verified === false) showToast("Your email is not verified yet — check your inbox.", "warning")
      const queryNext = safeNextPath(new URLSearchParams(location.search).get("next"))
      const from = location.state?.from
      const fromPath = from?.pathname
        ? `${from.pathname}${from.search || ""}${from.hash || ""}`
        : null
      navigate(queryNext || safeNextPath(fromPath) || "/dashboard")
    } catch (error) {
      const data = error?.response?.data
      const code = data?.code || ""
      setLoginError({ code, detail: data?.detail || (typeof data === "string" && data ? data : "Invalid email or password. Please check your details and try again.") })
      if (code === "account_deactivated" || /verify/i.test(data?.detail || "")) setShowVerifyBox(true)
    } finally { setLoading(false) }
  }

  return (
    <AuthShell portal="tourist" title="Welcome back">
      <CMSPageIntro pageKey="auth-login" />
      <p className="mb-5 rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] px-3 py-2.5 text-sm text-[var(--ny-green-dark)]">Sign in to save places, build an itinerary and manage trip requests.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div><label htmlFor="login-email" className="mb-1.5 block text-sm font-semibold">Email address</label><div className="relative"><FiMail size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" /><input id="login-email" type="email" autoComplete="email" data-testid="login-email" className="input-field pl-11" placeholder="you@example.com" {...register("email", { required: "Email is required" })} /></div>{errors.email && <p className="mt-1 text-xs text-[var(--ny-danger)]">{errors.email.message}</p>}</div>
        <div><label htmlFor="login-password" className="mb-1.5 block text-sm font-semibold">Password</label><div className="relative"><FiLock size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" /><input id="login-password" type="password" autoComplete="current-password" data-testid="login-password" className="input-field pl-11" placeholder="Your password" {...register("password", { required: "Password is required" })} /></div>{errors.password && <p className="mt-1 text-xs text-[var(--ny-danger)]">{errors.password.message}</p>}</div>
        {loginError && <div role="alert" className="rounded-[var(--ny-radius-md)] border border-[#E9B9B9] bg-[var(--ny-soft-red)] p-3 text-sm text-[var(--ny-danger)]"><div className="flex gap-2"><FiAlertCircle size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><div><p>{loginError.detail}</p>{loginError.code === "email_not_found" && <p className="mt-1 text-xs">No account with this email yet? <Link to="/register" className="font-semibold underline">Create one</Link>.</p>}{loginError.code === "wrong_password" && <p className="mt-1 text-xs">You can <Link to="/forgot-password" className="font-semibold underline">reset your password</Link>.</p>}</div></div></div>}
        <div className="flex items-center justify-between gap-3 text-sm"><label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4" />Remember me</label><Link to="/forgot-password" className="font-semibold text-[var(--ny-green)] hover:underline">Forgot password?</Link></div>
        <button type="submit" disabled={loading} data-testid="login-submit" className="ny-btn ny-btn-primary w-full">{loading ? "Signing in…" : "Sign in"}<FiLogIn size={17} aria-hidden="true" /></button>
      </form>

      <div className="mt-5 rounded-[var(--ny-radius-md)] border border-[#E9D39A] bg-[var(--ny-soft-gold)] p-3"><button type="button" onClick={() => setShowVerifyBox((value) => !value)} className="flex w-full items-center gap-2 text-left text-sm font-semibold text-[var(--ny-warning)]"><FiHelpCircle size={16} aria-hidden="true" />{showVerifyBox ? "Hide verification help" : "Didn't get a verification email?"}</button>{showVerifyBox && <div className="mt-3"><p className="text-xs leading-5 text-[var(--ny-text-secondary)]">Enter the address you used to register and we will send a fresh verification link.</p><div className="mt-2 flex gap-2"><label htmlFor="verify-email" className="sr-only">Email for verification</label><input id="verify-email" type="email" value={verifyEmail} onChange={(event) => setVerifyEmail(event.target.value)} placeholder="Email you registered with" className="input-field min-w-0 flex-1" /><button type="button" onClick={sendVerification} disabled={verifyBusy} className="ny-btn ny-btn-secondary shrink-0 px-3"><FiSend size={15} aria-hidden="true" />{verifyBusy ? "Sending…" : "Send"}</button></div>{verifyMsg && <p className={`mt-2 text-xs ${verifyMsg.ok ? "text-[var(--ny-success)]" : "text-[var(--ny-danger)]"}`} role="status">{verifyMsg.text}</p>}</div>}</div>

      <div className="my-5 flex items-center gap-3 text-xs text-[var(--ny-text-muted)]"><span className="h-px flex-1 bg-[var(--ny-border)]" />or<span className="h-px flex-1 bg-[var(--ny-border)]" /></div>
      <SocialLoginButtons showDivider={false} />
      <p className="mt-6 text-center text-sm text-[var(--ny-text-secondary)]">New to Nepal Yatra? <Link to="/register" className="font-semibold text-[var(--ny-green)] hover:underline">Create an account</Link></p>
      <div className="mt-5 flex justify-center gap-4 border-t border-[var(--ny-border)] pt-4 text-xs text-[var(--ny-text-secondary)]"><Link to="/staff/login" className="inline-flex items-center gap-1 hover:text-[var(--ny-green)]"><FiUser size={13} aria-hidden="true" />Staff login</Link><Link to="/admin/login" className="hover:text-[var(--ny-green)]">Admin login</Link></div>
    </AuthShell>
  )
}
