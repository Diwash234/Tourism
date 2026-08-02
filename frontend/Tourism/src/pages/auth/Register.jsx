import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { FiUser, FiMail, FiLock, FiPhone } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"
import SocialLoginButtons from "./SocialLoginButtons"

const Register = () => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const password = watch("password")

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      // FIXED: RegisterSerializer's real fields are first_name/last_name
      // (checked tourist/serializers.py) — the form used to send a
      // single `name` field, which isn't a field DRF recognizes at all,
      // so it was silently dropped on every single registration. Every
      // user created through this form has had first_name/last_name
      // unset. Splitting the "Full Name" input here rather than adding
      // two separate fields, to keep the form itself unchanged for
      // existing users.
      const [first_name, ...rest] = data.name.trim().split(" ")
      const last_name = rest.join(" ")

      await authApi.register({
        first_name,
        last_name,
        email: data.email,
        phone_number: data.phone_number || undefined,
        password: data.password,
        password_confirm: data.password_confirm,
      })

      showToast(
        data.phone_number
          ? "Account created! Check your email to verify, and check your phone for an SMS code."
          : "Account created! Please check your email to verify your account.",
        "success"
      )
      navigate("/login")
    } catch (err) {
      showToast(err?.response?.data?.message || err?.response?.data?.email?.[0] || "Registration failed", "error")
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
            <FiPhone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="tel"
              placeholder="Phone Number (optional — for SMS verification)"
              className="input-field pl-11"
              {...register("phone_number", {
                pattern: { value: /^\+?[0-9\s-]{7,15}$/, message: "Enter a valid phone number" },
              })}
            />
            {errors.phone_number && <p className="text-xs text-red-500 mt-1">{errors.phone_number.message}</p>}
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
              {...register("password_confirm", {
                required: true,
                validate: (value) => value === password || "Passwords do not match",
              })}
            />
            {errors.password_confirm && (
              <p className="text-xs text-red-500 mt-1">{errors.password_confirm.message}</p>
            )}
          </div>
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div className="mt-6">
          <SocialLoginButtons />
        </div>

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