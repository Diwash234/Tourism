import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { useForm } from "react-hook-form"
import { FiLock, FiCheckCircle } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"

/**
 * ResetPassword — reached from the email link the backend sends via
 * ForgotPasswordView: /reset-password?token=<uuid>.
 *
 * FIX: this page did not exist. The backend emailed a reset link to
 * `/reset-password?token=...` but there was no route/page for it, so a
 * user who forgot their password could never get back into their
 * account.
 */
const ResetPassword = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token")
  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const newPassword = watch("new_password", "")

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authApi.resetPassword({
        token,
        new_password: data.new_password,
      })
      setDone(true)
      showToast("Password reset successful! You can now log in.", "success")
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        "Could not reset password. The link may be invalid or expired."
      showToast(detail, "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalSceneBackground />
      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-4 py-2 rounded-xl">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8"
      >
        {done ? (
          <div className="text-center">
            <FiCheckCircle className="mx-auto text-green-500 text-5xl mb-4" />
            <h1 className="text-2xl font-bold mb-2">Password Updated</h1>
            <p className="text-sm text-gray-500 mb-6">
              Your password has been reset successfully.
            </p>
            <Link
              to="/login"
              className="inline-block w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold text-center hover:opacity-90 transition"
            >
              Go to Login
            </Link>
          </div>
        ) : !token ? (
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">Invalid Link</h1>
            <p className="text-sm text-gray-500 mb-6">
              This password reset link is missing its token. Please request
              a new one.
            </p>
            <Link
              to="/forgot-password"
              className="inline-block w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold text-center hover:opacity-90 transition"
            >
              Request a new link
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-center mb-1">Set New Password</h1>
            <p className="text-sm text-gray-500 text-center mb-6">
              Choose a new password for your account.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="relative">
                <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  placeholder="New password (min 8 characters)"
                  className="input-field pl-11"
                  {...register("new_password", { required: true, minLength: 8 })}
                />
                {errors.new_password && (
                  <p className="text-xs text-red-500 mt-1">
                    Password must be at least 8 characters.
                  </p>
                )}
              </div>

              <div className="relative">
                <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  placeholder="Confirm new password"
                  className="input-field pl-11"
                  {...register("password_confirm", {
                    required: true,
                    validate: (value) =>
                      value === newPassword || "Passwords do not match.",
                  })}
                />
                {errors.password_confirm && (
                  <p className="text-xs text-red-500 mt-1">
                    {errors.password_confirm.message || "Please confirm your password."}
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold hover:opacity-90 transition disabled:opacity-60"
              >
                {loading ? "Resetting..." : "Reset Password"}
              </button>
            </form>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default ResetPassword
