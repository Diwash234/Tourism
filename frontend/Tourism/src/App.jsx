import { lazy, Suspense, useEffect } from "react"
import { Routes, Route, Navigate } from "react-router-dom"
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
import Landing from "./pages/Landing"
import About from "./pages/About"
import DynamicCMSPage from "./pages/DynamicCMSPage"
import Contact from "./pages/Contact"
import HowItWorks from "./pages/HowItWorks"
import PrivacyPolicy from "./pages/PrivacyPolicy"
import TermsOfService from "./pages/TermsOfService"
import CustomerSupport from "./pages/CustomerSupport"
import ThankYou from "./pages/ThankYou"
import NotFound from "./pages/NotFound"

// Authentication
import Login from "./pages/auth/Login"
import UserLogin from "./pages/auth/UserLogin"
import StaffLogin from "./pages/auth/StaffLogin"
import AdminLogin from "./pages/auth/AdminLogin"
import Register from "./pages/auth/Register"
import ForgotPassword from "./pages/auth/ForgotPassword"
import VerifyEmail from "./pages/auth/VerifyEmail"
import ResetPassword from "./pages/auth/ResetPassword"
import OAuthCallback from "./pages/auth/OAuthCallback"
import VerifyPhone from "./pages/VerifyPhone"

// Destination Pages
import DestinationList from "./pages/destinations/DestinationList"
import DestinationDetails from "./pages/destinations/DestinationDetails"
import SubmitPlacePage from "./pages/SubmitPlacePage"
import SubmitServicePage from "./pages/SubmitServicePage"
import DiscoverNepal from "./pages/DiscoverNepal"
const ExploreNepalMap = lazy(() => import("./pages/ExploreNepalMap"))
const DistrictsIndex = lazy(() => import("./pages/DistrictsIndex"))
const DistrictDetail = lazy(() => import("./pages/DistrictDetail"))
import CompareDestinations from "./pages/CompareDestinations"
import Gallery from "./pages/Gallery"

// Features
import Chatbot from "./Chatbot"
import MyBooking from "./MyBookings"
import BookHotel from "./BookHotel"

// User Dashboard Pages
import Dashboard from "./pages/Dashboard"
import Profile from "./pages/Profile"
import Recommendation from "./pages/Recommendation"
import BudgetEstimator from "./pages/BudgetEstimator"
import RiskAlertDashboard from "./pages/RiskAlertDashboard"
import Hotels from "./pages/Hotels"
import HotelSearch from "./pages/HotelSearch"
const Navigation = lazy(() => import("./pages/Navigation"))
const DistancesExplorer = lazy(() => import("./pages/DistancesExplorer"))
const TravelPlanner = lazy(() => import("./pages/TravelPlanner"))
import Language from "./pages/Language"
import Emergency from "./pages/Emergency"
import NearbyPlaces from "./pages/NearbyPlaces"
import Translation from "./pages/Translation"
import Settings from "./pages/Settings"
import Favorites from "./pages/Favorites"
import History from "./pages/History"
import Notifications from "./pages/Notifications"
import Expenditure from "./pages/Expenditure"
import MySubmissions from "./pages/MySubmissions"
import StaffDashboard from "./pages/StaffDashboard"
const Itinerary = lazy(() => import("./pages/Itinerary"))
const BeforeYouTravel = lazy(() => import("./pages/BeforeYouTravel"))
import FamilySafety from "./pages/FamilySafety"
import SharedTripView from "./pages/SharedTripView"

// New Features (Remote Repository Updates)
import Packages from "./pages/Packages"
import Guides from "./pages/Guides"
import GuidePortal from "./pages/GuidePortal"
import TourismJobs from "./pages/TourismJobs"
import GuideBookings from "./pages/GuideBookings"
import PackageDetail from "./pages/PackageDetail"
import Collaborate from "./pages/Collaborate"
import Checkout from "./pages/Checkout"
import PartnerDesk from "./pages/PartnerDesk"
import TripStatus from "./pages/TripStatus"
// TripPlanner was merged into Itinerary (single dataset-driven planner).
// The old /trip-planner route now redirects to /itinerary below.
import PersonalDetails from "./pages/PersonalDetails"
import LocalDashboard from "./pages/local/LocalDashboard"
import LocalRoute from "./routes/LocalRoute"

// Admin
// Heavy, low-traffic surfaces are code-split (register DEF-013): admin
// console, maps, navigation and planners load as separate chunks.
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"))
import AdminLayout from "./components/admin/AdminLayout"
import StaffLayout from "./components/admin/StaffLayout"
const DiagnosticsCenter = lazy(() => import("./pages/admin/DiagnosticsCenter"))
const HotelAssignments = lazy(() => import("./pages/admin/HotelAssignments"))
const AdminTasks = lazy(() => import("./pages/admin/Tasks"))

const RouteLoading = () => (
  <div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite">
    <div className="text-center"><span className="mx-auto block h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><p className="mt-3 text-sm text-[var(--ny-text-secondary)]">Loading this part of your journey…</p></div>
  </div>
)

const LazyRoute = ({ children }) => <Suspense fallback={<RouteLoading />}>{children}</Suspense>


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
      <RedirectRules />
      <CommandPalette />
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-emerald-300">Loading…</div>}>
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
        {/* The emailed links point here — these routes were missing, so
            verification / password-reset links dead-ended (Round 21 fix). */}
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/auth/callback/:provider" element={<OAuthCallback />} />
      </Route>

      {/* Public traveller chrome */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/page/:slug" element={<DynamicCMSPage />} />
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
        <Route path="/districts" element={<LazyRoute><DistrictsIndex /></LazyRoute>} />
        <Route path="/districts/:districtName" element={<LazyRoute><DistrictDetail /></LazyRoute>} />
        <Route path="/compare" element={<CompareDestinations />} />
        <Route path="/destinations/compare" element={<CompareDestinations />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/itinerary" element={<LazyRoute><Itinerary /></LazyRoute>} />
        <Route path="/trip-planner" element={<Navigate to="/itinerary" replace />} />
        <Route path="/packages" element={<Packages />} />
        <Route path="/recommendation" element={<Recommendation />} />
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
        {/* Public planning and safety tools. These pages keep their existing
            data contracts but do not require an account to open. */}
        <Route path="/budget-estimator" element={<BudgetEstimator />} />
        <Route path="/before-you-travel" element={<LazyRoute><BeforeYouTravel /></LazyRoute>} />
        <Route path="/risk-alerts" element={<RiskAlertDashboard />} />
        <Route path="/navigation" element={<LazyRoute><Navigation /></LazyRoute>} />
        <Route path="/distances" element={<LazyRoute><DistancesExplorer /></LazyRoute>} />
        <Route path="/language" element={<Language />} />
        <Route path="/nearby-places" element={<NearbyPlaces />} />
        <Route path="/translation" element={<Translation />} />
        <Route path="/discover-nepal" element={<DiscoverNepal />} />
        <Route path="/explore-map" element={<LazyRoute><ExploreNepalMap /></LazyRoute>} />
        <Route path="/hotels/search" element={<HotelSearch />} />
        {/* Travel planner — real routes between any two destinations (public) */}
        <Route path="/travel" element={<LazyRoute><TravelPlanner /></LazyRoute>} />
      </Route>


      {/* Protected User Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/personal-details" element={<PersonalDetails />} />
          <Route path="/verify-phone" element={<VerifyPhone />} />
          <Route path="/hotels" element={<Hotels />} />
          <Route path="/destinations/submit" element={<SubmitPlacePage />} />
          <Route path="/submit-service" element={<SubmitServicePage />} />

          <Route path="/family-safety" element={<FamilySafety />} />
          <Route path="/safety" element={<FamilySafety />} />

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

      {/* Local Guide Routes */}
      <Route element={<LocalRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/local/dashboard" element={<LocalDashboard />} />
          </Route>
        </Route>


      {/* Admin Routes */}
      <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route 
              path="/admin" 
              element={<LazyRoute><AdminDashboard /></LazyRoute>}
            />
            <Route path="/admin/hotel-assignments" element={<LazyRoute><HotelAssignments /></LazyRoute>} />
            <Route path="/admin/tasks" element={<LazyRoute><AdminTasks /></LazyRoute>} />
            <Route path="/admin/diagnostics" element={<LazyRoute><DiagnosticsCenter /></LazyRoute>} />
          </Route>
        </Route>


      {/* 404 Page — wrapped in MainLayout for consistent Navbar + Footer */}
      <Route element={<MainLayout />}>
        <Route path="*" element={<NotFound />} />
      </Route>

      </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}


export default App