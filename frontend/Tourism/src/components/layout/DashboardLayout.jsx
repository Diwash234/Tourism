import { Outlet, useLocation } from "react-router-dom"
import useSidebarState from "../../hooks/useSidebarState"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import MobileBottomNav from "./MobileBottomNav"
import { ElevationScrollProgress } from "../common/MotionSystem"

const DashboardLayout = () => {
  const location = useLocation()
  const [sidebarOpen] = useSidebarState()
  // The desktop rail is always present — expanded (64) or icon-only (16) —
  // so content padding must always match the visible rail width (brief §12/§24).
  const desktopPad = sidebarOpen ? "lg:pl-64" : "lg:pl-16"

  return (
    <div className="ny-app-shell flex min-h-screen w-full flex-col overflow-x-hidden bg-[var(--ny-bg)] text-[var(--ny-text)] dark:bg-[#0B1714] dark:text-[#EAF2EF]">
      <a href="#main-content" className="ny-skip-link">Skip to main content</a>
      <ElevationScrollProgress />
      <Navbar />
      <Sidebar />
      <div
        id="main-content"
        key={location.pathname}
        className={`ny-app-main ny-page flex w-full flex-1 flex-col justify-between pb-28 pt-16 transition-[padding] duration-300 lg:pb-0 ${desktopPad}`}
      >
        <div className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-6 sm:px-6 md:py-8 lg:px-8">
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
