import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { FiCheckCircle, FiXCircle, FiLoader } from "react-icons/fi"
import { motion } from "framer-motion"
import authApi from "../../api/authApi"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/Nepalscenebackground"

/**
 * VerifyEmail — reached from the email link the backend sends after
 * registration: /verify-email?token=<uuid>.
 *
 * FIX: this page did not exist. The backend emails
 * `/verify-email?token=...` but there was no route/page for it, so
 * newly registered users could never verify their email address.
 */
const VerifyEmail = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token")

  const [status, setStatus] = useState("verifying") // verifying | success | error
  const [message, setMessage] = useState("")

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setMessage("This verification link is missing its token.")
      return
    }

    let cancelled = false
    authApi
      .verifyEmail(token)
      .then(() => {
        if (!cancelled) {
          setStatus("success")
          setMessage("Your email has been verified successfully.")
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus("error")
          setMessage(
            err?.response?.data?.detail ||
              "This link is invalid or has expired. Please request a new one."
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden">
      <NepalSceneBackground />
      <div className="relative z-10 mb-6 bg-white/90 backdrop-blur px-4 py-2 rounded-xl">
        <TourismLogo size="sm" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 card-base w-full max-w-md p-8 text-center"
      >
        {status === "verifying" && (
          <>
            <FiLoader className="mx-auto text-amber-500 text-5xl mb-4 animate-spin" />
            <h1 className="text-2xl font-bold mb-2">Verifying your email…</h1>
            <p className="text-sm text-gray-500">Please wait a moment.</p>
          </>
        )}

        {status === "success" && (
          <>
            <FiCheckCircle className="mx-auto text-green-500 text-5xl mb-4" />
            <h1 className="text-2xl font-bold mb-2">Email Verified!</h1>
            <p className="text-sm text-gray-500 mb-6">{message}</p>
            <Link
              to="/login"
              className="inline-block w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold text-center hover:opacity-90 transition"
            >
              Go to Login
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <FiXCircle className="mx-auto text-red-500 text-5xl mb-4" />
            <h1 className="text-2xl font-bold mb-2">Verification Failed</h1>
            <p className="text-sm text-gray-500 mb-6">{message}</p>
            <Link
              to="/login"
              className="inline-block w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold text-center hover:opacity-90 transition"
            >
              Back to Login
            </Link>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default VerifyEmail
