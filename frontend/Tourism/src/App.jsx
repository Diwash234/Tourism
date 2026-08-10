import { Routes, Route } from "react-router-dom"

// Layouts
import MainLayout from "./components/layout/MainLayout"
import DashboardLayout from "./components/layout/DashboardLayout"
import ScrollToTop from "./components/layout/ScrollToTop"

// Route Guards
import ProtectedRoute from "./routes/ProtectedRoute"
import AdminRoute from "./routes/AdminRoute"

// Public Pages
import Landing from "./pages/Landing"
import About from "./pages/About"
import Contact from "./pages/Contact"
import NotFound from "./pages/NotFound"

// Authentication
import Login from "./pages/auth/Login"
import Register from "./pages/auth/Register"
import ForgotPassword from "./pages/auth/ForgotPassword"
import OAuthCallback from "./pages/auth/OAuthCallback"
import VerifyPhone from "./pages/VerifyPhone"

// Destination Pages
import DestinationList from "./pages/destinations/DestinationList"
import DestinationDetails from "./pages/destinations/DestinationDetails"
import SubmitPlacePage from "./pages/SubmitPlacePage"
import DiscoverNepal from "./pages/DiscoverNepal"
import ExploreNepalMap from "./pages/ExploreNepalMap"
import ItineraryPlanner from "./pages/ItineraryPlanner"

// Features
import Chatbot from "./Chatbot"
import MyBooking from "./MyBookings"
import Bookhotel from "./Bookhotel"

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

// Admin Pages
import AdminDashboard from "./pages/admin/AdminDashboard"
import HotelAssignments from "./pages/admin/HotelAssignments"
import AdminTasks from "./pages/admin/Tasks"
import PlaceApprovals from "./pages/admin/PlaceApprovals"
import UserManagement from "./pages/admin/UserManagement"


function App() {
  return (
    <>
      {/* Scroll to top whenever the route changes */}
      <ScrollToTop />

      <Routes>

        {/* =====================================================
            PUBLIC ROUTES
        ===================================================== */}
        <Route element={<MainLayout />}>

          {/* Home / General */}
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />

          {/* Authentication */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* OAuth callback */}
          <Route
            path="/auth/callback/:provider"
            element={<OAuthCallback />}
          />

          {/* Destinations */}
          <Route
            path="/destinations"
            element={<DestinationList />}
          />

          <Route
            path="/destinations/:slug"
            element={<DestinationDetails />}
          />

          {/* Itinerary Planner */}
          <Route
            path="/itinerary"
            element={<ItineraryPlanner />}
          />

          {/* Public Emergency */}
          <Route
            path="/emergency"
            element={<Emergency />}
          />

        </Route>


        {/* =====================================================
            PROTECTED USER ROUTES
        ===================================================== */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>

            {/* Dashboard */}
            <Route
              path="/dashboard"
              element={<Dashboard />}
            />

            {/* Profile */}
            <Route
              path="/profile"
              element={<Profile />}
            />

            {/* Phone Verification */}
            <Route
              path="/verify-phone"
              element={<VerifyPhone />}
            />

            {/* Hotels */}
            <Route
              path="/hotels"
              element={<Hotels />}
            />

            {/* Hotel Search */}
            <Route
              path="/hotels/search"
              element={<HotelSearch />}
            />

            {/* Hotel Booking */}
            <Route
              path="/hotels/:hotelId/book"
              element={<Bookhotel />}
            />

            {/* My Bookings */}
            <Route
              path="/my-bookings"
              element={<MyBooking />}
            />


            {/* =================================================
                DESTINATIONS / EXPLORATION
            ================================================= */}

            <Route
              path="/destinations/submit"
              element={<SubmitPlacePage />}
            />

            <Route
              path="/discover-nepal"
              element={<DiscoverNepal />}
            />

            <Route
              path="/explore-map"
              element={<ExploreNepalMap />}
            />

            <Route
              path="/nearby-places"
              element={<NearbyPlaces />}
            />

            <Route
              path="/navigation"
              element={<Navigation />}
            />


            {/* =================================================
                TRAVEL FEATURES
            ================================================= */}

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

            <Route
              path="/language"
              element={<Language />}
            />

            <Route
              path="/translation"
              element={<Translation />}
            />

            <Route
              path="/chatbot"
              element={<Chatbot />}
            />


            {/* =================================================
                USER ACCOUNT
            ================================================= */}

            <Route
              path="/settings"
              element={<Settings />}
            />

            <Route
              path="/favorites"
              element={<Favorites />}
            />

            <Route
              path="/history"
              element={<History />}
            />

            <Route
              path="/notifications"
              element={<Notifications />}
            />

            <Route
              path="/expenditure"
              element={<Expenditure />}
            />

            <Route
              path="/my-submissions"
              element={<MySubmissions />}
            />

            {/* Staff Dashboard */}
            <Route
              path="/staff"
              element={<StaffDashboard />}
            />

          </Route>
        </Route>


        {/* =====================================================
            ADMIN ROUTES
        ===================================================== */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AdminRoute />}>
            <Route element={<DashboardLayout />}>

              {/* Main Admin Dashboard */}
              <Route
                path="/admin"
                element={<AdminDashboard />}
              />

              {/* Hotel Assignments */}
              <Route
                path="/admin/hotel-assignments"
                element={<HotelAssignments />}
              />

              {/* Admin Tasks */}
              <Route
                path="/admin/tasks"
                element={<AdminTasks />}
              />

              {/* Place Approvals */}
              <Route
                path="/admin/place-approvals"
                element={<PlaceApprovals />}
              />

              {/* User Management */}
              <Route
                path="/admin/users"
                element={<UserManagement />}
              />

            </Route>
          </Route>
        </Route>


        {/* =====================================================
            404 NOT FOUND
            Wrapped in MainLayout so Navbar, Sidebar, Footer
            and FloatingChatbot remain available.
        ===================================================== */}
        <Route element={<MainLayout />}>
          <Route
            path="*"
            element={<NotFound />}
          />
        </Route>

      </Routes>
    </>
  )
}

export default App