import { createContext, useState, useEffect } from "react"
import authApi from "../api/authApi"

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {

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

  }, [])



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



  const isAuthenticated = !!user

  const isAdmin = user?.role === "admin"



  return (

    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        register,
        logout,
        isAuthenticated,
        isAdmin,
        loading,
      }}
    >

      {children}

    </AuthContext.Provider>

  )
}