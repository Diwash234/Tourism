import { useForm } from "react-hook-form"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useState } from "react"
import { FiMail, FiLock } from "react-icons/fi"
import { motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

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
      await login(data)
      showToast("Welcome back!", "success")
      navigate(location.state?.from?.pathname || "/dashboard")
    } catch (err) {
      showToast(err?.response?.data?.message || "Invalid credentials", "error")
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