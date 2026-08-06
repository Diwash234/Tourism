import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import HimalAI from "../../Chatbot"

const MainLayout = () => {
  const location = useLocation()
  return (
    <div className="flex flex-col min-h-screen w-full">
      <Navbar />
      <Sidebar />
      <main
        key={location.pathname}
        className="
          flex-1 w-full
          ml-0 lg:ml-60 xl:ml-64
          transition-[margin] duration-200
        "
      >
        <Outlet />
      </main>
      <div className="ml-0 lg:ml-60 xl:ml-64 transition-[margin] duration-200">
        <Footer />
      </div>
      <HimalAI />
    </div>
  )
}

export default MainLayout
