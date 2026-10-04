import { useEffect, Suspense } from "react"
import useSidebarState from "../../hooks/useSidebarState"
import { Outlet, useLocation } from "react-router-dom"
import useRouteSeo from "../../hooks/useRouteSeo"
import useKeyboardShortcuts from "../../hooks/useKeyboardShortcuts"
import usePublicConfig from "../../hooks/usePublicConfig"
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
import ContinuousTicker from "./ContinuousTicker"
import GlobalCtaBanner from "../cms/GlobalCtaBanner"
import GlobalActionButtons from "../common/GlobalActionButtons"
import AdmissionModal from "../common/AdmissionModal"

const MainLayout = () => {
  const [sidebarOpen] = useSidebarState()
  const desktopPad = sidebarOpen ? "lg:pl-64" : "lg:pl-16"
  const location = useLocation()
  const { settings } = usePublicConfig()

  const hasTopbar = Boolean(settings?.topbar) && settings.topbar.enabled !== false && (settings.topbar.status ? settings.topbar.status === "published" : true)
  const brandingAnnouncement = settings?.branding
  const showBrandingBar = Boolean(brandingAnnouncement?.show_announcement_bar) && Boolean((brandingAnnouncement?.announcement_bar_text || "").trim())
  // When the announcement bar is on, the fixed header stack grows by
  // the bar's height so content never hides behind it.
  const topPad = hasTopbar ? "pt-[140px]" : showBrandingBar ? "pt-24" : "pt-16"
  const announcement = settings?.announcement && typeof settings.announcement === "object" ? settings.announcement : (settings?.announcement ? { text: String(settings.announcement) } : null)
  // Settings-desk announcement bar (branding). Shown at the very top
  // when the admin enables it and provides text.
  const barText = (brandingAnnouncement?.announcement_bar_text || "").trim()
  const barColor = brandingAnnouncement?.primary_color || "#0B3D91"

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
      {/* Settings-desk announcement bar — fixed at the very top,
          above the navbar, when the admin enables it. */}
      {showBrandingBar && (
        <div
          role="status"
          aria-live="polite"
          className="fixed inset-x-0 top-0 z-[70] px-4 py-2 text-center text-xs font-bold text-white"
          style={{ background: barColor }}
        >
          {barText}
        </div>
      )}
      <Navbar />
      <Sidebar />
      {announcement && (announcement.text || announcement.html) && (
        <div role="status" aria-live="polite" className="w-full bg-emerald-900 px-4 py-2 text-center text-sm font-semibold text-emerald-50">
          {announcement.text || announcement.html}
        </div>
      )}
      <main
        id="main-content"
        key={location.pathname}
        className={`ny-app-main ny-page flex-1 w-full ${topPad} transition-[padding] duration-300 ${desktopPad}`}
      >
        <ContinuousTicker />
        <Suspense fallback={<div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite"><span className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><span className="sr-only">Loading page</span></div>}><Outlet /></Suspense>
      </main>
      <div className={`ny-footer-wrap pb-28 transition-[padding] duration-300 lg:pb-0 ${desktopPad}`}>
        <GlobalCtaBanner />
        <Footer />
      </div>
      <MobileBottomNav />
      <FloatingChatbot />
      <CookieConsentBanner />
      <ScrollToTop />
      <QuickActions />
      <GlobalActionButtons />
      <AdmissionModal />
      <KeyboardShortcutsModal />
    </div>
  )
}

export default MainLayout
