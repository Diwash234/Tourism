import { Outlet } from "react-router-dom"

/**
 * Bare chrome for login/register so Admin, Staff and Traveller portals
 * do not inherit the public traveller navbar + sidebar.
 */
export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-[var(--ny-bg)]">
      <Outlet />
    </div>
  )
}
