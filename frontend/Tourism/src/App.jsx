import { lazy, Suspense, useEffect } from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import ErrorBoundary from "./components/common/ErrorBoundary"
import { installGlobalErrorHandlers } from "./utils/errorLogger"
import CommandPalette from "./components/common/CommandPalette"
import OfflineBanner from "./components/common/OfflineBanner"
import axiosClient from "./api/axiosClient"

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
const About = lazy(() => import("./pages/About"))
const DynamicCMSPage = lazy(() => import("./pages/DynamicCMSPage"))
const Contact = lazy(() => import("./pages/Contact"))
const HowItWorks = lazy(() => import("./pages/HowItWorks"))
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"))
const TermsOfService = lazy(() => import("./pages/TermsOfService"))
const CookiePolicy = lazy(() => import("./pages/CookiePolicy"))
const DataDeletion = lazy(() => import("./pages/DataDeletion"))
const Unsubscribe = lazy(() => import("./pages/Unsubscribe"))
const CustomerSupport = lazy(() => import("./pages/CustomerSupport"))
const ThankYou = lazy(() => import("./pages/ThankYou"))
const NotFound = lazy(() => import("./pages/NotFound"))
const TravelGuide = lazy(() => import("./pages/TravelGuide"))

// Authentication
const Login = lazy(() => import("./pages/auth/Login"))
const UserLogin = lazy(() => import("./pages/auth/UserLogin"))
const StaffLogin = lazy(() => import("./pages/auth/StaffLogin"))
const AdminLogin = lazy(() => import("./pages/auth/AdminLogin"))
const Register = lazy(() => import("./pages/auth/Register"))
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"))
const VerifyEmail = lazy(() => import("./pages/auth/VerifyEmail"))
const ResetPassword = lazy(() => import("./pages/auth/ResetPassword"))
const OAuthCallback = lazy(() => import("./pages/auth/OAuthCallback"))
const VerifyPhone = lazy(() => import("./pages/VerifyPhone"))

// Destination Pages
const DestinationList = lazy(() => import("./pages/destinations/DestinationList"))
const DestinationDetails = lazy(() => import("./pages/destinations/DestinationDetails"))
const SubmitPlacePage = lazy(() => import("./pages/SubmitPlacePage"))
const SubmitServicePage = lazy(() => import("./pages/SubmitServicePage"))
const DiscoverNepal = lazy(() => import("./pages/DiscoverNepal"))
const SearchPage = lazy(() => import("./pages/SearchPage"))
const DiscoverPage = lazy(() => import("./pages/DiscoverPage"))
const DecidePage = lazy(() => import("./pages/DecidePage"))
const SharedPlanPage = lazy(() => import("./pages/SharedPlanPage"))
const ExploreNepalMap = lazy(() => import("./pages/ExploreNepalMap"))
const DistrictsIndex = lazy(() => import("./pages/DistrictsIndex"))
const DistrictDetail = lazy(() => import("./pages/DistrictDetail"))
const CompareDestinations = lazy(() => import("./pages/CompareDestinations"))
const Gallery = lazy(() => import("./pages/Gallery"))
const TravelToolkit = lazy(() => import("./pages/TravelToolkit"))

// Features
const Chatbot = lazy(() => import("./Chatbot"))
const MyBooking = lazy(() => import("./MyBookings"))
const BookHotel = lazy(() => import("./BookHotel"))

// User Dashboard Pages
const Dashboard = lazy(() => import("./pages/Dashboard"))
const Profile = lazy(() => import("./pages/Profile"))
const Recommendation = lazy(() => import("./pages/Recommendation"))
const BudgetEstimator = lazy(() => import("./pages/BudgetEstimator"))
const RiskAlertDashboard = lazy(() => import("./pages/RiskAlertDashboard"))
const Hotels = lazy(() => import("./pages/Hotels"))
const HotelSearch = lazy(() => import("./pages/HotelSearch"))
const Navigation = lazy(() => import("./pages/Navigation"))
const DistancesExplorer = lazy(() => import("./pages/DistancesExplorer"))
const TravelPlanner = lazy(() => import("./pages/TravelPlanner"))
import Language from "./pages/Language.jsx"
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
const BeforeYouTravel = lazy(() => import("./pages/BeforeYouTravel"))
const FamilySafety = lazy(() => import("./pages/FamilySafety"))
const SharedTripView = lazy(() => import("./pages/SharedTripView"))
// Feature pages that existed but were never routed, so they could not be
// reached. Each one now has a real route and (where applicable) a nav entry.
const Feedback = lazy(() => import("./pages/Feedback"))
const HelpSupport = lazy(() => import("./pages/HelpSupport"))
const Marketplace = lazy(() => import("./pages/Marketplace"))
const Risk = lazy(() => import("./pages/Risk"))
const GuideDirectory = lazy(() => import("./pages/GuideDirectory"))
const JobBoard = lazy(() => import("./pages/JobBoard"))
const SafetyCenter = lazy(() => import("./pages/SafetyCenter"))
const Analytics = lazy(() => import("./pages/Analytics"))
const Payments = lazy(() => import("./pages/Payment"))

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
// Heavy, low-traffic surfaces are code-split (register DEF-013): admin
// console, maps, navigation and planners load as separate chunks.
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"))
import AdminLayout from "./components/admin/AdminLayout"
import StaffLayout from "./components/admin/StaffLayout"
const DiagnosticsCenter = lazy(() => import("./pages/admin/DiagnosticsCenter"))
const HotelAssignments = lazy(() => import("./pages/admin/HotelAssignments"))
const AdminTasks = lazy(() => import("./pages/admin/Tasks"))
const AdminPlaceApprovals = lazy(() => import("./pages/admin/PlaceApprovals"))
const AdminDestinationMedia = lazy(() => import("./pages/admin/DestinationMediaManager"))
const BookingManagement = lazy(() => import("./pages/BookingManagement"))

const RouteLoading = () => (
  <div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite">
    <div className="text-center"><span className="mx-auto block h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><p className="mt-3 text-sm text-[var(--ny-text-secondary)]">Loading this part of your journeyÔÇª</p></div>
  </div>
)

const LazyRoute = ({ children }) => <Suspense fallback={<RouteLoading />}>{children}</Suspense>


function App() {
  useEffect(() => {
    installGlobalErrorHandlers()
    // Remember the last request id so error reports can reference it.
    const onOk = (resp) => {
      const rid = resp.headers?.["x-request-id"]
      if (rid) window.__LAST_REQUEST_ID__ = rid
      return resp
    }
    const onErr = (err) => {
      const rid = err.response?.headers?.["x-request-id"]
      if (rid) window.__LAST_REQUEST_ID__ = rid
      return Promise.reject(err)
    }
    const interceptorId = axiosClient.interceptors.response.use(onOk, onErr)
    return () => axiosClient.interceptors.response.eject(interceptorId)
  }, [])
  return (
    <ErrorBoundary name="App">
      <ScrollToTop />
      <RedirectRules />
      <CommandPalette />
      <OfflineBanner />
      <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-emerald-300">LoadingÔÇª</div>}>
      <Routes>

      {/* Auth portals ÔÇö no traveller navbar/sidebar so Admin, Staff and Traveller look different */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<UserLogin />} />
        <Route path="/login/user" element={<UserLogin />} />
        <Route path="/staff/login" element={<StaffLogin />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/portal" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        {/* The emailed links point here ÔÇö these routes were missing, so
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
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
        <Route path="/terms-of-service" element={<TermsOfService />} />
        <Route path="/cookie-policy" element={<CookiePolicy />} />
        <Route path="/data-deletion" element={<DataDeletion />} />
        <Route path="/unsubscribe" element={<Unsubscribe />} />
        {/* Short legacy URLs keep working and point at one canonical page. */}
        <Route path="/privacy" element={<Navigate to="/privacy-policy" replace />} />
        <Route path="/terms" element={<Navigate to="/terms-of-service" replace />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/knowledge-base" element={<Navigate to="/how-it-works" replace />} />
        <Route path="/thank-you" element={<ThankYou />} />

        {/* Destinations */}
        <Route path="/destinations" element={<DestinationList />} />
        <Route path="/destinations/:slug" element={<DestinationDetails />} />
        <Route path="/districts" element={<LazyRoute><DistrictsIndex /></LazyRoute>} />
        <Route path="/districts/:districtName" element={<LazyRoute><DistrictDetail /></LazyRoute>} />
        <Route path="/compare" element={<CompareDestinations />} />
        <Route path="/destinations/compare" element={<CompareDestinations />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/travel-toolkit" element={<LazyRoute><TravelToolkit /></LazyRoute>} />
        <Route path="/itinerary" element={<LazyRoute><Itinerary /></LazyRoute>} />
        <Route path="/travel-guides/:slug" element={<LazyRoute><TravelGuide /></LazyRoute>} />
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
        <Route path="/search" element={<SearchPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/decide" element={<DecidePage />} />
        <Route path="/plans/shared/:token" element={<SharedPlanPage />} />
        <Route path="/explore-map" element={<LazyRoute><ExploreNepalMap /></LazyRoute>} />
        <Route path="/hotels/search" element={<HotelSearch />} />
        {/* Travel planner ÔÇö real routes between any two destinations (public) */}
        <Route path="/travel" element={<LazyRoute><TravelPlanner /></LazyRoute>} />
        {/* Previously unreachable: the pages existed but had no route. */}
        <Route path="/marketplace" element={<LazyRoute><Marketplace /></LazyRoute>} />
        <Route path="/risk" element={<LazyRoute><Risk /></LazyRoute>} />
        <Route path="/feedback" element={<LazyRoute><Feedback /></LazyRoute>} />
        <Route path="/help" element={<LazyRoute><HelpSupport /></LazyRoute>} />
        <Route path="/guide-directory" element={<LazyRoute><GuideDirectory /></LazyRoute>} />
        <Route path="/job-board" element={<LazyRoute><JobBoard /></LazyRoute>} />
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
          <Route path="/bookings" element={<BookingManagement />} />
          <Route path="/safety-center" element={<SafetyCenter />} />
          <Route path="/payments" element={<Payments />} />

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
            <Route path="/admin/place-approvals" element={<LazyRoute><AdminPlaceApprovals /></LazyRoute>} />
            <Route path="/admin/destination-media" element={<LazyRoute><AdminDestinationMedia /></LazyRoute>} />
            <Route path="/admin/analytics" element={<LazyRoute><Analytics /></LazyRoute>} />
          </Route>
        </Route>


      {/* 404 Page ÔÇö wrapped in MainLayout for consistent Navbar + Footer */}
      <Route element={<MainLayout />}>
        <Route path="*" element={<NotFound />} />
      </Route>

      </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}


export default App
