import { Navigate, Outlet } from "react-router-dom"
import useAuth from "../hooks/useAuth"
import Loader from "../components/common/Loader"

const AdminRoute = () => {
  const { isAdmin, loading } = useAuth()

  if (loading) return <Loader fullScreen />
  if (!isAdmin) return <Navigate to="/dashboard" replace />
  return <Outlet />
}

export default AdminRoute