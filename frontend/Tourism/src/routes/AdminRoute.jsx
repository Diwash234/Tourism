import { Navigate, Outlet, useLocation } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"
import { canAccessAdminSection } from "../components/admin/adminNavigation"

const AdminRoute = () => {
  const { isAdmin, isStaff, isAuthenticated, loading, can } = useAuth()
  const location = useLocation()
  const requestedSection = new URLSearchParams(location.search).get("section")

  if (loading) return <Loader fullScreen />
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />
  }
  if (!isAdmin && !isStaff) {
    // Logged in but not an admin — send to the dashboard rather than the
    // admin login (re-logging in won't help).
    return <Navigate to="/dashboard" replace />
  }
  if (requestedSection && !canAccessAdminSection(requestedSection, can)) {
    return <Navigate to="/admin?section=overview" replace />
  }
  return <Outlet />
}

export default AdminRoute
