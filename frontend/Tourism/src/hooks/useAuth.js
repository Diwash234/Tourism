import { useContext } from "react"
import { AuthContext } from "../context/AuthContext"

const useAuth = () => useContext(AuthContext)

// Exported both ways: some components use `import useAuth from`, others use
// `import { useAuth } from`. Supporting both means a component can never fail
// the production build over import style alone.
export { useAuth }
export default useAuth