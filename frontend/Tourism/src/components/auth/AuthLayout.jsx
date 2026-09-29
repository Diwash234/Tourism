import { Suspense } from "react"
import { Outlet } from "react-router-dom"
import useRouteSeo from "../../hooks/useRouteSeo"

/**
 * Bare chrome for login/register so Admin, Staff and Traveller portals
 * do not inherit the public traveller navbar + sidebar.
 */
export default function AuthLayout() {
  useRouteSeo()
  return (
    <div className="min-h-screen bg-[var(--ny-bg)]">
      <Suspense fallback={<div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite"><span className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><span className="sr-only">Loading page</span></div>}><Outlet /></Suspense>
    </div>
  )
}
