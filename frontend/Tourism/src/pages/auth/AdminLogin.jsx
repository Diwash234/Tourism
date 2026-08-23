import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock, FiShield, FiAlertTriangle } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import safeNextPath from "../../utils/safeNextPath"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"

export default function AdminLogin() {
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
      const role = String(userData?.role || "").toLowerCase()
      const isAdmin =
        userData?.is_superuser === true ||
        ["admin", "super_admin", "tourism_admin"].includes(role)
      if (!isAdmin) {
        showToast("Administrator access required. Staff should use the Staff login.", "error")
        return
      }
      showToast(`Welcome, ${userData?.first_name || userData?.email}`, "success")
      const next = safeNextPath(new URLSearchParams(location.search).get("next"))
      navigate(location.state?.from?.pathname || next || "/admin")
    } catch (err) {
      showToast(err?.response?.data?.detail || "Invalid administrator credentials", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell portal="admin" title="Administrator Sign In">
      <div className="flex items-start gap-2 p-3 rounded-xl bg-slate-900 text-slate-200 text-xs mb-5">
        <FiShield className="mt-0.5 shrink-0 text-nepalred-400" />
        <span>
          Restricted area. Super-admin accounts are created on the server with{" "}
          <code className="text-nepalred-300">python manage.py createsuperuser</code>.
          All logins are recorded. Demo: admin@tourism.gov.np / Admin@12345
        </span>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="relative">
          <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="email"
            placeholder="Administrator email"
            data-testid="login-email"
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
          data-testid="login-submit"
          className="btn-primary w-full py-3 bg-gradient-to-r from-slate-800 to-nepalred-600 hover:from-slate-900 hover:to-nepalred-700 text-white font-bold rounded-xl"
        >
          {loading ? "Authenticating..." : "Enter Admin Console"}
        </button>
      </form>

      <div className="mt-5"><SocialLoginButtons /></div>
      <div className="mt-6 pt-4 border-t border-gray-100 text-center text-xs text-gray-400 space-x-4">
        <Link to="/login" className="hover:text-teal-600">Traveller login</Link>
        <Link to="/staff/login" className="hover:text-amber-600">Staff login</Link>
      </div>
    </AuthShell>
  )
}
