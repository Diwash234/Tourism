import { Navigate, Outlet, useLocation } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

// Guards pages meant for the "local" (local guide) role only.
const LocalRoute = () => {
  const { isLocal, isAdmin, isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Loader fullScreen />
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />
  if (!isLocal && !isAdmin) return <Navigate to="/dashboard" replace />
  return <Outlet />
}

export default LocalRoute