import { Navigate, Outlet } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

// Guards pages meant for the "local" (local guide) role only.
const LocalRoute = () => {
  const { isLocal, isAdmin, loading } = useAuth()

  if (loading) return <Loader fullScreen />
  if (!isLocal && !isAdmin) return <Navigate to="/dashboard" replace />
  return <Outlet />
}

export default LocalRoute