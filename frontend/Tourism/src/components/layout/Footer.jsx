import { Link } from "react-router-dom"
import { FiFacebook, FiInstagram, FiTwitter, FiMapPin, FiMail, FiPhone } from "react-icons/fi"
import { APP_NAME } from "../../utils/constants"

const Footer = () => {
  return (
    <footer className="bg-dusk-gradient text-white/80 mt-0">
      <div className="lungta-strip" />
      <div className="container-app py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h3 className="text-white text-xl font-display font-semibold mb-3">{APP_NAME}</h3>
          <p className="text-sm text-white/60">
            Discover local destinations, plan smart budgets, and travel safely with
            real-time alerts and navigation.
          </p>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Explore</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/destinations" className="hover:text-marigold-300 transition">Destinations</Link></li>
            <li><Link to="/recommendation" className="hover:text-marigold-300 transition">Recommendations</Link></li>
            <li><Link to="/budget-estimator" className="hover:text-marigold-300 transition">Budget Estimator</Link></li>
            <li><Link to="/risk-alerts" className="hover:text-marigold-300 transition">Risk Alerts</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Company</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/about" className="hover:text-marigold-300 transition">About Us</Link></li>
            <li><Link to="/contact" className="hover:text-marigold-300 transition">Contact</Link></li>
            <li><Link to="/emergency" className="hover:text-marigold-300 transition">Emergency</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Contact</h4>
          <ul className="space-y-2 text-sm text-white/70">
            <li className="flex items-center gap-2"><FiMapPin className="text-secondary-300" /> Pokhara, Nepal</li>
            <li className="flex items-center gap-2"><FiMail className="text-secondary-300" /> support@tourists.app</li>
            <li className="flex items-center gap-2"><FiPhone className="text-secondary-300" /> +977-000-0000</li>
          </ul>
          <div className="flex gap-4 mt-4 text-lg">
            <FiFacebook className="hover:text-marigold-300 cursor-pointer transition" />
            <FiInstagram className="hover:text-marigold-300 cursor-pointer transition" />
            <FiTwitter className="hover:text-marigold-300 cursor-pointer transition" />
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 py-4 text-center text-xs text-white/50">
        © {new Date().getFullYear()} {APP_NAME}. All rights reserved.
      </div>
    </footer>
  )
}

export default Footer