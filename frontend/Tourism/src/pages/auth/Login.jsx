import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock, FiShield, FiUser, FiBriefcase, FiCheckCircle } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"
import SocialLoginButtons from "./SocialLoginButtons"

const ROLE_PRESETS = [
  {
    id: "tourist",
    label: "Tourist / User",
    icon: FiUser,
    email: "tourist@nepaltourism.com",
    pass: "Tourist@12345",
    badge: "Public Portal",
    color: "from-blue-600 to-indigo-600",
  },
  {
    id: "staff",
    label: "Staff / Sub-Admin",
    icon: FiBriefcase,
    email: "staff@tourism.gov.np",
    pass: "Staff@12345",
    badge: "Moderation Desk",
    color: "from-purple-600 to-rose-600",
  },
  {
    id: "admin",
    label: "Admin / Super-Admin",
    icon: FiShield,
    email: "admin@tourism.gov.np",
    pass: "Admin@12345",
    badge: "Full RBAC Control",
    color: "from-rose-600 to-amber-500",
  },
]

const Login = () => {
  const [selectedRole, setSelectedRole] = useState("tourist")
  const { register, handleSubmit, setValue, formState: { errors } } = useForm({
    defaultValues: {
      email: "tourist@nepaltourism.com",
      password: "Tourist@12345",
    }
  })
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)

  const handleRolePreset = (preset) => {
    setSelectedRole(preset.id)
    setValue("email", preset.email)
    setValue("password", preset.pass)
  }

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const userData = await login(data)
      showToast(`Welcome back, ${userData?.first_name || userData?.email}!`, "success")

      const adminRoles = ["admin", "super_admin", "tourism_admin", "staff", "content_moderator", "district_manager"]
      const isAdminOrStaff =
        adminRoles.includes(userData?.role) ||
        userData?.is_staff === true ||
        userData?.is_superuser === true

      const fallback = isAdminOrStaff ? "/admin" : "/dashboard"
      navigate(location.state?.from?.pathname || fallback)
    } catch (err) {
      showToast(err?.response?.data?.detail || err?.response?.data?.message || "Invalid email or password", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalSceneBackground />

      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-5 py-2.5 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-3">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8 shadow-2xl border border-purple-100 bg-white"
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
                    ? "border-purple-600 bg-purple-50/80 shadow-md ring-2 ring-purple-400"
                    : "border-gray-200 hover:border-purple-300 bg-gray-50"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white bg-gradient-to-tr ${preset.color}`}>
                  <Icon size={14} />
                </div>
                <span className="text-[11px] font-bold text-gray-800 leading-tight">
                  {preset.label}
                </span>
                <span className="text-[9px] text-purple-600 font-semibold">
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

          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="text-[11px] text-green-700 font-medium flex items-center gap-1">
              <FiCheckCircle size={12} /> Auto-filled demo credentials
            </span>
            <Link to="/forgot-password" className="text-primary-600 hover:underline">
              Forgot Password?
            </Link>
          </div>

          <button
            type="submit"
            className="btn-primary w-full py-3 bg-gradient-to-r from-purple-700 to-rose-600 hover:from-purple-800 hover:to-rose-700 text-white font-bold rounded-xl shadow-lg transition-all"
            disabled={loading}
          >
            {loading ? "Logging in..." : `Login to ${ROLE_PRESETS.find(p => p.id === selectedRole)?.label}`}
          </button>
        </form>

        <div className="mt-6">
          <SocialLoginButtons />
        </div>

        <p className="text-sm text-center text-gray-500 mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-purple-600 font-bold hover:underline">
            Sign Up
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

export default Login
