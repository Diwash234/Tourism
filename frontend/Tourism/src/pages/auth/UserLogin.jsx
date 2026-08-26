import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock, FiUser, FiLogIn } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
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

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const userData = await login(data)
      showToast(`Welcome back, ${userData?.first_name || userData?.email || "traveller"}!`, "success")
      const next = safeNextPath(new URLSearchParams(location.search).get("next"))
      navigate(location.state?.from?.pathname || next || "/dashboard")
    } catch (err) {
      showToast(err?.response?.data?.detail || "Invalid email or password", "error")
    } finally { setLoading(false) }
  }

  return (
    <AuthShell portal="tourist" title="Welcome back">
      <div className="absolute inset-0 -z-0 overflow-hidden rounded-[2rem]">
        <LightRays color="#1f6b4d" accent="#b8862f" intensity={0.22} speed={24} />
      </div>

      <p className="relative z-10 mb-4 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-900">
        Traveller portal only. Demo: tourist@nepaltourism.com / Tourist@12345. Google or GitHub opens the accounts already signed in on this device.
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

      <div className="my-5 flex items-center gap-3 text-xs text-stone-400 relative z-10">
        <div className="flex-1 h-px bg-stone-200" /> or <div className="flex-1 h-px bg-stone-200" />
      </div>
      <div className="relative z-10"><SocialLoginButtons /></div>

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
