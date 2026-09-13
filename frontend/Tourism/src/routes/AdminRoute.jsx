import { Navigate, Outlet, useLocation } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

const AdminRoute = () => {
  const { isAdmin, isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Loader fullScreen />
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />
  }
  if (!isAdmin) {
    // Logged in but not an admin — send to the dashboard rather than the
    // admin login (re-logging in won't help).
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}

export default AdminRoute
