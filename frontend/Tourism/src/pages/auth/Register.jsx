import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { FiUser, FiMail, FiPhone, FiLock, FiCheckCircle } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"
import PasswordStrengthField from "../../components/ui/PasswordStrengthField"
import CrazyButton from "../../components/ui/CrazyButton"
import LightRays from "../../components/ui/LightRays"

const Register = () => {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    defaultValues: { password: "", password_confirm: "" },
  })
  const { showToast } = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const password = watch("password")

  const onSubmit = async (data) => {
    setLoading(true)
    try {
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
      showToast("Account created! Please check your email to verify your account.", "success")
      navigate("/login")
    } catch (err) {
      showToast(
        err?.response?.data?.message ||
        err?.response?.data?.email?.[0] ||
        err?.response?.data?.password?.[0] ||
        "Registration failed",
        "error"
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell portal="tourist" title="Join Nepal Tourism">
      <div className="absolute inset-0 -z-0 overflow-hidden rounded-[2rem]">
        <LightRays color="#1f6b4d" accent="#c2603a" intensity={0.25} speed={28} />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="relative z-10 space-y-4">
        <div className="relative">
          <FiUser className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            placeholder="Full name"
            autoComplete="name"
            className="input-field pl-11"
            {...register("name", { required: "Name is required" })}
          />
          {errors.name && <p className="text-xs text-rose-600 mt-1">{errors.name.message}</p>}
        </div>

        <div className="relative">
          <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            type="email"
            placeholder="Email address"
            autoComplete="email"
            className="input-field pl-11"
            {...register("email", {
              required: "Email is required",
              pattern: { value: /^\S+@\S+\.\S+$/, message: "Enter a valid email" },
            })}
          />
          {errors.email && <p className="text-xs text-rose-600 mt-1">{errors.email.message}</p>}
        </div>

        <div className="relative">
          <FiPhone className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            type="tel"
            placeholder="Phone (optional)"
            autoComplete="tel"
            className="input-field pl-11"
            {...register("phone_number", {
              pattern: { value: /^\+?[0-9\s-]{7,15}$/, message: "Enter a valid phone number" },
            })}
          />
          {errors.phone_number && <p className="text-xs text-rose-600 mt-1">{errors.phone_number.message}</p>}
        </div>

        <div className="relative">
          <FiLock className="absolute left-4 top-4 text-stone-400 pointer-events-none" />
          <div className="pl-0">
            <PasswordStrengthField
              label=""
              placeholder="Create a strong password"
              id="reg-password"
              autoComplete="new-password"
              className="!mb-0"
              value={password || ""}
              name="password"
              onChange={(e) => setValue("password", e.target.value, { shouldValidate: true })}
              {...register("password", {
                required: "Password is required",
                minLength: { value: 8, message: "Minimum 8 characters" },
              })}
            />
          </div>
          {errors.password && <p className="text-xs text-rose-600 mt-1">{errors.password.message}</p>}
        </div>

        <div className="relative">
          <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
          <input
            type="password"
            placeholder="Confirm password"
            autoComplete="new-password"
            className="input-field pl-11"
            {...register("password_confirm", {
              required: "Please confirm your password",
              validate: (value) => value === password || "Passwords do not match",
            })}
          />
          {errors.password_confirm && <p className="text-xs text-rose-600 mt-1">{errors.password_confirm.message}</p>}
        </div>

        <motion.div whileTap={{ scale: 0.98 }}>
          <CrazyButton type="submit" disabled={loading} className="w-full py-3 text-base">
            {loading ? "Creating account..." : "Create Account"}
            {!loading && <FiCheckCircle />}
          </CrazyButton>
        </motion.div>
      </form>

      <div className="my-5 flex items-center gap-3 text-xs text-stone-400 relative z-10">
        <div className="flex-1 h-px bg-stone-200" /> or continue with{" "}
        <div className="flex-1 h-px bg-stone-200" />
      </div>
      <div className="relative z-10"><SocialLoginButtons /></div>

      <p className="text-sm text-center text-stone-500 mt-6 relative z-10">
        Already have an account?{" "}
        <Link to="/login" className="text-primary-700 font-bold hover:underline">Sign in</Link>
      </p>
    </AuthShell>
  )
}

export default Register
