import { useForm } from "react-hook-form"
import { Link } from "react-router-dom"
import { useState } from "react"
import { FiMail } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"

const ForgotPassword = () => {
  const { register, handleSubmit, formState: { errors } } = useForm()
  const { showToast } = useToast()
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

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-base w-full max-w-md p-8"
      >
        <h1 className="text-2xl font-bold text-center mb-1">Forgot Password</h1>
        <p className="text-sm text-gray-500 text-center mb-6">
          Enter your email and we will send you a reset link
        </p>

        {sent ? (
          <div className="text-center text-sm text-secondary-600 bg-secondary-500/10 rounded-xl p-4">
            Reset link sent! Please check your inbox.
          </div>
        ) : (
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
        )}

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