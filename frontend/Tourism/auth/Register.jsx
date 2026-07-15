import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { FiUser, FiMail, FiLock } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"

const Register = () => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const password = watch("password")

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authApi.register(data)
      showToast("Account created! Please login.", "success")
      navigate("/login")
    } catch (err) {
      showToast(err?.response?.data?.message || "Registration failed", "error")
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
        <h1 className="text-2xl font-bold text-center mb-1">Create Account</h1>
        <p className="text-sm text-gray-500 text-center mb-6">Join Tourist and start exploring</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="relative">
            <FiUser className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input placeholder="Full Name" className="input-field pl-11" {...register("name", { required: true })} />
            {errors.name && <p className="text-xs text-red-500 mt-1">Name is required</p>}
          </div>
          <div className="relative">
            <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="email" placeholder="Email" className="input-field pl-11" {...register("email", { required: true })} />
            {errors.email && <p className="text-xs text-red-500 mt-1">Email is required</p>}
          </div>
          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="password" placeholder="Password" className="input-field pl-11" {...register("password", { required: true, minLength: 6 })} />
            {errors.password && <p className="text-xs text-red-500 mt-1">Minimum 6 characters</p>}
          </div>
          <div className="relative">
            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="password"
              placeholder="Confirm Password"
              className="input-field pl-11"
              {...register("confirmPassword", {
                required: true,
                validate: (value) => value === password || "Passwords do not match",
              })}
            />
            {errors.confirmPassword && (
              <p className="text-xs text-red-500 mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <p className="text-sm text-center text-gray-500 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary-500 font-semibold hover:underline">
            Login
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

export default Register