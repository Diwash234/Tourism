import { Routes, Route } from "react-router-dom"

// Layouts
import MainLayout from "./components/layout/MainLayout"
import DashboardLayout from "./components/layout/DashboardLayout"

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

// Destination Pages
import Destinationlist from "./pages/destinations/Destinationlist"
import DestinationDetails from "./pages/destinations/DestinationDetails"

// Features
import Chatbot from "./Chatbot"
import MyBooking from "./MyBookings"

// User Dashboard Pages
import Dashboard from "./pages/Dashboard"
import Profile from "./pages/Profile"
import Recommendation from "./pages/Recommendation"
import BudgetEstimator from "./pages/BudgetEstimator"
import RiskAlertDashboard from "./pages/RiskAlertDashboard"
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


function App() {
  return (
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

        {/* Destinations */}
        <Route path="/destinations" element={<Destinationlist />} />
        <Route path="/destinations/:slug" element={<DestinationDetails />} />

        {/* Public Emergency */}
        <Route path="/emergency" element={<Emergency />} />
      </Route>


      {/* Protected User Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />

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
          </Route>
        </Route>
      </Route>


      {/* 404 Page */}
      <Route path="*" element={<NotFound />} />

    </Routes>
  )
}


export default App
