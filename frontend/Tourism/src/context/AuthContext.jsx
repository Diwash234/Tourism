import authApi from "../api/authApi"
import React, { createContext, useState, useEffect } from "react";
import { useLocation } from "react-router-dom"
import { isGuestPreview } from "../api/axiosClient"
export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const location = useLocation()
  const guestPreview = isGuestPreview() || new URLSearchParams(location.search).get("as") === "traveller"


  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user")

    try {
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  const [loading, setLoading] = useState(true)

  // "Session expired, sign in again" UX. axiosClient dispatches these when a
  // token refresh fails ("session-expired") or a stale session was silently
  // dropped while public data recovered ("session-downgraded"). "auth-logout"
  // is kept for backwards compatibility.
  const [sessionNotice, setSessionNotice] = useState(null)
  useEffect(() => {
    const onExpired = () => {
      setUser(null)
      setSessionNotice("expired")
    }
    const onDowngraded = () => {
      setUser(null)
      setSessionNotice("downgraded")
    }
    window.addEventListener("session-expired", onExpired)
    window.addEventListener("session-downgraded", onDowngraded)
    window.addEventListener("auth-logout", onExpired)
    return () => {
      window.removeEventListener("session-expired", onExpired)
      window.removeEventListener("session-downgraded", onDowngraded)
      window.removeEventListener("auth-logout", onExpired)
    }
  }, [])
  const dismissSessionNotice = () => setSessionNotice(null)


  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    if (guestPreview) {
      setLoading(false)
      return
    }

    const token = localStorage.getItem("access")

    if (!token) {
      setLoading(false)
      return
    }


    authApi
      .getCurrentUser()
      .then(({ data }) => {

        setUser(data)

        localStorage.setItem(
          "user",
          JSON.stringify(data)
        )

      })
      .catch(() => {

        setUser(null)

        localStorage.removeItem("access")
        localStorage.removeItem("refresh")
        localStorage.removeItem("user")

      })
      .finally(() => {

        setLoading(false)

      })
    }, 0)
    return () => clearTimeout(t)
  }, [guestPreview])



  const login = async (credentials) => {

    const { data } = await authApi.login(credentials)


    // Save JWT tokens from Django SimpleJWT
    localStorage.setItem(
      "access",
      data.access
    )

    localStorage.setItem(
      "refresh",
      data.refresh
    )


    /*
      If your login API returns user data,
      save it.
      Otherwise fetch current user from profile API.
    */

    let userData = data.user


    if (!userData) {

      const response = await authApi.getCurrentUser()

      userData = response.data

    }


    localStorage.setItem(
      "user",
      JSON.stringify(userData)
    )


    setUser(userData)


    return userData
  }


  // NEW: Google/GitHub OAuth callbacks return {access, refresh, user}
  // directly (see authApi.js/views_oauth.py) — same JWT pair shape as
  // login(), just not obtained via the email/password endpoint. Reuses
  // the exact same storage steps rather than duplicating them.
  const loginWithTokens = async (data) => {
    localStorage.setItem("access", data.access)
    localStorage.setItem("refresh", data.refresh)

    let userData = data.user
    if (!userData) {
      const response = await authApi.getCurrentUser()
      userData = response.data
    }

    localStorage.setItem("user", JSON.stringify(userData))
    setUser(userData)
    return userData
  }



  const register = async (payload) => {

    const { data } = await authApi.register(payload)

    return data

  }



  const logout = async () => {

    try {

      await authApi.logout()

    } catch (error) {

      console.log("Logout error:", error)

    }


    localStorage.removeItem("access")
    localStorage.removeItem("refresh")
    localStorage.removeItem("user")


    setUser(null)

  }



  const visibleUser = guestPreview ? null : user
  const isAuthenticated = !!visibleUser

  const role = String(visibleUser?.role || "").toLowerCase()
  const ADMIN_ROLES = ["admin", "super_admin", "tourism_admin"]
  const STAFF_ROLES = ["staff", "content_moderator", "district_manager", "hotel_manager", "tourist_police"]

  // Staff Django is_staff flags must NOT unlock the Admin console.
  const isAdmin = !!(visibleUser && (ADMIN_ROLES.includes(role) || visibleUser.is_superuser === true))
  const isStaff = !!(visibleUser && (STAFF_ROLES.includes(role) || isAdmin))
  const isLocal =
    (visibleUser && (role === "local" || role === "local_guide" || visibleUser.is_local === true)) ||
    isAdmin



  return (

    <AuthContext.Provider
      value={{
        user: visibleUser,
        setUser,
        login,
        loginWithTokens,
        register,
        logout,
        isAuthenticated,
        isAdmin,
        isStaff,
        isLocal,
        loading,
        sessionNotice,
        dismissSessionNotice,
      }}
    >

      {children}

      {sessionNotice && (
        <div
          role="alert"
          className="fixed bottom-4 left-1/2 z-[120] w-[min(92vw,26rem)] -translate-x-1/2 rounded-xl border border-amber-300 bg-white p-4 shadow-2xl dark:border-amber-500/40 dark:bg-slate-900"
        >
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {sessionNotice === "expired"
              ? "Your session has expired. Please sign in again."
              : "You were signed out because your session became invalid."}
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Public information remains available while you browse as a guest.
          </p>
          <div className="mt-3 flex gap-2">
            <a
              href="/login"
              onClick={dismissSessionNotice}
              className="rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-800"
            >
              Sign in
            </a>
            <button
              type="button"
              onClick={dismissSessionNotice}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Keep browsing
            </button>
          </div>
        </div>
      )}

    </AuthContext.Provider>

  )
}