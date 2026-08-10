import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"

const DashboardLayout = () => {
  const location = useLocation()
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 w-full">
      <Navbar />
      <Sidebar />
      <div
        key={location.pathname}
        className="
          flex-1 w-full
          ml-0 lg:ml-60 xl:ml-64
          transition-[margin] duration-200
        "
      >
        <div className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 py-6">
          <Outlet />
        </div>
        <Footer />
      </div>
      <FloatingChatbot />
    </div>
  )
}

export default DashboardLayout
