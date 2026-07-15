import { Outlet } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"

const DashboardLayout = () => (
  <div className="flex flex-col min-h-screen bg-gray-50">
    <Navbar />
    <div className="container-app flex gap-6 py-6 flex-1 w-full">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Outlet />
      </div>
    </div>
  </div>
)

export default DashboardLayout