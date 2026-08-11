import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import useSidebarState from "../../hooks/useSidebarState"

const DashboardLayout = () => {
  const location = useLocation()
  const [collapsed] = useSidebarState()

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 w-full overflow-x-hidden">
      <Navbar />
      <Sidebar />
      <div
        key={location.pathname}
        className={`flex-1 w-full flex flex-col justify-between transition-[margin] duration-300 ${
          collapsed ? "ml-0" : "ml-0 lg:ml-64"
        }`}
      >
        <div className="flex-1 min-w-0 px-3 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full">
          <Outlet />
        </div>
        <Footer />
      </div>
      <FloatingChatbot />
    </div>
  )
}

export default DashboardLayout
