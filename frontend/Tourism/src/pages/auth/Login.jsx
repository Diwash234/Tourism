import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalsceneBackground from "../../components/branding/Nepalscenebackground"
import SocialLoginButtons from "./SocialLoginButtons"

const Login = () => {
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
      showToast("Welcome back!", "success")
      // NEW: previously this always navigated to /dashboard, even for
      // admin accounts, and there was no "Admin Login" entry point
      // anywhere. Rather than a second login form, one login now
      // branches by role — matches how AdminRoute/isAdmin already work.
      // FIX: treat super_admin / tourism_admin like admin (matches the
      // backend ROLE_SENIORITY hierarchy).
      const adminRoles = ["admin", "super_admin", "tourism_admin"]
      const isAdmin =
        adminRoles.includes(userData?.role) ||
        userData?.is_staff === true ||
        userData?.is_superuser === true
      const fallback = isAdmin ? "/admin" : "/dashboard"
      navigate(location.state?.from?.pathname || fallback)
    } catch (err) {
      showToast(err?.response?.data?.message || "Invalid credentials", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalsceneBackground />
      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-4 py-2 rounded-xl">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8"
      >
        <h1 className="text-2xl font-bold text-center mb-1">Welcome Back</h1>
        <p className="text-sm text-gray-500 text-center mb-6">Login to continue exploring</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="relative">
            <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="email"
              placeholder="Email"
              className="input-field pl-11"
              {...register("email", { required: true })}
            />
            {errors.email && <p className="text-xs text-red-500 mt-1">Email is required</p>}
          </div>
          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="password"
              placeholder="Password"
              className="input-field pl-11"
              {...register("password", { required: true, minLength: 6 })}
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">Minimum 6 characters</p>}
          </div>
          <div className="text-right">
            <Link to="/forgot-password" className="text-sm text-primary-500 hover:underline">
              Forgot Password?
            </Link>
          </div>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="mt-6">
          <SocialLoginButtons />
        </div>

        <p className="text-sm text-center text-gray-500 mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-primary-500 font-semibold hover:underline">
            Sign Up
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

export default Login