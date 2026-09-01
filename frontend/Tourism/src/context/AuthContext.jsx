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


  useEffect(() => {
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
      }}
    >

      {children}

    </AuthContext.Provider>

  )
}