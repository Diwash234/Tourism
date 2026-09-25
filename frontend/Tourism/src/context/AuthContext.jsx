import authApi from "../api/authApi"
import { createContext, useState, useEffect } from "react";
import { useLocation } from "react-router-dom"
import { clearAuthStorage, isGuestPreview } from "../api/axiosClient"
export const AuthContext = createContext(null)

const ADMIN_ROLES = ["admin", "super_admin", "tourism_admin"]
const STAFF_ROLES = [
  "staff", "content_moderator", "district_manager", "hotel_manager",
  "tourist_police", "police", "hospital_staff", "rescue_team", "emergency_operator",
]

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
  const [capabilities, setCapabilities] = useState({})
  const [managedDistricts, setManagedDistricts] = useState([])

  const loadCapabilities = (userData) => {
    const role = String(userData?.role || "").toLowerCase()
    if (userData?.is_superuser || ADMIN_ROLES.includes(role)) {
      setCapabilities({})
      setManagedDistricts([])
      return Promise.resolve()
    }
    if (!userData || !STAFF_ROLES.includes(role)) {
      setCapabilities({})
      setManagedDistricts([])
      return Promise.resolve()
    }
    return authApi.getCapabilities().then(({ data }) => {
      setCapabilities(data?.capabilities || {})
      setManagedDistricts(data?.managed_districts || [])
    }).catch(() => {
      setCapabilities({})
      setManagedDistricts([])
    })
  }

  // "Session expired, sign in again" UX. axiosClient dispatches these when a
  // token refresh fails ("session-expired") or a stale session was silently
  // dropped while public data recovered ("session-downgraded"). "auth-logout"
  // is kept for backwards compatibility.
  const [sessionNotice, setSessionNotice] = useState(null)
  useEffect(() => {
    const onExpired = () => {
      setUser(null)
      setCapabilities({})
      setManagedDistricts([])
      setSessionNotice("expired")
    }
    const onDowngraded = () => {
      setUser(null)
      setCapabilities({})
      setManagedDistricts([])
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
        loadCapabilities(data)

      })
      .catch(() => {

        setUser(null)

        localStorage.removeItem("access")
        localStorage.removeItem("refresh")
        localStorage.removeItem("user")
        setCapabilities({})
        setManagedDistricts([])

      })
      .finally(() => {

        setLoading(false)

      })
    }, 0)
    return () => clearTimeout(t)
  }, [guestPreview])



  const login = async (credentials) => {
    try {
      const { data } = await authApi.login(credentials)
      const userData = data.user || (await authApi.getCurrentUser()).data
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
      loadCapabilities(userData)
      return userData
    } catch (error) {
      clearAuthStorage()
      setUser(null)
      throw error
    }
  }


  // NEW: Google/GitHub OAuth callbacks return {access, refresh, user}
  // directly (see authApi.js/views_oauth.py) — same JWT pair shape as
  // login(), just not obtained via the email/password endpoint. Reuses
  // the exact same storage steps rather than duplicating them.
  const loginWithTokens = async (data) => {
    try {
      localStorage.setItem("access", data.access)
      localStorage.setItem("refresh", data.refresh)
      const userData = data.user || (await authApi.getCurrentUser()).data
      localStorage.setItem("user", JSON.stringify(userData))
      setUser(userData)
      loadCapabilities(userData)
      return userData
    } catch (error) {
      clearAuthStorage()
      setUser(null)
      throw error
    }
  }



  const register = async (payload) => {

    const { data } = await authApi.register(payload)

    return data

  }



  const updateUser = (nextUser) => {
    setUser(nextUser)
    loadCapabilities(nextUser)
    if (nextUser) localStorage.setItem("user", JSON.stringify(nextUser))
    else localStorage.removeItem("user")
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
    setCapabilities({})
    setManagedDistricts([])


    setUser(null)

  }



  const visibleUser = guestPreview ? null : user
  const isAuthenticated = !!visibleUser

  const role = String(visibleUser?.role || "").toLowerCase()

  // Staff Django is_staff flags must NOT unlock administrative modules by
  // themselves. The server capability payload is the UI's visibility hint;
  // backend checks remain authoritative.
  const isAdmin = !!(visibleUser && (ADMIN_ROLES.includes(role) || visibleUser.is_superuser === true))
  const isStaff = !!(visibleUser && (STAFF_ROLES.includes(role) || isAdmin))
  const can = (module, action = "view") => {
    if (isAdmin) return true
    const actions = capabilities[module] || []
    return actions.includes(action) || actions.includes("*")
  }
  const isLocal =
    (visibleUser && (role === "local" || role === "local_guide" || visibleUser.is_local === true)) ||
    isAdmin

  return (

    <AuthContext.Provider
      value={{
        user: visibleUser,
        setUser,
         updateUser,
        login,
        loginWithTokens,
        register,
        logout,
        isAuthenticated,
        isAdmin,
        isStaff,
        isLocal,
        capabilities,
        managedDistricts,
        can,
        loading,
        sessionNotice,
        dismissSessionNotice,
      }}
    >

      {children}

      {sessionNotice && (
        <div
          role="alert"
          className="ny-session-notice fixed bottom-4 left-1/2 w-[min(92vw,26rem)] -translate-x-1/2 rounded-xl border border-amber-300 bg-white p-4 shadow-2xl dark:border-amber-500/40 dark:bg-slate-900"
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
              className="ny-btn ny-btn-primary min-h-11 px-3 text-xs"
            >
              Sign in
            </a>
            <button
              type="button"
              onClick={dismissSessionNotice}
              className="ny-btn ny-btn-secondary min-h-11 px-3 text-xs"
            >
              Keep browsing
            </button>
          </div>
        </div>
      )}

    </AuthContext.Provider>

  )
}