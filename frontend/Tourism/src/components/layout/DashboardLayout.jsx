import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"

/**
 * FIXED: this used to give the content column a hardcoded
 * `ml-60 xl:ml-64` margin to manually match the Sidebar's own
 * `fixed ... w-60 xl:w-64` width -- two separate files that both have
 * to agree on the exact same pixel value at the exact same breakpoint.
 * Any small change to one (or a third page nesting its own margin/
 * padding) could silently desync them, which is what produced the
 * "extra gap between the sidebar and the content, content pushed over
 * and having to scroll sideways/down" symptom. It also meant Footer
 * -- rendered inside that same margined column -- was indented on
 * every dashboard page instead of spanning full width like it does on
 * public (MainLayout) pages, leaving a visible dead strip under/left
 * of the sidebar.
 *
 * Now a single CSS Grid owns the two-column layout: `lg:grid-cols-[15rem_1fr]`
 * i.e. the sidebar's track width IS the content's remaining width by
 * construction, so they can never drift apart. Footer moved outside
 * the grid so it's always full-width and consistent with every other
 * page in the app, on any screen size (mobile/tablet/desktop, and any
 * in-between width from resizing/minimizing a window).
 */
const DashboardLayout = () => {
  const location = useLocation()
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 w-full">
      <Navbar />
      <div className="flex-1 w-full min-w-0 lg:grid lg:grid-cols-[15rem_1fr] xl:grid-cols-[16rem_1fr]">
        <Sidebar />
        <div key={location.pathname} className="min-w-0">
          <div className="min-w-0 px-4 sm:px-6 lg:px-8 py-6">
            <Outlet />
          </div>
        </div>
      </div>
      <Footer />
      <FloatingChatbot />
    </div>
  )
}

export default DashboardLayout