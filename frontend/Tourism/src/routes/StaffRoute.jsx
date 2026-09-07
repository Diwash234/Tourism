import { Navigate, Outlet, useLocation } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

const StaffRoute = () => {
  const { isStaff, isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Loader fullScreen />
  if (!isAuthenticated) {
    return <Navigate to="/staff/login" state={{ from: location }} replace />
  }
  if (!isStaff) {
    return <Navigate to="/dashboard" replace />
  }
  return <Outlet />
}

export default StaffRoute
