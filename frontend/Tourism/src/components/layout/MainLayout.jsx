import { useEffect, Suspense } from "react"
import useSidebarState from "../../hooks/useSidebarState"
import { Outlet, useLocation } from "react-router-dom"
import useRouteSeo from "../../hooks/useRouteSeo"
import useKeyboardShortcuts from "../../hooks/useKeyboardShortcuts"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import CookieConsentBanner from "../common/CookieConsentBanner"
import MobileBottomNav from "./MobileBottomNav"
import ScrollToTop from "../common/ScrollToTop"
import KeyboardShortcutsModal from "../common/KeyboardShortcutsModal"
import QuickActions from "../common/QuickActions"
import ReadingProgress from "../common/ReadingProgress"
import { ElevationScrollProgress } from "../common/MotionSystem"


const MainLayout = () => {
  const [sidebarOpen] = useSidebarState()
  const desktopPad = sidebarOpen ? "lg:pl-64" : "lg:pl-16"
  const location = useLocation()

  useRouteSeo()
  useKeyboardShortcuts()

  // Scroll to top on route change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" })
  }, [location.pathname])

  return (
    <div className="ny-app-shell flex min-h-screen w-full flex-col overflow-x-hidden bg-[var(--ny-bg)] text-[var(--ny-text)] dark:bg-[#0B1714] dark:text-[#EAF2EF]">
      <a href="#main-content" className="ny-skip-link">Skip to main content</a>
      <ElevationScrollProgress />
      <ReadingProgress />
      <Navbar />
      <Sidebar />
      <main
        id="main-content"
        key={location.pathname}
        className={`ny-app-main ny-page flex-1 w-full pt-16 transition-[padding] duration-300 ${desktopPad}`}
      >
        <Suspense fallback={<div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite"><span className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><span className="sr-only">Loading page</span></div>}><Outlet /></Suspense>
      </main>
      <div className={`ny-footer-wrap pb-28 transition-[padding] duration-300 lg:pb-0 ${desktopPad}`}>
        <Footer />
      </div>
      <MobileBottomNav />
      <FloatingChatbot />
      <CookieConsentBanner />
      <ScrollToTop />
      <QuickActions />
      <KeyboardShortcutsModal />
    </div>
  )
}

export default MainLayout
