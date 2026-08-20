import { useEffect } from "react"
import { Routes, Route } from "react-router-dom"
import ErrorBoundary from "./components/common/ErrorBoundary"
import { installGlobalErrorHandlers } from "./utils/errorLogger"

// Layouts
import MainLayout from "./components/layout/MainLayout"
import DashboardLayout from "./components/layout/DashboardLayout"
import AuthLayout from "./components/auth/AuthLayout"
import ScrollToTop from "./components/layout/ScrollToTop"

// Route Guards
import ProtectedRoute from "./routes/ProtectedRoute"
import AdminRoute from "./routes/AdminRoute"
import StaffRoute from "./routes/StaffRoute"

// Public Pages
import Landing from "./pages/Landing"
import About from "./pages/About"
import Contact from "./pages/Contact"
import ThankYou from "./pages/ThankYou"
import NotFound from "./pages/NotFound"

// Authentication
import Login from "./pages/auth/Login"
import UserLogin from "./pages/auth/UserLogin"
import StaffLogin from "./pages/auth/StaffLogin"
import AdminLogin from "./pages/auth/AdminLogin"
import Register from "./pages/auth/Register"
import ForgotPassword from "./pages/auth/ForgotPassword"
import OAuthCallback from "./pages/auth/OAuthCallback"
import VerifyPhone from "./pages/VerifyPhone"

// Destination Pages
import DestinationList from "./pages/destinations/DestinationList"
import DestinationDetails from "./pages/destinations/DestinationDetails"
import SubmitPlacePage from "./pages/SubmitPlacePage"
import SubmitServicePage from "./pages/SubmitServicePage"
import DiscoverNepal from "./pages/DiscoverNepal"
import ExploreNepalMap from "./pages/ExploreNepalMap"
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
import Navigation from "./pages/Navigation"
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
import Itinerary from "./pages/Itinerary"
import FamilySafety from "./pages/FamilySafety"
import SharedTripView from "./pages/SharedTripView"

// New Features (Remote Repository Updates)
import Packages from "./pages/Packages"
import TripPlanner from "./pages/TripPlanner"
import PersonalDetails from "./pages/PersonalDetails"
import LocalDashboard from "./pages/local/LocalDashboard"
import LocalRoute from "./routes/LocalRoute"

// Admin
import AdminDashboard from "./pages/admin/AdminDashboard"
import AdminLayout from "./components/admin/AdminLayout"
import StaffLayout from "./components/admin/StaffLayout"
import DiagnosticsCenter from "./pages/admin/DiagnosticsCenter"
import HotelAssignments from "./pages/admin/HotelAssignments"
import AdminTasks from "./pages/admin/Tasks"


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
      } catch {}
    }
    importInterceptor()
  }, [])
  return (
    <ErrorBoundary name="App">
      <ScrollToTop />
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
        <Route path="/thank-you" element={<ThankYou />} />

        {/* Destinations */}
        <Route path="/destinations" element={<DestinationList />} />
        <Route path="/destinations/:slug" element={<DestinationDetails />} />
        <Route path="/compare" element={<CompareDestinations />} />
        <Route path="/destinations/compare" element={<CompareDestinations />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/itinerary" element={<Itinerary />} />
        <Route path="/packages" element={<Packages />} />
        <Route path="/trip-planner" element={<TripPlanner />} />

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

          <Route path="/chatbot" element={<Chatbot />} />

          <Route
            path="/hotels/:hotelId/book"
            element={<BookHotel />}
          />

          <Route
            path="/my-bookings"
            element={<MyBooking />}
          />

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
        <Route path="*" element={<NotFound />} />
      </Route>

      </Routes>
    </ErrorBoundary>
  )
}


export default App