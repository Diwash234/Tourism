import { useEffect, lazy, Suspense } from "react"
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom"
import usePublicConfig from "./hooks/usePublicConfig"
import ErrorBoundary from "./components/common/ErrorBoundary"
import { installGlobalErrorHandlers } from "./utils/errorLogger"
import CommandPalette from "./components/common/CommandPalette"

// Layouts
import MainLayout from "./components/layout/MainLayout"
import DashboardLayout from "./components/layout/DashboardLayout"
import AuthLayout from "./components/auth/AuthLayout"
import ScrollToTop from "./components/layout/ScrollToTop"
import RedirectRules from "./components/layout/RedirectRules"

// Route Guards
import ProtectedRoute from "./routes/ProtectedRoute"
import AdminRoute from "./routes/AdminRoute"
import StaffRoute from "./routes/StaffRoute"

// Public Pages
const Landing = lazy(() => import("./pages/Landing"))
const About = lazy(() => import("./pages/About"))
const Contact = lazy(() => import("./pages/Contact"))
const HowItWorks = lazy(() => import("./pages/HowItWorks"))
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"))
const TermsOfService = lazy(() => import("./pages/TermsOfService"))
const CustomerSupport = lazy(() => import("./pages/CustomerSupport"))
const ThankYou = lazy(() => import("./pages/ThankYou"))
const NotFound = lazy(() => import("./pages/NotFound"))
const DynamicCMSPage = lazy(() => import("./pages/DynamicCMSPage"))

// Authentication
const Login = lazy(() => import("./pages/auth/Login"))
const UserLogin = lazy(() => import("./pages/auth/UserLogin"))
const StaffLogin = lazy(() => import("./pages/auth/StaffLogin"))
const AdminLogin = lazy(() => import("./pages/auth/AdminLogin"))
const Register = lazy(() => import("./pages/auth/Register"))
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"))
const OAuthCallback = lazy(() => import("./pages/auth/OAuthCallback"))
const VerifyPhone = lazy(() => import("./pages/VerifyPhone"))

// Destination Pages
const DestinationList = lazy(() => import("./pages/destinations/DestinationList"))
const DestinationDetails = lazy(() => import("./pages/destinations/DestinationDetails"))
const SubmitPlacePage = lazy(() => import("./pages/SubmitPlacePage"))
const SubmitServicePage = lazy(() => import("./pages/SubmitServicePage"))
const DiscoverNepal = lazy(() => import("./pages/DiscoverNepal"))
const Districts = lazy(() => import("./pages/Districts"))
const DistrictDetail = lazy(() => import("./pages/DistrictDetail"))
const ExploreNepalMap = lazy(() => import("./pages/ExploreNepalMap"))
const CompareDestinations = lazy(() => import("./pages/CompareDestinations"))
const Gallery = lazy(() => import("./pages/Gallery"))

// Features
import Chatbot from "./Chatbot"
import MyBooking from "./MyBookings"
import BookHotel from "./BookHotel"

// User Dashboard Pages
const Dashboard = lazy(() => import("./pages/Dashboard"))
const Profile = lazy(() => import("./pages/Profile"))
const Recommendation = lazy(() => import("./pages/Recommendation"))
const BudgetEstimator = lazy(() => import("./pages/BudgetEstimator"))
const RiskAlertDashboard = lazy(() => import("./pages/RiskAlertDashboard"))
const Hotels = lazy(() => import("./pages/Hotels"))
const HotelSearch = lazy(() => import("./pages/HotelSearch"))
const Navigation = lazy(() => import("./pages/Navigation"))
const Language = lazy(() => import("./pages/Language"))
const Emergency = lazy(() => import("./pages/Emergency"))
const NearbyPlaces = lazy(() => import("./pages/NearbyPlaces"))
const Translation = lazy(() => import("./pages/Translation"))
const Settings = lazy(() => import("./pages/Settings"))
const Favorites = lazy(() => import("./pages/Favorites"))
const History = lazy(() => import("./pages/History"))
const Notifications = lazy(() => import("./pages/Notifications"))
const Expenditure = lazy(() => import("./pages/Expenditure"))
const MySubmissions = lazy(() => import("./pages/MySubmissions"))
const StaffDashboard = lazy(() => import("./pages/StaffDashboard"))
const Itinerary = lazy(() => import("./pages/Itinerary"))
const FamilySafety = lazy(() => import("./pages/FamilySafety"))
const SharedTripView = lazy(() => import("./pages/SharedTripView"))

// New Features (Remote Repository Updates)
const Packages = lazy(() => import("./pages/Packages"))
const Guides = lazy(() => import("./pages/Guides"))
const GuidePortal = lazy(() => import("./pages/GuidePortal"))
const TourismJobs = lazy(() => import("./pages/TourismJobs"))
const GuideBookings = lazy(() => import("./pages/GuideBookings"))
const PackageDetail = lazy(() => import("./pages/PackageDetail"))
const Collaborate = lazy(() => import("./pages/Collaborate"))
const Checkout = lazy(() => import("./pages/Checkout"))
const PartnerDesk = lazy(() => import("./pages/PartnerDesk"))
const TripStatus = lazy(() => import("./pages/TripStatus"))
// TripPlanner was merged into Itinerary (single dataset-driven planner).
// The old /trip-planner route now redirects to /itinerary below.
const PersonalDetails = lazy(() => import("./pages/PersonalDetails"))
const LocalDashboard = lazy(() => import("./pages/local/LocalDashboard"))
import LocalRoute from "./routes/LocalRoute"

// Admin
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"))
import AdminLayout from "./components/admin/AdminLayout"
import StaffLayout from "./components/admin/StaffLayout"
const DiagnosticsCenter = lazy(() => import("./pages/admin/DiagnosticsCenter"))
const HotelAssignments = lazy(() => import("./pages/admin/HotelAssignments"))
const AdminTasks = lazy(() => import("./pages/admin/Tasks"))


// Admin-managed URL redirects (RedirectRule) arrive through the public config;
// this moves visitors off renamed/retired URLs with no redeploy (spec §17).
function RedirectHandler() {
  const config = usePublicConfig()
  const navigate = useNavigate()
  useEffect(() => {
    const path = window.location.pathname
    const hit = (config.redirects || []).find((r) => String(r.old_path || "").toLowerCase() === path.toLowerCase())
    if (!hit?.new_path) return
    if (/^https?:\/\//i.test(hit.new_path)) window.location.replace(hit.new_path)
    else navigate(hit.new_path, { replace: true })
  }, [config.redirects, navigate])
  return null
}


// Per-route SEO: applies ManagedPage seo_title / meta_description / og_image
// (already exposed by the public config API) to the live document head.
function RouteSEO() {
  const { pathname } = useLocation()
  const { pages } = usePublicConfig()
  useEffect(() => {
    const page = (pages || []).find((p) => p.route === pathname)
    if (!page) return
    const t = page.seo_title || page.title
    if (t) document.title = `${t} | Nepal Yatra`
    const setMeta = (selector, attr, key, val) => {
      if (!val) return
      let el = document.head.querySelector(selector)
      if (!el) { el = document.createElement("meta"); el.setAttribute(attr, key); document.head.appendChild(el) }
      el.setAttribute("content", val)
    }
    setMeta('meta[name="description"]', "name", "description", page.meta_description)
    setMeta('meta[property="og:title"]', "property", "og:title", t)
    setMeta('meta[property="og:description"]', "property", "og:description", page.meta_description)
    setMeta('meta[property="og:image"]', "property", "og:image", page.og_image_url)
  }, [pathname, pages])
  return null
}

function App() {
  useEffect(() => {
    installGlobalErrorHandlers()
    const importInterceptor = async () => {
      try {
        const { default: axiosClient } = await import("./api/axiosClient")
        axiosClient.interceptors.response.use(
          (resp) => {
            const rid = resp.headers?.["x-request-id"]
            if (rid) window.__LAST_REQUEST_ID__ = rid
            return resp
          },
          (err) => {
            const rid = err.response?.headers?.["x-request-id"]
            if (rid) window.__LAST_REQUEST_ID__ = rid
            return Promise.reject(err)
          },
        )
      } catch { /* OAuth import interceptor is best-effort; app works without it */ }
    }
    importInterceptor()
  }, [])
  return (
    <ErrorBoundary name="App">
      <ScrollToTop />
      <RouteSEO />
      <RedirectRules />
      <CommandPalette />
      <RedirectHandler />
      <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><span className="animate-pulse text-sm text-gray-400">Loading Nepal Yatra…</span></div>}>
      <Routes>

      {/* Auth portals — no traveller navbar/sidebar so Admin, Staff and Traveller look different */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<UserLogin />} />
        <Route path="/login/user" element={<UserLogin />} />
        <Route path="/staff/login" element={<StaffLogin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/portal" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/auth/callback/:provider" element={<OAuthCallback />} />
      </Route>

      {/* Public traveller chrome */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/support" element={<CustomerSupport />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/knowledge-base" element={<HowItWorks />} />
        <Route path="/thank-you" element={<ThankYou />} />

        {/* Destinations */}
        <Route path="/destinations" element={<DestinationList />} />
        <Route path="/destinations/:slug" element={<DestinationDetails />} />
        <Route path="/compare" element={<CompareDestinations />} />
        <Route path="/destinations/compare" element={<CompareDestinations />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/itinerary" element={<Itinerary />} />
        <Route path="/trip-planner" element={<Navigate to="/itinerary" replace />} />
        <Route path="/packages" element={<Packages />} />
        <Route path="/guides" element={<Guides />} />
        <Route path="/guide-portal" element={<GuidePortal />} />
        <Route path="/tourism-jobs" element={<TourismJobs />} />
        <Route path="/guide-bookings" element={<GuideBookings />} />
        <Route path="/packages/:slug" element={<PackageDetail />} />
        <Route path="/collaborate" element={<Collaborate />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/trip/:reference?" element={<TripStatus />} />
        <Route path="/trip" element={<TripStatus />} />

        <Route path="/chatbot" element={<Chatbot />} />

        {/* Public Emergency */}
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/safety/shared/:token" element={<SharedTripView />} />
      </Route>


      {/* Protected User Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/personal-details" element={<PersonalDetails />} />
          <Route path="/verify-phone" element={<VerifyPhone />} />
          <Route path="/hotels" element={<Hotels />} />
          {/* Dedicated search endpoint (richer data: image_url, destination_name) */}
          <Route path="/hotels/search" element={<HotelSearch />} />
          <Route path="/destinations/submit" element={<SubmitPlacePage />} />
          <Route path="/submit-service" element={<SubmitServicePage />} />
          <Route path="/discover-nepal" element={<DiscoverNepal />} />
          <Route path="/districts" element={<Districts />} />
          <Route path="/districts/:slug" element={<DistrictDetail />} />
          <Route path="/explore-map" element={<ExploreNepalMap />} />

          <Route 
            path="/recommendation" 
            element={<Recommendation />} 
          />

          <Route 
            path="/budget-estimator" 
            element={<BudgetEstimator />} 
          />

          <Route 
            path="/risk-alerts" 
            element={<RiskAlertDashboard />} 
          />

          <Route path="/family-safety" element={<FamilySafety />} />
          <Route path="/safety" element={<FamilySafety />} />

          <Route path="/navigation" element={<Navigation />} />
          <Route path="/language" element={<Language />} />

          <Route 
            path="/nearby-places" 
            element={<NearbyPlaces />} 
          />

          <Route 
            path="/translation" 
            element={<Translation />} 
          />

          <Route path="/settings" element={<Settings />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/history" element={<History />} />
          <Route path="/expenditure" element={<Expenditure />} />
          <Route path="/my-submissions" element={<MySubmissions />} />

          <Route
            path="/hotels/:hotelId/book"
            element={<BookHotel />}
          />

          <Route
            path="/my-bookings"
            element={<MyBooking />}
          />
          <Route path="/partner" element={<PartnerDesk />} />

          <Route
            path="/notifications"
            element={<Notifications />}
          />
        </Route>
      </Route>

      {/* Staff-only Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<StaffRoute />}>
          <Route element={<StaffLayout />}>
            <Route path="/staff" element={<StaffDashboard module="dashboard" />} />
            <Route path="/staff/destinations" element={<StaffDashboard module="destinations" />} />
            <Route path="/staff/images" element={<StaffDashboard module="images" />} />
            <Route path="/staff/budget" element={<StaffDashboard module="budget" />} />
            <Route path="/staff/safety" element={<StaffDashboard module="safety" />} />
            <Route path="/staff/reviews" element={<StaffDashboard module="reviews" />} />
            <Route path="/staff/hotels" element={<StaffDashboard module="hotels" />} />
            <Route path="/staff/restaurants" element={<StaffDashboard module="restaurants" />} />
            <Route path="/staff/transportation" element={<StaffDashboard module="transportation" />} />
            <Route path="/staff/travel-plans" element={<StaffDashboard module="travel_plans" />} />
            <Route path="/staff/content" element={<StaffDashboard module="content" />} />
            <Route path="/staff/feedback" element={<StaffDashboard module="feedback" />} />
          </Route>
        </Route>
      </Route>

      {/* Local Guide Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<LocalRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/local/dashboard" element={<LocalDashboard />} />
          </Route>
        </Route>
      </Route>


      {/* Admin Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route 
              path="/admin" 
              element={<AdminDashboard />} 
            />
            <Route path="/admin/hotel-assignments" element={<HotelAssignments />} />
            <Route path="/admin/tasks" element={<AdminTasks />} />
            <Route path="/admin/diagnostics" element={<DiagnosticsCenter />} />
          </Route>
        </Route>
      </Route>


      {/* 404 Page — wrapped in MainLayout for consistent Navbar + Footer */}
      <Route element={<MainLayout />}>
        <Route path="/page/:slug" element={<DynamicCMSPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>

      </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}


export default App