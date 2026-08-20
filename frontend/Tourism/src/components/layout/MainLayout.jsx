import { useEffect } from "react"
import { Outlet, useLocation } from "react-router-dom"
import Navbar from "./Navbar"
import Sidebar from "./Sidebar"
import Footer from "./Footer"
import FloatingChatbot from "../common/FloatingChatbot"
import { ElevationScrollProgress } from "../common/MotionSystem"
import usePublicConfig from "../../hooks/usePublicConfig"

const setMeta = (attr, key, value) => {
  if (!value) return
  let element = document.querySelector(`meta[${attr}="${key}"]`)
  if (!element) {
    element = document.createElement("meta")
    element.setAttribute(attr, key)
    document.head.appendChild(element)
  }
  element.setAttribute("content", value)
}

const MainLayout = () => {
  const location = useLocation()
  const { pages, branding } = usePublicConfig()

  useEffect(() => {
    const page = (pages || []).find(item => item.route === location.pathname)
    const title = page?.seo_title || page?.title || branding?.site_title
    if (title) document.title = title
    if (page?.meta_description) setMeta("name", "description", page.meta_description)
    if (page?.og_image_url) setMeta("property", "og:image", page.og_image_url)
    if (page?.search_visible === false) setMeta("name", "robots", "noindex,nofollow")
    else document.querySelector('meta[name="robots"]')?.remove()
  }, [location.pathname, pages, branding])

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
