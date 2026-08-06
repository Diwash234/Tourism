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

// Features
import Chatbot from "./Chatbot"
import MyBooking from "./MyBookings"
import BookHotel from "./Bookhotel"

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

// Admin
import AdminDashboard from "./pages/admin/AdminDashboard"
import HotelAssignments from "./pages/admin/HotelAssignments"
import AdminTasks from "./pages/admin/Tasks"


function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>

      {/* Public Routes */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />

        {/* Auth */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        {/* Public — user isn't logged in yet during this step */}
        <Route path="/auth/callback/:provider" element={<OAuthCallback />} />

        {/* Destinations */}
        <Route path="/destinations" element={<DestinationList />} />
        <Route path="/destinations/:slug" element={<DestinationDetails />} />

        {/* Public Emergency */}
        <Route path="/emergency" element={<Emergency />} />
      </Route>


      {/* Protected User Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/verify-phone" element={<VerifyPhone />} />
          <Route path="/hotels" element={<Hotels />} />
          {/* Dedicated search endpoint (richer data: image_url, destination_name) */}
          <Route path="/hotels/search" element={<HotelSearch />} />
          <Route path="/destinations/submit" element={<SubmitPlacePage />} />
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


      {/* Admin Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AdminRoute />}>
          <Route element={<DashboardLayout />}>
            <Route 
              path="/admin" 
              element={<AdminDashboard />} 
            />
            {/* FIXED: both fully built, both had zero routes anywhere —
                same "built but never wired up" pattern as Bookhotel.jsx
                earlier this session. Gated behind the same AdminRoute as
                /admin since the backend has no way to expose a stricter
                superadmin-only flag to the frontend yet (checked
                UserProfileSerializer — is_superuser isn't a field on it
                at all). The backend still enforces the real
                superuser-only restriction on assign/delete actions. */}
            <Route path="/admin/hotel-assignments" element={<HotelAssignments />} />
            <Route path="/admin/tasks" element={<AdminTasks />} />
          </Route>
        </Route>
      </Route>


      {/* 404 Page — wrapped in MainLayout for consistent Navbar + Footer */}
      <Route element={<MainLayout />}>
        <Route path="*" element={<NotFound />} />
      </Route>

    </Routes>
    </>
  )
}


export default App