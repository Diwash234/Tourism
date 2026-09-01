import { useEffect, useState } from "react"
import { useParams, useSearchParams, useNavigate, Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiAlertCircle } from "react-icons/fi"
import authApi from "../../api/authApi"
import useAuth from "../../hooks/useAuth"
import { getRedirectUri } from "../../utils/oauth"
import TourismLogo from "../../components/branding/TourismLogo"
import NepalSceneBackground from "../../components/branding/NepalSceneBackground"

/**
 * OAuthCallback — lands here after the user approves access on
 * Google's/GitHub's consent screen (see utils/oauth.js for the
 * redirect-out half). Reads ?code= from the URL, exchanges it via the
 * backend (views_oauth.py), and logs the user in with the returned JWT
 * pair — reusing loginWithTokens() so this goes through the exact same
 * storage path as email/password login.
 *
 * Route: /auth/callback/:provider  (provider = "google" | "github")
 */
const OAuthCallback = () => {
  const { provider } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { loginWithTokens } = useAuth()

  const [status, setStatus] = useState("loading") // loading | error | cancelled
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    const code = searchParams.get("code")
    const oauthError = searchParams.get("error")

    // User clicked "Cancel" on the provider's consent screen
    if (oauthError) {
      setStatus("cancelled")
      return
    }

    if (!code) {
      setStatus("error")
      setErrorMessage("No authorization code was returned.")
      return
    }

    const exchange = async () => {
      try {
        const { data } =
          provider === "google"
            ? await authApi.googleAuthCallback(code, getRedirectUri("google"))
            : await authApi.githubAuthCallback(code)

        const userData = await loginWithTokens(data)
        const role = String(userData?.role || "").toLowerCase()
        const isAdmin = userData?.is_superuser === true || ["admin", "super_admin", "tourism_admin"].includes(role)
        const isStaff = ["staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police"].includes(role)
        navigate(isAdmin ? "/admin" : isStaff ? "/staff" : "/dashboard", { replace: true })
      } catch (err) {
        setStatus("error")
        setErrorMessage(
          err.response?.data?.detail ||
          `${provider === "google" ? "Google" : "GitHub"} sign-in failed. Please try again.`
        )
      }
    }

    exchange()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
        {status === "loading" && (
          <>
            <div className="animate-spin h-8 w-8 border-4 border-himalaya-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500">Signing you in with {provider === "google" ? "Google" : "GitHub"}...</p>
          </>
        )}

        {status === "cancelled" && (
          <>
            <FiAlertCircle className="mx-auto text-saffron-500 mb-3" size={32} />
            <h2 className="font-semibold text-lg mb-2">Sign-in cancelled</h2>
            <p className="text-sm text-gray-500 mb-5">You cancelled the {provider} sign-in — no problem.</p>
            <Link to="/login" className="btn-primary inline-block">Back to Login</Link>
          </>
        )}

        {status === "error" && (
          <>
            <FiAlertCircle className="mx-auto text-nepalred-500 mb-3" size={32} />
            <h2 className="font-semibold text-lg mb-2">Sign-in failed</h2>
            <p className="text-sm text-gray-500 mb-5">{errorMessage}</p>
            <Link to="/login" className="btn-primary inline-block">Back to Login</Link>
          </>
        )}
      </motion.div>
    </div>
  )
}

export default OAuthCallback