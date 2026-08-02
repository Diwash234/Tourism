import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { FiPhone, FiCheckCircle } from "react-icons/fi"
import authApi from "../api/authApi"
import useToast from "../hooks/useToast"
import useAuth from "../hooks/useAuth"

const RESEND_COOLDOWN_SECONDS = 60 // matches the backend's own 60s rate limit in ResendPhoneOTPView

/**
 * VerifyPhone — NOT a login screen. The backend's VerifyPhoneView and
 * ResendPhoneOTPView both require IsAuthenticated (checked
 * views_auth.py directly), so this only works for an already-logged-in
 * user confirming a phone number, typically the one they registered
 * with (RegisterView auto-sends the first OTP if phone_number was
 * provided at signup).
 *
 * Also note: UserProfileSerializer doesn't expose `phone_verified` at
 * all (checked serializers.py) — only `phone_number`. So this page
 * can't know from the backend whether verification already happened;
 * it uses a local sessionStorage flag once verified in THIS session as
 * the best available signal. Add phone_verified to the serializer for
 * a proper persistent check.
 */
const VerifyPhone = () => {
  const { user } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [code, setCode] = useState("")
  const [verifying, setVerifying] = useState(false)
  const [resending, setResending] = useState(false)
  const [verified, setVerified] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (cooldown <= 0) return
    timerRef.current = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(timerRef.current)
  }, [cooldown])

  const handleVerify = async (e) => {
    e.preventDefault()
    if (!code.trim()) {
      showToast("Enter the code sent to your phone", "error")
      return
    }
    setVerifying(true)
    try {
      await authApi.verifyPhone(code.trim())
      setVerified(true)
      sessionStorage.setItem("phone_verified_this_session", "true")
      showToast("Phone number verified!", "success")
    } catch (err) {
      const detail = err.response?.data?.detail || ""
      if (detail.toLowerCase().includes("expired")) {
        showToast("That code expired — request a new one below.", "error")
      } else if (detail.toLowerCase().includes("incorrect")) {
        showToast("Incorrect code — please try again.", "error")
      } else {
        showToast(detail || "Verification failed.", "error")
      }
    } finally {
      setVerifying(false)
    }
  }

  const handleResend = async () => {
    setResending(true)
    try {
      await authApi.resendPhoneOtp()
      showToast("A new code has been sent.", "success")
      setCooldown(RESEND_COOLDOWN_SECONDS)
    } catch (err) {
      if (err.response?.status === 429) {
        showToast(err.response.data.detail, "error")
        setCooldown(RESEND_COOLDOWN_SECONDS)
      } else {
        showToast("Could not resend code — check your connection.", "error")
      }
    } finally {
      setResending(false)
    }
  }

  if (!user?.phone_number) {
    return (
      <div className="container-app py-16 text-center">
        <p className="text-gray-500">No phone number on file — add one in Settings first.</p>
      </div>
    )
  }

  return (
    <div className="container-app py-16 max-w-md mx-auto fade-in">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card-base p-8 text-center">
        {verified ? (
          <>
            <FiCheckCircle className="mx-auto text-forest-500 mb-3" size={40} />
            <h1 className="text-xl font-bold mb-2">Phone Verified</h1>
            <p className="text-sm text-gray-500 mb-6">{user.phone_number} is now confirmed.</p>
            <button onClick={() => navigate("/dashboard")} className="btn-primary w-full">
              Continue
            </button>
          </>
        ) : (
          <>
            <FiPhone className="mx-auto text-himalaya-500 mb-3" size={32} />
            <h1 className="text-xl font-bold mb-1">Verify Your Phone</h1>
            <p className="text-sm text-gray-500 mb-6">Enter the code sent to {user.phone_number}</p>

            <form onSubmit={handleVerify} className="space-y-4">
              <input
                className="input-field text-center text-lg tracking-[0.5em]"
                placeholder="000000"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                disabled={verifying}
              />
              <button type="submit" className="btn-primary w-full" disabled={verifying}>
                {verifying ? "Verifying..." : "Verify"}
              </button>
            </form>

            <button
              onClick={handleResend}
              disabled={resending || cooldown > 0}
              className="text-sm text-himalaya-500 font-medium mt-4 disabled:text-gray-300 disabled:cursor-not-allowed"
            >
              {resending
                ? "Sending..."
                : cooldown > 0
                ? `Resend code in ${cooldown}s`
                : "Resend code"}
            </button>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default VerifyPhone