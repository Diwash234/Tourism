import { useForm } from "react-hook-form"
import CMSPageIntro from "../../components/cms/CMSPageIntro"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useState } from "react"
import { FiUser, FiMail, FiPhone, FiLock } from "react-icons/fi"
import authApi from "../../api/authApi"
import useToast from "../../hooks/useToast"
import AuthShell from "../../components/auth/AuthShell"
import SocialLoginButtons from "./SocialLoginButtons"
import PasswordStrengthField from "../../components/ui/PasswordStrengthField"
import safeNextPath from "../../utils/safeNextPath"

const Register = () => {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm({
    defaultValues: { password: "", password_confirm: "" },
  })
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const password = watch("password")
  const confirm = watch("password_confirm")
  // Live feedback while typing (before the submit attempt): the moment both
  // fields are filled and differ, tell the user the passwords do not match.
  const liveMismatch =
    password.length > 0 && confirm.length > 0 && confirm !== password && !errors.password_confirm

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
      const queryNext = safeNextPath(new URLSearchParams(location.search).get("next"))
      const from = location.state?.from
      const fromPath = from?.pathname ? `${from.pathname}${from.search || ""}${from.hash || ""}` : null
      const next = queryNext || safeNextPath(fromPath) || "/dashboard"
      navigate(`/login?next=${encodeURIComponent(next)}`)
    } catch (err) {
      const data = err?.response?.data
      // Round 21: show the ACTUAL reason, not a bare "Registration failed".
      // Priority: field errors (email taken, password rules, phone) →
      // non_field_errors (Django password validators) → detail (throttle /
      // server errors) → last-resort human-readable summary.
      const fieldError =
        data?.password_confirm?.[0] ||
        data?.password?.[0] ||
        data?.email?.[0] ||
        data?.phone_number?.[0] ||
        data?.first_name?.[0]
      const reason =
        data?.message ||
        fieldError ||
        data?.non_field_errors?.[0] ||
        data?.detail ||
        (typeof data === "string" && data) ||
        "Registration failed. Please check your details and try again."
      const emailTaken = /already exists/i.test(String(data?.email?.[0] || ""))
      showToast(
        emailTaken ? "An account with this email already exists — please sign in instead." : reason,
        "error"
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell portal="tourist" title="Create your Nepal Yatra account">
      <CMSPageIntro pageKey="auth-register" compact />
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <div>
          <label htmlFor="reg-name" className="ny-field-label">Full name</label>
          <div className="relative">
            <FiUser aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
            <input
              id="reg-name"
              autoComplete="name"
              className="input-field pl-11"
              aria-invalid={errors.name ? true : undefined}
              aria-describedby={errors.name ? "reg-name-error" : undefined}
              {...register("name", { required: "Name is required" })}
            />
          </div>
          {errors.name && <p id="reg-name-error" role="alert" className="ny-field-error">{errors.name.message}</p>}
        </div>

        <div>
          <label htmlFor="reg-email" className="ny-field-label">Email address</label>
          <div className="relative">
            <FiMail aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
            <input
              id="reg-email"
              type="email"
              autoComplete="email"
              className="input-field pl-11"
              aria-invalid={errors.email ? true : undefined}
              aria-describedby={errors.email ? "reg-email-error" : undefined}
              {...register("email", {
                required: "Email is required",
                pattern: { value: /^\S+@\S+\.\S+$/, message: "Enter a valid email" },
              })}
            />
          </div>
          {errors.email && <p id="reg-email-error" role="alert" className="ny-field-error">{errors.email.message}</p>}
        </div>

        <div>
          <label htmlFor="reg-phone" className="ny-field-label">Phone <span className="font-normal text-[var(--ny-text-secondary)]">(optional)</span></label>
          <div className="relative">
            <FiPhone aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
            <input
              id="reg-phone"
              type="tel"
              autoComplete="tel"
              className="input-field pl-11"
              aria-invalid={errors.phone_number ? true : undefined}
              aria-describedby={errors.phone_number ? "reg-phone-hint reg-phone-error" : "reg-phone-hint"}
              {...register("phone_number", {
                pattern: { value: /^\+?[0-9\s-]{7,15}$/, message: "Enter a valid phone number" },
              })}
            />
          </div>
          <p id="reg-phone-hint" className="mt-1 text-xs text-[var(--ny-text-secondary)]">Only used to verify your number by SMS and for your safety contacts.</p>
          {errors.phone_number && <p id="reg-phone-error" role="alert" className="ny-field-error">{errors.phone_number.message}</p>}
        </div>

        <div>
          <PasswordStrengthField
            label="Password"
            placeholder=""
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
          {errors.password && <p role="alert" className="ny-field-error">{errors.password.message}</p>}
        </div>

        <div>
          <label htmlFor="reg-password-confirm" className="ny-field-label">Confirm password</label>
          <div className="relative">
            <FiLock aria-hidden="true" className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
            <input
              id="reg-password-confirm"
              type="password"
              autoComplete="new-password"
              className="input-field pl-11"
              aria-invalid={errors.password_confirm || liveMismatch ? true : undefined}
              aria-describedby={errors.password_confirm || liveMismatch ? "reg-password-confirm-error" : undefined}
              {...register("password_confirm", {
                required: "Please confirm your password",
                validate: (value) => value === password || "Passwords do not match",
              })}
            />
          </div>
          {(errors.password_confirm || liveMismatch) && (
            <p id="reg-password-confirm-error" role="alert" className="ny-field-error">{errors.password_confirm?.message || "Passwords do not match"}</p>
          )}
        </div>

        <p className="text-xs leading-5 text-[var(--ny-text-secondary)]">
          By creating an account you agree to the <Link to="/terms-of-service" className="font-semibold text-[var(--ny-green)] underline">Terms of Service</Link>. The <Link to="/privacy-policy" className="font-semibold text-[var(--ny-green)] underline">Privacy Policy</Link> explains what we store and how to delete it.
        </p>

        <button type="submit" disabled={loading} className="ny-btn ny-btn-primary min-h-12 w-full text-base">
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <div className="my-5 flex items-center gap-3 text-xs text-stone-400 ">
        <div className="flex-1 h-px bg-stone-200" /> or continue with{" "}
        <div className="flex-1 h-px bg-stone-200" />
      </div>
      {/* this page has its own divider above → hide the component's */}
      <SocialLoginButtons showDivider={false} />

      <p className="text-sm text-center text-stone-600 font-medium mt-6">
        Already have an account?{" "}
        <Link to="/login" className="text-primary-700 font-extrabold hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  )
}

export default Register
