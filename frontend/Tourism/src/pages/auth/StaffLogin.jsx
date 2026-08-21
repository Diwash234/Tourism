import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock, FiAlertCircle } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"

export default function StaffLogin() {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)

  const STAFF_ROLES = ["staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police"]

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const userData = await login(data)
      const role = String(userData?.role || "").toLowerCase()
      const isStaff =
        STAFF_ROLES.includes(role) ||
        ["admin", "super_admin", "tourism_admin"].includes(role) ||
        userData?.is_superuser === true
      if (!isStaff) {
        showToast("This account does not have staff privileges.", "error")
        return
      }
      showToast(`Welcome, ${userData?.first_name || userData?.email}`, "success")
      navigate(location.state?.from?.pathname || "/staff")
    } catch (err) {
      showToast(err?.response?.data?.detail || "Invalid staff credentials", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell portal="staff" title="Staff Sign In">
      <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 mb-5">
        <FiAlertCircle className="mt-0.5 shrink-0" />
        <span>
          This area is for authorised tourism staff. Accounts are created by an
          administrator — public self-registration is not available here.
        </span>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="relative">
          <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="email"
            placeholder="Staff email"
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
            {...register("password", { required: true })}
          />
          {errors.password && <p className="text-xs text-red-500 mt-1">Password is required</p>}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold rounded-xl"
        >
          {loading ? "Signing in..." : "Sign In to Staff Desk"}
        </button>
      </form>

      <div className="mt-5"><SocialLoginButtons /></div>
      <div className="mt-6 pt-4 border-t border-gray-100 text-center text-xs text-gray-400 space-x-4">
        <Link to="/login" className="hover:text-teal-600">Traveller login</Link>
        <Link to="/admin/login" className="hover:text-slate-700">Admin login</Link>
      </div>
    </AuthShell>
  )
}
