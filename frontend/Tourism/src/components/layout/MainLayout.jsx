import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import { ElevationScrollProgress } from "../common/MotionSystem"

const MainLayout = () => {
  const location = useLocation()

  return (
    <div className="flex flex-col min-h-screen w-full bg-white overflow-x-hidden">
      <ElevationScrollProgress />
      <Navbar />
      <Sidebar />
      <main
        key={location.pathname}
        className="flex-1 w-full pt-16 transition-[padding] duration-300 lg:pl-64"
      >
        <Outlet />
      </main>
      <div className="transition-[padding] duration-300 lg:pl-64">
        <Footer />
      </div>
      <FloatingChatbot />
    </div>
  )
}

export default MainLayout
