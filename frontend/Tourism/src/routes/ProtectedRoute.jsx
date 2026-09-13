import { Navigate, Outlet, useLocation } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

const ProtectedRoute = () => {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Loader fullScreen />
  if (!isAuthenticated) {
    // Admin CMS previews render public pages inside an iframe (?as=traveller).
    // Never redirect an iframe to /login — it confuses admins ("logged out")
    // and can clobber the parent tab's session. Show a notice instead.
    if (typeof window !== "undefined" && window.self !== window.top) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-8">
          <div className="max-w-sm rounded-2xl border border-slate-200 bg-white p-6 text-center shadow">
            <p className="font-black text-slate-900">This page needs a traveller login</p>
            <p className="mt-2 text-sm text-slate-500">
              Admin previews show public pages. Open this route in the live site
              while signed in to see it, or preview a public page here.
            </p>
          </div>
        </div>
      )
    }
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <Outlet />
}

export default ProtectedRoute