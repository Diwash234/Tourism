import authApi from "../api/authApi"
import React, { createContext, useState, useEffect } from "react"

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



  // -----------------------------
  // Check logged in user
  // -----------------------------

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


      .catch((error) => {


        console.log(
          "Auth check failed:",
          error
        )


        setUser(null)


        localStorage.removeItem("access")
        localStorage.removeItem("refresh")
        localStorage.removeItem("user")


      })


      .finally(() => {

        setLoading(false)

      })



  }, [])



  // -----------------------------
  // Normal login
  // -----------------------------

  const login = async (credentials) => {


    const { data } = await authApi.login(credentials)



    localStorage.setItem(
      "access",
      data.access
    )


    localStorage.setItem(
      "refresh",
      data.refresh
    )



    let userData = data.user



    // If backend does not send user
    // fetch profile

    if (!userData) {


      const response =
        await authApi.getCurrentUser()


      userData = response.data

    }



    localStorage.setItem(
      "user",
      JSON.stringify(userData)
    )



    setUser(userData)



    return userData


  }





  // -----------------------------
  // OAuth login
  // Google/Github
  // -----------------------------

  const loginWithTokens = async (data) => {


    localStorage.setItem(
      "access",
      data.access
    )


    localStorage.setItem(
      "refresh",
      data.refresh
    )



    let userData = data.user



    if (!userData) {


      const response =
        await authApi.getCurrentUser()


      userData = response.data

    }



    localStorage.setItem(
      "user",
      JSON.stringify(userData)
    )



    setUser(userData)



    return userData


  }






  // -----------------------------
  // Register
  // -----------------------------

  const register = async (payload) => {


    const { data } =
      await authApi.register(payload)


    return data


  }







  // -----------------------------
  // Logout
  // -----------------------------

  const logout = async () => {


    try {


      await authApi.logout()


    } catch(error) {


      console.log(
        "Logout error:",
        error
      )


    }



    localStorage.removeItem("access")
    localStorage.removeItem("refresh")
    localStorage.removeItem("user")



    setUser(null)


  }






  // -----------------------------
  // Permission checks
  // -----------------------------


  const isAuthenticated =
    !!user




  // ADMIN ONLY
  // superuser OR explicit admin role

  const isAdmin =
      user?.is_admin === true ||
      user?.is_superuser === true ||
      user?.role === "admin"





  // STAFF ONLY
  // staff but NOT admin

  const isStaff =
      user?.is_staff === true &&
      !isAdmin





  // TOURIST USER

  const isTourist =
      user?.role === "tourist"







  return (

    <AuthContext.Provider

      value={{

        user,

        setUser,


        login,

        loginWithTokens,

        register,

        logout,


        isAuthenticated,


        isAdmin,

        isStaff,

        isTourist,


        loading,


      }}

    >


      {children}


    </AuthContext.Provider>


  )

}