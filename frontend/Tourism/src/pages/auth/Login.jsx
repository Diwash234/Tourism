import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock, FiShield, FiUser, FiBriefcase, FiAlertCircle, FiHelpCircle, FiSend } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import authApi from "../../api/authApi"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"
import SocialLoginButtons from "./SocialLoginButtons"

const ROLE_PRESETS = [
  {
    id: "tourist",
    label: "Tourist / User",
    icon: FiUser,
    badge: "Public Portal",
    color: "from-blue-600 to-indigo-600",
  },
  {
    id: "staff",
    label: "Staff / Sub-Admin",
    icon: FiBriefcase,
    badge: "Moderation Desk",
    color: "from-purple-600 to-rose-600",
  },
  {
    id: "admin",
    label: "Admin / Super-Admin",
    icon: FiShield,
    badge: "Full RBAC Control",
    color: "from-rose-600 to-amber-500",
  },
]

const Login = () => {
  const [selectedRole, setSelectedRole] = useState("tourist")
  const { register, handleSubmit, getValues, formState: { errors } } = useForm()
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  // Specific login failure reason from the backend (Round 21):
  // { code: "email_not_found" | "wrong_password" | "account_deactivated" | "", detail: "..." }
  const [loginError, setLoginError] = useState(null)
  // "Didn't get a verification email?" resend flow (no login required)
  const [verifyEmail, setVerifyEmail] = useState("")
  const [verifyBusy, setVerifyBusy] = useState(false)
  const [verifyMsg, setVerifyMsg] = useState(null) // { text, ok }

  const handleRolePreset = (preset) => {
    setSelectedRole(preset.id)
  }

  const sendVerification = async () => {
    // Dedicated box first, then the email already typed in the login form.
    const email = (verifyEmail || getValues("email") || "").trim()
    if (!email) {
      setVerifyMsg({ text: "Enter your email above, then press 'Send link'.", ok: false })
      return
    }
    // Keep the email until the send succeeds (see UserLogin.jsx).
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
      showToast(`Welcome back, ${userData?.first_name || userData?.email}!`, "success")
      if (userData?.is_verified === false) {
        showToast("Your email is not verified yet — check your inbox, or resend the link from the box on this page.", "warning")
      }

      const role = String(userData?.role || "").toLowerCase()
      const isAdmin = ["admin", "super_admin", "tourism_admin"].includes(role) || userData?.is_superuser === true
      const isStaff = ["staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police"].includes(role)
      const fallback = isAdmin ? "/admin" : isStaff ? "/staff" : "/dashboard"
      navigate(location.state?.from?.pathname || fallback)
    } catch (err) {
      const d = err?.response?.data
      setLoginError({
        code: d?.code || "",
        detail: d?.detail || (typeof d === "string" && d ? d : "Invalid email or password. Please check and try again."),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[85svh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalSceneBackground />

      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-5 py-2.5 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-3">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8 shadow-2xl border border-[#E5E0D5] bg-white"
      >
        <div className="text-center mb-6">
          <h1 className="text-2xl font-black text-gray-900 tracking-tight">Portal Login</h1>
          <p className="text-xs text-gray-500 mt-1">Select your account tier or log in with credentials</p>
        </div>

        {/* 3 Role Selection Badges */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          {ROLE_PRESETS.map((preset) => {
            const Icon = preset.icon
            const isSelected = selectedRole === preset.id
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleRolePreset(preset)}
                className={`p-2.5 rounded-xl border text-center flex flex-col items-center gap-1 transition-all ${
                  isSelected
                    ? "border-purple-600 bg-[#F7F8F5]/80 shadow-md ring-2 ring-purple-400"
                    : "border-gray-200 hover:border-[#2E6B5A] bg-gray-50"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white bg-gradient-to-tr ${preset.color}`}>
                  <Icon size={14} />
                </div>
                <span className="text-[11px] font-bold text-gray-800 leading-tight">
                  {preset.label}
                </span>
                <span className="text-[9px] text-emerald-700 font-semibold">
                  {preset.badge}
                </span>
              </button>
            )
          })}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="relative">
            <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="email"
              placeholder="Email Address"
              className="input-field pl-11 text-sm"
              {...register("email", { required: true })}
            />
            {errors.email && <p className="text-xs text-red-500 mt-1">Email is required</p>}
          </div>

          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="password"
              placeholder="Password"
              className="input-field pl-11 text-sm"
              {...register("password", { required: true })}
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">Password is required</p>}
          </div>

          {loginError && (
            <div
              role="alert"
              className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-800"
            >
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

          <div className="flex items-center justify-end text-xs text-gray-500">
            <Link to="/forgot-password" className="text-primary-600 hover:underline">
              Forgot Password?
            </Link>
          </div>

          <button
            type="submit"
            className="btn-primary w-full py-3 bg-gradient-to-r from-[#1f6b4d] to-[#14503a] hover:from-[#2a8562] hover:to-[#14503a] text-white font-bold rounded-xl shadow-lg transition-all"
            disabled={loading}
          >
            {loading ? "Logging in..." : `Login to ${ROLE_PRESETS.find(p => p.id === selectedRole)?.label}`}
          </button>
        </form>

        {/* Verify / activate account — the option that was missing:
            when the backend says an account exists but its email was
            never verified (or the link was lost), the user can resend
            the verification link from right here without logging in. */}
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-3.5">
          <div className="flex items-center gap-2 text-amber-800">
            <FiHelpCircle size={16} className="shrink-0" />
            <h3 className="text-sm font-bold">Verify your email / activate account</h3>
          </div>
          <p className="mt-1 text-xs text-amber-700 leading-relaxed">
            Signed up but haven't verified your email yet — or the link didn't arrive?
            Enter your email and we'll send a fresh verification link.
          </p>
          <div className="mt-2.5 flex gap-2">
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

        <div className="mt-6">
          <SocialLoginButtons />
        </div>

        <p className="text-sm text-center text-gray-600 font-medium mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-emerald-700 font-extrabold hover:underline">
            Register (Sign Up)
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

export default Login
