import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import MobileBottomNav from "./MobileBottomNav"
import { ElevationScrollProgress } from "../common/MotionSystem"

const DashboardLayout = () => {
  const location = useLocation()

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 w-full overflow-x-hidden">
      <ElevationScrollProgress />
      <Navbar />
      <Sidebar />
      <div
        key={location.pathname}
        className="flex-1 w-full flex flex-col justify-between pt-16 transition-[padding] duration-300 lg:pl-64"
      >
        <div className="flex-1 min-w-0 px-3 sm:px-4 md:px-6 lg:px-8 py-5 md:py-8 max-w-[1600px] mx-auto w-full">
          <Outlet />
        </div>
        <Footer />
      </div>
      <MobileBottomNav />
      <FloatingChatbot />
    </div>
  )
}

export default DashboardLayout
