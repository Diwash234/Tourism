import { Routes, Route } from "react-router-dom"

import MainLayout from "./components/layout/MainLayout"
import DashboardLayout from "./components/layout/DashboardLayout"
import ProtectedRoute from "./routes/ProtectedRoute"
import AdminRoute from "./routes/AdminRoute"
import LocalRoute from "./routes/LocalRoute"

import Landing from "./pages/Landing"
import About from "./pages/About"
import Contact from "./pages/Contact"
import NotFound from "./pages/NotFound"

import Login from "./pages/auth/Login"
import Register from "./pages/auth/Register"
import ForgotPassword from "./pages/auth/ForgotPassword"

import DestinationList from "./pages/destinations/DestinationList"
import DestinationDetails from "./pages/destinations/DestinationDetails"

import Dashboard from "./pages/Dashboard"
import Profile from "./pages/Profile"
import Recommendation from "./pages/Recommendation"
import BudgetEstimator from "./pages/BudgetEstimator"
import RiskAlertDashboard from "./pages/RiskAlertDashboard"
import Navigation from "./pages/Navigation"
import Emergency from "./pages/Emergency"
import NearbyPlaces from "./pages/NearbyPlaces"
import Translation from "./pages/Translation"
import Settings from "./pages/Settings"
import Favorites from "./pages/Favorites"
import History from "./pages/History"
import Notifications from "./pages/Notifications"
import PersonalDetails from "./pages/PersonalDetails"
import Packages from "./pages/Packages"
import TripPlanner from "./pages/TripPlanner"

import AdminDashboard from "./pages/admin/AdminDashboard"
import AdminAgencies from "./pages/admin/AdminAgencies"
import LocalDashboard from "./pages/local/LocalDashboard"

function App() {
  return (
    <Routes>
      {/* Public site (Navbar + Footer) */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/destinations" element={<DestinationList />} />
        <Route path="/destinations/:id" element={<DestinationDetails />} />
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/packages" element={<Packages />} />
      </Route>

      {/* Authenticated area (Navbar + Sidebar) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/personal-details" element={<PersonalDetails />} />
          <Route path="/trip-planner" element={<TripPlanner />} />
          <Route path="/recommendation" element={<Recommendation />} />
          <Route path="/budget-estimator" element={<BudgetEstimator />} />
          <Route path="/risk-alerts" element={<RiskAlertDashboard />} />
          <Route path="/navigation" element={<Navigation />} />
          <Route path="/nearby-places" element={<NearbyPlaces />} />
          <Route path="/translation" element={<Translation />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/history" element={<History />} />
          <Route path="/notifications" element={<Notifications />} />
        </Route>
      </Route>

      {/* Local guide only */}
      <Route element={<LocalRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/local/dashboard" element={<LocalDashboard />} />
        </Route>
      </Route>

      {/* Admin only */}
      <Route element={<AdminRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/agencies" element={<AdminAgencies />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App