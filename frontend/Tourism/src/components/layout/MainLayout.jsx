import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import { ElevationScrollProgress } from "../common/MotionSystem"
import useSidebarState from "../../hooks/useSidebarState"

const MainLayout = () => {
  const location = useLocation()
  const [collapsed] = useSidebarState()

  return (
    <div className="flex flex-col min-h-screen w-full bg-white overflow-x-hidden">
      <ElevationScrollProgress />
      <Navbar />
      <Sidebar />
      <main
        key={location.pathname}
        className={`flex-1 w-full transition-[margin] duration-300 ${
          collapsed ? "ml-0" : "ml-0 lg:ml-64"
        }`}
      >
        <Outlet />
      </main>
      <div className={`transition-[margin] duration-300 ${collapsed ? "ml-0" : "ml-0 lg:ml-64"}`}>
        <Footer />
      </div>
      <FloatingChatbot />
    </div>
  )
}

export default MainLayout
